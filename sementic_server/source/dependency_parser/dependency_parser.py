"""
提供句法依存分析功能

@Author: Xu Ze
@Time: 2019-06-05
@Version: 0.1.0
"""

from os.path import join, abspath
from os import getcwd
import os
import yaml
import copy
import pprint
import logging
import json
from sementic_server.source.dependency_parser.server_request import ServerRequest
from sementic_server.source.ner_task.entity_code import EntityCode

logger = logging.getLogger("server_log")


class DependencyParser(object):
    """本类用于依存分析，获得依存分析结果"""

    def __init__(self):
        self.dir_yml = join(abspath(getcwd()), "..", "..", "data", "yml")

        rootpath = str(os.getcwd()).replace("\\", "/")
        if 'source' in rootpath.split('/'):
            replace_words_dir = open(os.path.join(os.getcwd(), '../../', 'data', 'yml', 'replaceword.yml'),
                                     encoding='utf-8')
        else:
            replace_words_dir = open(os.path.join(os.getcwd(), 'sementic_server', 'data', 'yml', 'replaceword.yml'),
                                     encoding='utf-8')
        entity_code = EntityCode()

        self.account = entity_code.get_account()
        self.ner_entities_dics = entity_code.get_ner_entities()
        self.rever_ner_entities_dics = {v: k for k, v in self.ner_entities_dics.items()}
        self.replace_words = yaml.load(replace_words_dir, Loader=yaml.SafeLoader)

    def get_denpendency_tree(self, sentence, entities, relations):
        """
        :param:sentence,输入的句子
        return:
            dependency_tree_recovered:根据输入的句子建立的依存分析树，每个数据项代表一条边，例子如下：
            {'dep': 'ROOT', 'governor': 0, 'governorGloss': 'ROOT', 'dependent': 8, 'dependentGloss': '老婆'}
            'dep'表示依存关系，
            'governor'表示一条边的头部节点的序号
            'governorGloss'表示一条边的头部节点的值
            'dependent'表示一条边的尾部节点的序号
            'dependentGloss'表示一条边的尾部节点的值

            tokens_recovered:树中的所有节点列表，数据项例子如下：
            {'index': 1, 'word': '在', 'originalText': '在', 'characterOffsetBegin': 0,
            'characterOffsetEnd': 1, 'pos': 'P'}
            'index'表示数据项编号
            'word'表示节点的存放的字符（一个字到一个短语）
            'characterOffsetBegin'字符在句子中的起始位置
            'characterOffsetEnd'字符在句子中的末尾位置
            'pos'表示字符的词性
        """
        # 替换实体，更新关系
        sentence_replaced, entities_replaced, relations_updated = self.replace_entities_relations_2(sentence, entities,
                                                                                                    relations)

        pprint.pprint(entities_replaced)
        pprint.pprint(relations_updated)

        # 调用nlp工具获得依存关系
        dependency_tree, tokens = ServerRequest().get_dependency(sentence_replaced)
        # 还原依存关系树中的实体和关系
        dependency_tree_recovered, tokens_recovered = self.recover_tokens(dependency_tree, tokens, entities_replaced)

        pprint.pprint(dependency_tree_recovered)
        pprint.pprint(tokens_recovered)

        # 找到所有关系并返回
        dependency_graph = self.find_dependency_graph(dependency_tree_recovered, tokens, entities, relations)

        return dependency_tree_recovered, tokens_recovered, dependency_graph, entities, relations

    def replace_entities_relations_2(self, sentence, entities, relations):
        new_sen = copy.deepcopy(sentence)
        c_entities = copy.deepcopy(entities)
        c_relations = copy.deepcopy(relations)
        max_k = len(self.replace_words['NAME'])
        for idx, entity in enumerate(c_entities):
            if idx >= max_k:
                raise ValueError('没有足够的实体替换')

            old_value = entity["value"]
            if entity['type'] in self.account:
                new_value = self.replace_words['NAME'][idx]
            else:
                new_value = self.replace_words[self.rever_ner_entities_dics[entity['type']]][idx]
            new_sen = new_sen.replace(old_value, new_value)
            entity['value'] = new_value
            entity['origin_word'] = old_value
            entity['origin_start'] = entity['begin']
            entity['origin_end'] = entity['end']

        for entity in c_entities:
            s = new_sen.find(entity['value'])
            entity['begin'] = s
            entity['end'] = s + len(entity['value'])

        for rel in c_relations:
            s = new_sen.find(rel['value'])
            rel['begin'] = s
            rel['end'] = s + len(rel['value'])

        return new_sen, c_entities, c_relations

    def recover_tokens(self, dependency_tree, tokens, entities_replaced):
        """
        将依存分析的结果里面的实体进行复原
        :param dependency_tree:依存树的边
        :param tokens:依存树的节点
        :param entities_replaced:用词典替换后的实体
        :param relations_updated:更新位置后的关系
        :return:
            entities:NER之后的实体列表
            relations:关系列表
        """
        # 先将树中的tokens和entity_replaced的中的entity进行关联，增加index字段
        self.add_index(tokens, entities_replaced)

        # 将依存分析返回的tokens的每个值都进行更新
        for token in tokens:
            # 假如碰到之前替换过的字段，替换回去
            for entity_replaced in entities_replaced:
                # 使用index字段进行匹配
                if entity_replaced['index'] == token['index']:
                    # 获得替换过的字段和原始字段的长度差
                    move_len = len(token['word']) - len(entity_replaced['origin_word'])

                    token['word'] = entity_replaced['origin_word']
                    token['originalText'] = entity_replaced['origin_word']
                    token['characterOffsetBegin'] = entity_replaced['origin_start']
                    token['characterOffsetEnd'] = entity_replaced['origin_end']
                    # 每当匹配成功一个，将其他的字段的start和end都进行更新
                    for token_back in tokens:
                        # entities_replaced中的变量也要更新
                        if token_back['characterOffsetBegin'] > entity_replaced['begin']:
                            token_back['characterOffsetBegin'] = token_back['characterOffsetBegin'] - move_len
                            token_back['characterOffsetEnd'] = token_back['characterOffsetEnd'] - move_len
        # 更新边
        self.update_edge(dependency_tree, tokens)

        return dependency_tree, tokens

    @staticmethod
    def add_index(tokens, entities_replaced):
        for token in tokens:
            for entity_replaced in entities_replaced:
                if entity_replaced['begin'] == token['characterOffsetBegin']:
                    entity_replaced['index'] = token['index']

    @staticmethod
    def update_edge(dependency_tree, tokens):
        for node in dependency_tree:
            if node['governorGloss'] != 'ROOT':
                node['governorGloss'] = tokens[node['governor'] - 1]['word']
            node['dependentGloss'] = tokens[node['dependent'] - 1]['word']

    # 用于替换句子中的一个词
    @staticmethod
    def replace_string(raw_str, sub_str,
                       replace_str, start):
        """
            raw_str: 原始句子
            sub_str: 原始句子中需要替换的词（用于计算需要替换的长度）
            replace_str: 想替换后的词
            offset: 需要替换词的位置
        """
        front_str = raw_str[:start]
        mid_str = replace_str
        rear_str = raw_str[start + len(sub_str):]
        return front_str + mid_str + rear_str

    # 根据依存关系确定实体和边的依存关系
    def find_dependency_graph(self, dependency_tree_recovered,
                              tokens, entities_replaced, relations_updated):
        """
            dependency_tree_recovered: 依存树的边的集合
            entities_replaced: 实体集合
            relations_updated: 关系集合
        """
        # 将实体和关系整合起来
        entities_reltions = []
        entities = []
        relations = []
        self.collect_entity_rel(entities_reltions, entities, relations, entities_replaced, relations_updated)

        # 遍历依存树的边，将树中所有实体和关系节点，和树中最接近根的那个实体或者关系对应
        entity_dependency_list = []
        for edge in dependency_tree_recovered:
            # 当边的尾部的值属于 实体或者关系
            if edge['dependentGloss'] in entities_reltions:
                # 循环往上找，直到找到另一个实体或者边。若是找到根节点就说明没有前置实体或者关系
                governor = copy.deepcopy(edge)
                # governor是非根节点，才开始查
                if governor['governorGloss'] != 'ROOT':
                    self.search_to_root(entities_reltions, dependency_tree_recovered, governor)
                    self.connect_edge_entity(governor, edge, tokens, entity_dependency_list, entities, relations)

        return entity_dependency_list

    @staticmethod
    def collect_entity_rel(entities_reltions, entities, relations, entities_replaced, relations_updated):
        for entity in entities_replaced:
            entities_reltions.append(entity['value'])
            entities.append(entity['value'])
        for relation in relations_updated:
            entities_reltions.append(relation['value'])
            relations.append(relation['value'])

    @staticmethod
    def search_to_root(entities_reltions, dependency_tree_recovered, governor):
        # 当上方关系不是实体或者关系时
        while governor['governorGloss'] not in entities_reltions:
            # 当循环往上找之后，最终只能找到根节点，就退出
            if governor['governorGloss'] == 'ROOT':
                break
            # 往根节点查
            for pre_edge in dependency_tree_recovered:
                if pre_edge['dependent'] == governor['governor']:
                    governor = copy.deepcopy(pre_edge)
                    break

    @staticmethod
    def connect_edge_entity(governor, edge, tokens, entity_dependency_list, entities, relations):
        # 将寻找到的实体和边的依存关系联系起来，并去除根节点的情况
        if governor['governorGloss'] != 'ROOT':
            from_value = edge['dependentGloss']
            from_offset = tokens[edge['dependent'] - 1]['characterOffsetBegin']
            to_value = governor['governorGloss']
            to_offset = tokens[edge['governor'] - 1]['characterOffsetBegin']
            from_type = None
            to_type = None
            if from_value in entities:
                from_type = 'entity'
            elif from_value in relations:
                from_type = 'relation'
            if to_value in entities:
                to_type = 'entity'
            elif to_value in relations:
                to_type = 'relation'
            entity_dependency_list.append({'from': {'value': from_value, 'from_offset': from_offset,
                                                    'type': from_type}, 'to': {'value': to_value,
                                                                               'to_offset': to_offset,
                                                                               'type': to_type}})


if __name__ == '__main__':
    sentence = '在东莞常平司马村珠江啤酒厂斜对面合租的15842062826的老婆'
    entities = [{'type': 'MOB_NUM', 'value': '15842062826', 'code': 220, 'begin': 19, 'end': 31},
                {'type': 'ADDR_VALUE', 'value': '东莞常平司马村珠江啤酒厂', 'code': 310, 'begin': 1, 'end': 14}]
    relations = [{'type': 'HusbandToWife', 'value': '老婆', 'begin': 31, 'end': 33}]
    dp = DependencyParser()
    new_sen, c_entities, c_relations = dp.replace_entities_relations_2(sentence, entities, relations)
