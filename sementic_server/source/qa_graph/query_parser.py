"""
@description: 问答图生成过程
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import networkx as nx
import json
import os
import itertools
import csv
import copy
from sementic_server.source.qa_graph.graph import Graph
from sementic_server.source.qa_graph.query_graph_component import QueryGraphComponent

DEFAULT_EDGE = dict()
RELATION_DATA = dict()


def init_default_edge():
    if os.path.basename(os.getcwd()) == 'qa_graph':
        path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'ontology', 'default_relation.csv')
    else:
        path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'ontology', 'default_relation.csv')
    path = os.path.abspath(path)
    # path = os.path.join(os.getcwd(), 'ontology', 'default_relation.csv')
    with open(path, 'r') as csv_file:
        csv_file.readline()
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
            DEFAULT_EDGE[line[0]] = {'domain': line[1], 'range': line[2]}


def init_relation_data():
    global RELATION_DATA
    if os.path.basename(os.getcwd()) == 'qa_graph':
        relation_path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'ontology', 'relation.json')
    else:
        relation_path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'ontology', 'relation.json')
    relation_path = os.path.abspath(relation_path)
    with open(relation_path, 'r') as fr:
        RELATION_DATA = json.load(fr)


init_default_edge()
init_relation_data()


class QueryParser:
    def __init__(self, query_data):
        self.relation = query_data.setdefault('relation', list())
        self.entity = query_data.setdefault('entity', list())
        self.intent = query_data.setdefault('intent', 'PERSON')

        self.relation_component_list = list()
        self.entity_component_list = list()
        # 获取实体和关系对应的子图组件
        self.init_relation_component()
        self.init_entity_component()
        # 得到子图组件构成的集合，用图表示
        self.component_graph = nx.disjoint_union_all(self.relation_component_list + self.entity_component_list)
        self.query_graph = copy.deepcopy(self.component_graph)
        self.query_graph = Graph(self.query_graph)
        self.old_query_graph = copy.deepcopy(self.component_graph)

        self.node_type_dict = self.query_graph.node_type_statistic()
        self.component_assemble()

        while len(self.query_graph.nodes) != len(self.old_query_graph.nodes) \
                and not nx.algorithms.is_weakly_connected(self.query_graph):
            # 节点一样多说明上一轮没有合并
            # 图已连通也不用合并
            self.old_query_graph = copy.deepcopy(self.query_graph)
            # self.node_type_dict = dict()
            self.node_type_dict = self.query_graph.node_type_statistic()
            self.component_assemble()
        self.add_intention()

        while not nx.algorithms.is_weakly_connected(self.query_graph):
            # 若不连通则在联通分量之间添加默认边
            flag = self.add_default_edge()
            if not flag:
                print('未添加上说明缺少默认边')
                # 未添加上说明缺少默认边
                break

    def add_default_edge(self):
        flag = False
        components_set = self.query_graph.get_connected_components_subgraph()
        # d0 = {'ADDRESS': [0], 'PERSON':[1, 2]}
        d0 = Graph(components_set[0]).node_type_statistic()
        d1 = Graph(components_set[1]).node_type_statistic()
        candidates = itertools.product(d0.keys(), d1.keys())
        candidates = list(candidates)
        for key, edge in DEFAULT_EDGE.items():
            for c in candidates:
                if c[0] == edge['domain'] and c[1] == edge['range']:
                    node_0 = d0[edge['domain']][0]
                    node_1 = d1[edge['range']][0]
                    self.query_graph.add_edge(node_0, node_1, key)
                    flag = True
                    return flag
                elif c[1] == edge['domain'] and c[0] == edge['range']:
                    node_0 = d1[edge['domain']][0]
                    node_1 = d0[edge['range']][0]
                    self.query_graph.add_edge(node_0, node_1, key)
                    flag = True
                    return flag
        return flag

    def add_intention(self):
        # 也需要依存分析,待改进
        for n in self.query_graph.nodes:
            if self.query_graph.node[n]['label'] == 'concept':
                node_type = self.query_graph.node[n]['type']
                if node_type == self.intent:
                    self.query_graph.node[n]['intent'] = True
                    break

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
                    relation_component.node[n]['label'] = 'concept'

                relation_component.node['temp_0']['type'] = RELATION_DATA[r['type']]['domain']
                relation_component.node['temp_1']['type'] = RELATION_DATA[r['type']]['range']
                self.relation_component_list.append(relation_component)


if __name__ == '__main__':
    data_dict = {
        "entity": [{"type": "NAME",
                    "value": "张三",
                    "code": 0},
                   {"type": "TEL", "value": "139999999999", "code": 0}],
        "relation": [{"type": "ParentToChild",
                      "value": "父亲",
                      "offset": 3,
                      "code": 0},
                     ],
        "intent": 'PERSON'
    }
    qg = QueryParser(data_dict)
    qg.query_graph.show()
    # g = Graph(qg.query_graph)
    # g.show()
    qg.query_graph.export('query_graph')


