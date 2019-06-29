"""
@description: 通过SavedModel类将模型保存起来，使用TensorFlow Serving的形式提供预测服务
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-06-29
@version: 0.0.1
"""
import os
import grpc
import logging
import pickle
import numpy as np
import tensorflow as tf

from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc

from sementic_server.source.ner_task.bert import tokenization
from sementic_server.source.ner_task.data_process import InputFeatures
from sementic_server.source.ner_task.system_info import SystemInfo
from sementic_server.source.ner_task.utils import convert_id_to_label
from sementic_server.source.ner_task.utils import load_config

logger = logging.getLogger("server_log")

MODEL_NAME_NER = 'ner_model'
MODEL_NAME_SEN = 'sen_model'

MODEL_SIGNATURE_NER = 'prediction_labels'
MODEL_SIGNATURE_SEN = 'compute_sen_vector'


class ModelServing(object):
    """
    通过 grpc 的方式请求部署在Docker上的TensorFlow Serving服务。
    提供了两种服务：NER 和 SEN 服务
    NER：识别句子中的实体
    SEN：将句子表示成向量形式
    """

    def __init__(self, mode, is_test=False):
        self.system_info = SystemInfo()
        if is_test:
            # 测试模式下加载配置文件
            self.config = load_config('../../config/')
            self.time_out = self.config["grpc_request_timeout"]
            self.batch_size = self.config["pred_batch_size"]
            self.hidden_size = self.config["hidden_size"]

            with open('../../data/labels/label_list.pkl', 'rb') as rf:
                self.label_list = pickle.load(rf)
            with open('../../data/labels/label2id.pkl', 'rb') as rf:
                self.label2id = pickle.load(rf)
                self.id2label = {value: key for key, value in self.label2id.items()}

            self.label_map = {}
            for i, label in enumerate(self.label_list, 1):
                self.label_map[label] = i
            self.tokenizer = tokenization.FullTokenizer(vocab_file='../../chinese_L-12_H-768_A-12/vocab.txt',
                                                        do_lower_case=self.config["do_lower_case"])
            channel = grpc.insecure_channel(self.config["model_ner_address"])
            self.stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
        else:
            self.config = self.system_info.get_config()
            self.time_out = self.config["grpc_request_timeout"]
            self.batch_size = self.config["pred_batch_size"]
            self.hidden_size = self.config["hidden_size"]
            self.max_seq_length = self.config["max_seq_length"]

            label_path = self.system_info.get_labels_path()

            with open(os.path.join(label_path, 'label_list.pkl'), 'rb') as rf:
                self.label_list = pickle.load(rf)

            with open(os.path.join(label_path, 'label2id.pkl'), 'rb') as rf:
                self.label2id = pickle.load(rf)
                self.id2label = {value: key for key, value in self.label2id.items()}

            self.label_map = {}
            # 1表示从1开始对label进行index化
            for i, label in enumerate(self.label_list, 1):
                self.label_map[label] = i

            self.tokenizer = tokenization.FullTokenizer(vocab_file=os.getcwd() + self.config["vocab_file"],
                                                        do_lower_case=self.config["do_lower_case"])

            if mode == self.system_info.MODE_NER:
                channel = grpc.insecure_channel(self.config["model_ner_address"])
                self.stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
            else:
                logger.error('Please config ip address and port first.')

    def convert_single_example(self, ex_index, example, max_seq_length, tokenizer, mode):
        """
        将一个样本进行分析，然后将字转化为id, 标签转化为id,然后结构化到InputFeatures对象中
        :param ex_index: index
        :param example: 一个样本
        :param max_seq_length:
        :param tokenizer:
        :param mode:
        :return:
        """

        tokens = example
        # 序列截断
        if len(tokens) >= max_seq_length - 1:
            tokens = tokens[0:(max_seq_length - 2)]  # -2 的原因是因为序列需要加一个句首和句尾标志
        ntokens = []
        segment_ids = []
        label_ids = []
        ntokens.append("[CLS]")  # 句子开始设置CLS 标志
        segment_ids.append(0)
        label_ids.append(self.label_map["[CLS]"])  # O OR CLS 没有任何影响，不过我觉得O 会减少标签个数,不过拒收和句尾使用不同的标志来标注，使用LCS 也没毛病
        for i, token in enumerate(tokens):
            ntokens.append(token)
            segment_ids.append(0)
            label_ids.append(0)
        ntokens.append("[SEP]")  # 句尾添加[SEP] 标志
        segment_ids.append(0)
        label_ids.append(self.label_map["[SEP]"])
        input_ids = tokenizer.convert_tokens_to_ids(ntokens)  # 将序列中的字(ntokens)转化为ID形式
        input_mask = [1] * len(input_ids)

        # padding, 使用
        while len(input_ids) < max_seq_length:
            input_ids.append(0)
            input_mask.append(0)
            segment_ids.append(0)
            label_ids.append(0)
            ntokens.append("**NULL**")
        assert len(input_ids) == max_seq_length
        assert len(input_mask) == max_seq_length
        assert len(segment_ids) == max_seq_length
        assert len(label_ids) == max_seq_length

        # 结构化为一个类
        feature = InputFeatures(
            input_ids=input_ids,
            input_mask=input_mask,
            segment_ids=segment_ids,
            label_ids=label_ids,
        )
        return feature

    def convert(self, line, seq_length=128):
        feature = self.convert_single_example(0, line, seq_length, self.tokenizer, 'p')

        input_ids = np.reshape([feature.input_ids], (self.batch_size, seq_length)).tolist()
        input_mask = np.reshape([feature.input_mask], (self.batch_size, seq_length)).tolist()
        segment_ids = np.reshape([feature.segment_ids], (self.batch_size, seq_length)).tolist()
        label_ids = np.reshape([feature.label_ids], (self.batch_size, seq_length)).tolist()
        return input_ids, input_mask, segment_ids, label_ids

    def send_grpc_request_ner(self, raw_sen):
        """
        发送grpc请求到服务器，获取对句子实体识别的结果
        :param raw_sen: 待识别的句子
        :return:
        """
        sentence = self.tokenizer.tokenize(raw_sen)

        input_ids, input_mask, segment_ids, label_ids = self.convert(sentence, self.config["max_seq_length"])

        # create the request object and set the name and signature_name params
        request = predict_pb2.PredictRequest()
        request.model_spec.name = MODEL_NAME_NER
        request.model_spec.signature_name = MODEL_SIGNATURE_NER

        # fill in the request object with the necessary data
        request.inputs['input_ids'].CopyFrom(
            tf.contrib.util.make_tensor_proto(input_ids)
        )
        request.inputs['input_mask'].CopyFrom(
            tf.contrib.util.make_tensor_proto(input_mask)
        )
        request.inputs['segment_ids'].CopyFrom(
            tf.contrib.util.make_tensor_proto(segment_ids)
        )
        request.inputs['label_ids'].CopyFrom(
            tf.contrib.util.make_tensor_proto(label_ids)
        )

        result_future = self.stub.Predict.future(request, self.time_out)
        exception = result_future.exception()

        if exception:
            logger.error('process sentence: {0}, raise exception: {1}'.format(raw_sen, exception))
            return None, None
        else:
            pred_ids_result = np.array(result_future.result().outputs['pred_ids'].int_val)
            pred_label_result = convert_id_to_label(pred_ids_result, self.id2label)

            return sentence, pred_label_result

    def test_send_grpc_request_ner(self, raw_sen):
        """
        测试 ner 服务是否可以正常使用
        :param raw_sen:
        :return:
        """
        sentence = self.tokenizer.tokenize(raw_sen)

        input_ids, input_mask, segment_ids, label_ids = self.convert(sentence, self.config["max_seq_length"])

        # create the request object and set the name and signature_name params
        request = predict_pb2.PredictRequest()
        request.model_spec.name = MODEL_NAME_NER
        request.model_spec.signature_name = MODEL_SIGNATURE_NER

        # fill in the request object with the necessary data
        request.inputs['input_ids'].CopyFrom(
            tf.contrib.util.make_tensor_proto(input_ids)
        )
        request.inputs['input_mask'].CopyFrom(
            tf.contrib.util.make_tensor_proto(input_mask)
        )
        request.inputs['segment_ids'].CopyFrom(
            tf.contrib.util.make_tensor_proto(segment_ids)
        )
        request.inputs['label_ids'].CopyFrom(
            tf.contrib.util.make_tensor_proto(label_ids)
        )

        result_future = self.stub.Predict.future(request, self.time_out)
        exception = result_future.exception()

        if exception:
            print('process sentence: {0}, raise exception: {1}'.format(raw_sen, exception))
            return False
        else:
            pred_ids_result = np.array(result_future.result().outputs['pred_ids'].int_val)
            pred_label_result = convert_id_to_label(pred_ids_result, self.id2label)

            print(sentence)
            print(pred_label_result)
            return True