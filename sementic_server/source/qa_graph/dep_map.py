"""
@description: 依存分析使用
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-06-21
@version: 0.0.1
"""

import os
import json
import logging
import networkx as nx
from sementic_server.source.qa_graph.graph import Graph


logger = logging.getLogger("server_log")


class DepMap(object):
    """
    将依存分析结果映射到图上
    初始化的三个参数为依存信息、关系组件列表、实体组件列表
    """
    def __init__(self, dependency, r_components, e_components):
        logger.info('components assemble by dependency...')
        self.dependency = dependency
        self.r_components = r_components
        self.e_components = e_components
        self.dep_graph = None
        self.dep_graph_list = list()
        self.init_dep_graph()
        """
        依存分析结果分为以下情况讨论：
        1、实体指向关系
        2、关系指向实体
        3、实体指向实体(暂时当作非正常情况)
        4、其他（非正常情况）
        """

    def init_dep_graph(self):
        for item in self.dependency:
            f = item['from']
            t = item['to']
            if f['type'] == 'entity' and t['type'] == 'relation':
                temp_graph = self.from_ent_to_rel(f['value'], t['value'])
                self.dep_graph_list.append(temp_graph)
            elif f['type'] == 'relation' and t['type'] == 'entity':
                temp_graph = self.from_rel_to_ent(f['value'], t['value'])
                self.dep_graph_list.append(temp_graph)
        if len(self.dep_graph_list) == 0:
            return
        self.dep_graph = nx.disjoint_union_all(self.dep_graph_list)
        mapping = dict()
        for i, n in enumerate(self.dep_graph.nodes):
            mapping[n] = i
        nx.relabel_nodes(self.dep_graph, mapping, copy=False)
        self.dep_graph = Graph(self.dep_graph)

    def get_entity_component(self, e_value):
        """
        找到含有e_value的子图
        :param e_value: 依存分析中的某个词
        :return: 含有e_value的子图
        """
        for entity_graph in self.e_components:
            for node in entity_graph.nodes:
                if entity_graph.nodes[node]['label'] == 'literal' \
                        and entity_graph.nodes[node]['entity']['value'] == e_value:
                    return entity_graph

    def get_rel_component(self, r_value):
        """
        找到含有r_value的子图
        :param r_value: 依存分析中的某个词
        :return: 含有r_value的子图
        """
        for rel_graph in self.r_components:
            for e in rel_graph.edges:
                data = rel_graph.get_edge_data(e[0], e[1], e[2])
                if data['value'] == r_value:
                    mapping = {e[0]: 'proc', e[1]: 'succ'}
                    nx.relabel_nodes(rel_graph, mapping, copy=False)
                    return rel_graph

    def from_ent_to_rel(self, e, r):
        e_graph = self.get_entity_component(e)
        r_graph = self.get_rel_component(r)
        temp_graph = nx.union(e_graph, r_graph)
        mapping = {'proc': 'p'}
        nx.relabel_nodes(temp_graph, mapping, copy=False)
        return temp_graph

    def from_rel_to_ent(self, r, e):
        eg = self.get_entity_component(e)
        rg = self.get_rel_component(r)
        temp_graph = nx.disjoint_union(eg, rg)
        return temp_graph

    def check_dep(self):
        """
        判断依存分析结果是否为一个实体指向关系，或者关系指向实体
        :return:
        """
        for item in self.dependency:
            f = item['from']
            t = item['to']
            if f['type'] == t['type']:
                return False
        return True


if __name__ == '__main__':
    case_num = 2
    path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    path = os.path.abspath(path)

    with open(path, 'r') as fr:
        data = json.load(fr)
    # print(data)
    dep = data['dependency']
    print(dep)


