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

    @staticmethod
    def __combine_label(entities, label=None):
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

    def __get_entities(self, sentence, pred_label_result):
        """
        根据BIO标签从识别结果中找出所有的实体
        :param sentence: 待识别的句子
        :param pred_label_result: 对该句子预测的标签
        :return: 返回识别的实体
        """
        word = ""
        label = ""
        entities = []
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

        return entities

    def sentence_ner_entities(self, result_intent):
        """
        使用 BERT 模型对句子进行实体识别，返回标记实体的句子
        :param result_intent: 意图识别模块的输出
        :return:
            entities: 列表，存储的是 BERT 识别出来的实体信息:(word, label)
            result: account_label 模块返回的结果
        """
        sentence = result_intent["query"]

        sentence, pred_label_result = self.client.send_grpc_request_ner(sentence)

        if pred_label_result is None:
            logger.error("句子: {0}\t实体识别结果为空".format(result_intent["query"]))
            return None

        entities = self.__get_entities(sentence, pred_label_result)

        if len(entities) != 0:
            entities = self.__combine_label(entities, label=self.ner_entities['ADDR'])
            entities = self.__combine_label(entities, label=self.ner_entities['COMPANY'])
            entities = self.__combine_label(entities, label=self.ner_entities['DATE'])

            self.__combine_com_add(entities)
            entities = self.__combine_label(entities, label=self.ner_entities['COMPANY'])

        entity = []
        for word, label in entities:
            begin = result_intent["query"].find(word)
            entity.append(
                {"type": label, "value": word, "code": self.code[label], "begin": begin,
                 "end": begin + len(word) + 1 if begin != -1 else -1})
        result_intent["entity"] = entity
        for index, rel in enumerate(result_intent["relation"]):
            for word, _ in entities:
                if word.find(rel["value"]) != -1:
                    temp = result_intent["relation"].pop(index)
                    print(temp)

        return result_intent
