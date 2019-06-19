"""
@description: 命名实体识别模块
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""
from collections import defaultdict

import jieba
import logging

from sementic_server.source.ner_task.entity_code import EntityCode
from sementic_server.source.ner_task.system_info import SystemInfo
from sementic_server.source.ner_task.model_tf_serving import ModelServing

logger = logging.getLogger("server_log")


class SemanticSearch(object):
    """
    通过调用 sentence_ner_entities 函数实现对：人名、组织结构名、地名和日期 的识别
    """

    def __init__(self, test_mode=False):

        self.system_info = SystemInfo(is_test=test_mode)

        self.client = ModelServing(self.system_info.MODE_NER, is_test=test_mode)

        self.config = self.system_info.get_config()

        self.entity_code = EntityCode()
        self.ner_entities = self.entity_code.get_ner_entities()
        self.code = self.entity_code.get_entity_code()

        self.labels_list = []
        self.labels_list_split = []
        self.__init_specific_label_combine()
        self.__init_jieba()

    def __init_specific_label_combine(self):
        """
        初始化labels_list和labels_list_split列表
        用于将出现的此类标签：“NAMECOMPANY” 分开成 “NAME#COMPANY”
        :return:
        """
        entities = self.entity_code.get_entities()
        for i in range(0, len(entities)):
            for j in range(0, len(entities)):
                if i != j:
                    self.labels_list.append(entities[i] + entities[j])
                    self.labels_list_split.append((entities[i] + "#" + entities[j]))

                    self.labels_list.append(entities[j] + entities[i])
                    self.labels_list_split.append((entities[j] + "#" + entities[i]))

    def __init_jieba(self):
        """
        可以给分词工具加入领域词汇辅助分词，加入公司名称可以有效提升分词工具对公司名称分词的准确度
        :return:
        """
        entities = self.entity_code.get_entities()
        for label in entities:
            jieba.add_word(label)

    def __combine_label(self, entities, label=None):
        """
        合并实体列表中相连且相同的label
        :param entities:
        :param label:
        :return:
        """
        pre_label = False
        first_label = None
        entities_copy = []
        for i in range(len(entities)):
            if entities[i][1] != label:
                pre_label = False
                if first_label is not None:
                    entities_copy.append(first_label)
                    first_label = None
                entities_copy.append(entities[i])
            elif pre_label is False and entities[i][1] == label:
                pre_label = True
                first_label = entities[i]
            elif pre_label and first_label is not None and entities[i][1] == label:
                temp = first_label
                first_label = [temp[0] + entities[i][0], temp[1]]

        if first_label is not None:
            entities_copy.append(first_label)

        return entities_copy

    def __combine_com_add(self, entities):
        """
        合并 COMPANYADDR 和 ADDRCOMPANY 这类实体为 COMPANY
        :param entities:
        :return:
        """
        company_index = -1
        addr_index = -1

        for i, entity in enumerate(entities):
            if self.ner_entities['COMPANY'] == entity[1]:
                company_index = i
            if self.ner_entities['ADDR'] == entity[1]:
                addr_index = i

        if company_index != -1 and addr_index != -1:
            if company_index == addr_index + 1:
                entities[company_index][0] = entities[addr_index][0] + entities[company_index][0]
                entities.remove(entities[addr_index])
            elif company_index == addr_index - 1:
                entities[company_index][0] = entities[company_index][0] + entities[addr_index][0]
                entities.remove(entities[addr_index])

    def __split_diff_labels(self, template_sen):
        """
        检测模板句中是否有不同的label相互连接的情况，eg. "ADDRNAME"，这种情况分词工具无法正确分词
        如果存在相连的label，使用“#”将两个label分开
        :param template_sen: 模板句子
        :return:
        """
        for i, label in enumerate(self.labels_list):
            if label in template_sen:
                template_sen = template_sen.replace(label, self.labels_list_split[i])
        return template_sen

    def __convert_output_data_format(self, data_param):
        """
        将 data_param 数据转换成问答图模块需要的数据格式
        :param data_param:
        :return:
        """
        output = defaultdict()
        output["query"] = data_param["raw_input"]
        output["template"] = data_param["new_input"]
        entity = []
        for key, values in data_param["labels"].items():
            for v in values:
                begin = data_param["raw_input"].find(v)
                entity.append(
                    {"type": key, "value": v, "code": self.code[key], "begin": begin,
                     "end": begin + len(v) + 1 if begin != -1 else -1})
        output["entity"] = entity
        return output

    def sentence_ner_entities(self, result):
        """
        使用 BERT 模型对句子进行实体识别，返回标记实体的句子
        :param result: account_label 模块返回的结果
        :return:
            entities: 列表，存储的是 BERT 识别出来的实体信息:(word, label)
            result: account_label 模块返回的结果
        """
        sentence = result["new_input"]

        sentence, pred_label_result = self.client.send_grpc_request_ner(sentence)

        word = ""
        label = ""
        entities = []

        if sentence is None or pred_label_result is None:
            return entities, result

        for i in range(len(sentence)):
            temp_label = pred_label_result[i]
            if temp_label[0] == 'B':
                if word != "":
                    if "##" in word:
                        word = word.replace('##', '')
                    entities.append([word, label])
                    word = ""

                if temp_label[2:] == 'ORG':
                    label = self.ner_entities['COMPANY']
                elif temp_label[2:] == 'PER':
                    label = self.ner_entities['NAME']
                elif temp_label[2:] == 'DATE':
                    label = self.ner_entities['DATE']
                else:
                    label = self.ner_entities['ADDR']

                word += sentence[i]
            elif temp_label[0] == 'I' and word != "":
                word += sentence[i]
            elif temp_label == 'O' and word != "":
                if "##" in word:
                    word = word.replace('##', '')
                entities.append([word, label])
                word = ""
                label = ""
        if word != "":
            if "##" in word:
                word = word.replace('##', '')
            entities.append([word, label])

        if len(entities) != 0:
            entities = self.__combine_label(entities, label=self.ner_entities['ADDR'])
            entities = self.__combine_label(entities, label=self.ner_entities['COMPANY'])
            entities = self.__combine_label(entities, label=self.ner_entities['NAME'])
            entities = self.__combine_label(entities, label=self.ner_entities['DATE'])

            self.__combine_com_add(entities)
            entities = self.__combine_label(entities, label=self.ner_entities['COMPANY'])

        for (word, label) in entities:
            result["new_input"] = result["new_input"].replace(word, label)
            result["labels"].setdefault(label, []).append(word)

        result = self.__convert_output_data_format(result)
        return result
