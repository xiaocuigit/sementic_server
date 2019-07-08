"""
@description: 问答图生成过程
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import networkx as nx
import logging
import os
import itertools
import pandas as pd
import csv
import json
import copy
from sementic_server.source.qa_graph.graph import Graph
from sementic_server.source.qa_graph.query_graph_component import QueryGraphComponent
from sementic_server.source.qa_graph.dep_map import DepMap

DEFAULT_EDGE = dict()
RELATION_DATA = dict()
logger = logging.getLogger("server_log")


def init_default_edge():
    """
    初始化默认边列表
    :return:
    """
    if os.path.basename(os.getcwd()) == 'qa_graph':
        path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'ontology', 'default_relation.csv')
    else:
        path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'ontology', 'default_relation.csv')
    path = os.path.abspath(path)
    with open(path, 'r') as csv_file:
        csv_file.readline()
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
            DEFAULT_EDGE[line[0]] = {'domain': line[1], 'range': line[2]}


def init_relation_data():
    """
    将object_attribute.csv中的对象属性读取为一个关系字典
    :return:
    """
    global RELATION_DATA
    if os.path.basename(os.getcwd()) == 'qa_graph':
        relation_path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir,
                                     'data', 'ontology', 'object_attribute.csv')
    else:
        relation_path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'ontology', 'object_attribute.csv')
    df = pd.read_csv(relation_path)
    for i, row in df.iterrows():
        temp_dict = dict()
        temp_dict['domain'] = row['domain']
        temp_dict['range'] = row['range']
        if not isinstance(row['belong'], bool):
            row['belong'] = False
        temp_dict['belong'] = row['belong']
        RELATION_DATA[row['property']] = temp_dict


init_default_edge()
init_relation_data()


class QueryParser(object):
    """
    动态问答图语义解析模块
    """
    def __init__(self, query_data, dependency=None):
        logger.info('Query Graph Parsing...')
        # print('Query Graph Parsing...')
        self.relation = query_data.setdefault('relation', list())
        self.entity = query_data.setdefault('entity', list())
        self.intent = query_data['intent']
        self.dependency = dependency
        self.relation_component_list = list()
        self.entity_component_list = list()
        # 获取实体和关系对应的子图组件
        self.init_relation_component()
        self.init_entity_component()

        # 若有依存分析，根据依存分析来获取组件图
        if self.dependency and len(self.dependency) > 0:
            logger.info('dependency exist.')
            # print('dependency exist.')
            dm = DepMap(self.dependency, self.relation_component_list, self.entity_component_list)
            if dm.check_dep():
                # 使用依存分析，获取self.component_graph
                if dm.dep_graph and nx.algorithms.is_weakly_connected(dm.dep_graph):
                    self.query_graph = dm.dep_graph
                else:
                    logger.info('dependency wrong!')
                    # print('dependency wrong!')

        self.query_graph = None
        # 得到子图组件构成的集合，用图表示
        self.component_graph = nx.disjoint_union_all(self.relation_component_list + self.entity_component_list)
        self.query_graph = copy.deepcopy(self.component_graph)
        self.query_graph = Graph(self.query_graph)
        self.old_query_graph = copy.deepcopy(self.component_graph)
        self.query_graph.show()
        self.node_type_dict = self.query_graph.node_type_statistic()
        self.component_assemble()

        while len(self.query_graph.nodes) != len(self.old_query_graph.nodes) \
                and not nx.algorithms.is_weakly_connected(self.query_graph):
            # 节点一样多说明上一轮没有合并
            # 图已连通也不用合并
            self.old_query_graph = copy.deepcopy(self.query_graph)
            self.node_type_dict = self.query_graph.node_type_statistic()
            self.component_assemble()
        while not nx.algorithms.is_weakly_connected(self.query_graph):
            # 若不连通则在联通分量之间添加默认边
            flag = self.add_default_edge()
            if not flag:
                logger.info('default edge missing!')
                # 未添加上说明缺少默认边
                break

        # 经过上面两个循环，得到连通的图，下面确定意图
        self.determine_intention()

    def add_default_edge(self):
        flag = False
        components_set = self.query_graph.get_connected_components_subgraph()
        d0 = Graph(components_set[0]).node_type_statistic()
        d1 = Graph(components_set[1]).node_type_statistic()
        candidates = itertools.product(d0.keys(), d1.keys())
        candidates = list(candidates)
        trick_index = -1
        for key, edge in DEFAULT_EDGE.items():
            for c in candidates:
                if c[0] == edge['domain'] and c[1] == edge['range']:
                    node_0 = d0[edge['domain']][trick_index]
                    node_1 = d1[edge['range']][trick_index]
                    self.query_graph.add_edge(node_0, node_1, key)
                    flag = True
                    return flag
                elif c[1] == edge['domain'] and c[0] == edge['range']:
                    node_0 = d1[edge['domain']][trick_index]
                    node_1 = d0[edge['range']][trick_index]
                    self.query_graph.add_edge(node_0, node_1, key)
                    flag = True
                    return flag
        return flag

    def determine_intention_by_type(self):
        # 根据意图类型来确定意图，对应determine_intention中的1.2
        for n in self.query_graph.nodes:
            if self.query_graph.nodes[n]['label'] == 'concept':
                node_type = self.query_graph.nodes[n]['type']
                if node_type == self.intent:
                    self.add_intention_on_node(n)
                    break

    def add_intention_on_node(self, node):
        self.query_graph.nodes[node]['intent'] = True

    def add_intention_on_nodes(self, node_list):
        """
        在一批节点中优先选择person节点进行插入
        :param node_list: 带插入的一组空节点
        :return:
        """
        for node in node_list:
            if self.query_graph.nodes[node]['type'] == 'Person':
                self.query_graph.nodes[node]['intent'] = True
                return
        # 若找不到person
        node = node_list[0]
        self.query_graph.nodes[node]['intent'] = True

    def get_intention_candidate(self):
        """
        获取候选意图节点id
        :return:候选意图节点id
        """
        candidates_list = list()
        if self.intent:
            # 意图识别提供了意图类型
            # print(self.intent)
            for n in self.query_graph.nodes:
                if self.query_graph.nodes[n].get('type') == self.intent:
                    candidates_list.append(n)
        if len(candidates_list) == 0:
            # print('intention recognizer module produce wrong intention!')
            logger.info('intention recognizer module produce wrong intention!')
            intention_candidates = self.query_graph.get_concept_nodes()
        else:
            intention_candidates = [x for x in self.query_graph.nodes if x in candidates_list]

        none_nodes = self.query_graph.get_none_nodes(self.intent)
        if len(none_nodes) > 0:
            intention_candidates = [x for x in intention_candidates if x in none_nodes]
        person_nodes = self.get_person_nodes(intention_candidates)
        if len(person_nodes) > 0:
            return person_nodes
        return intention_candidates

    def determine_intention(self):
        """
        确定意图：
        1. 意图识别模块通过关键词，获取意图类型；
        2. 根据依存分析模块，将句法依存树根节点附近的实体节点中作为候选意图节点，若上一步得到了意图类型，删去候选意图中的与意图类型冲突的节点；
        3. 在所有候选节点中，若有空节点（即没有字面值描述的节点），则将候选节点集合中的所有空节点作为新的候选节点集合；
        4. 若上一步选出的节点有多个，则优先选择Person类型的节点。
        5. 在候选节点集合中，按照候选意图节点的入度与出度之差，对候选节点进行排序，选出入度与出度之差最大的节点；
        :return:
        """
        intention_candidates = self.get_intention_candidate()
        in_degree_centrality = nx.in_degree_centrality(self.query_graph)
        out_degree_centrality = nx.out_degree_centrality(self.query_graph)

        criterion_dict = dict()
        for node in intention_candidates:
            criterion_dict[node] = in_degree_centrality[node]/(1+out_degree_centrality[node])

        m = max(criterion_dict.values())
        # 考虑到多个节点上都有最大值
        intention_nodes = [k for k, v in criterion_dict.items() if v == m]
        intention_node = None
        if len(intention_nodes) > 1:
            intention_node = self.get_person_nodes(intention_nodes)
        if intention_node:
            self.add_intention_on_node(intention_node)
        else:
            self.add_intention_on_node(intention_nodes[0])

    def get_person_nodes(self, candidates):
        """
        从候选节点中选出任务person的节点
        :param candidates:
        :return:
        """
        node_list = list()
        for node in candidates:
            if self.query_graph.nodes[node].get('type') == 'Person':
                node_list.append(node)
        return node_list

    def component_assemble(self):
        # 之后根据依存分析来完善
        for k, v in self.node_type_dict.items():
            if len(v) >= 2:
                combinations = itertools.combinations(v, 2)
                for pair in combinations:
                    # 若两个节点之间连通，则跳过，不存在则合并
                    test_graph = nx.to_undirected(self.query_graph)
                    if nx.has_path(test_graph, pair[0], pair[1]):
                        continue
                    else:
                        mapping = {pair[0]: pair[1]}
                        nx.relabel_nodes(self.query_graph, mapping, copy=False)
                        break

    def init_entity_component(self):
        for e in self.entity:
            component = QueryGraphComponent(e)
            self.entity_component_list.append(nx.MultiDiGraph(component))

    def init_relation_component(self):
        for r in self.relation:
            if r['type'] in RELATION_DATA.keys():
                relation_component = nx.MultiDiGraph()
                relation_component.add_edge('temp_0', 'temp_1', r['type'], **r)
                for n in relation_component.nodes:
                    relation_component.nodes[n]['label'] = 'concept'

                relation_component.nodes['temp_0']['type'] = RELATION_DATA[r['type']]['domain']
                relation_component.nodes['temp_1']['type'] = RELATION_DATA[r['type']]['range']
                self.relation_component_list.append(relation_component)


if __name__ == '__main__':
    q = '在东莞常平司马村珠江啤酒厂斜对面合租的15842062826的老婆'
    case_num = 6
    p = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    p = os.path.abspath(p)

    with open(p, 'r') as fr:
        data = json.load(fr)
    # print(data)
    dp = data['dependency']
    # print('dependency', d)

    qg = QueryParser(data, data['dependency'])
    qg.query_graph.show()
