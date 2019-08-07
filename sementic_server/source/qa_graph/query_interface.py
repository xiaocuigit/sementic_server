"""
@description: 实现从问答图到查询接口的转化
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-06-02
@version: 0.0.1
"""


import os
import json
import logging
from copy import deepcopy
import networkx as nx
from sementic_server.source.qa_graph.query_parser import QueryParser, RELATION_DATA
from sementic_server.source.qa_graph.graph import Graph

logger = logging.getLogger("server_log")


class QueryInterface(object):
    """
    实现从问答图到查询接口的转化
    """
    def __init__(self, graph, query):
        self.graph = nx.convert_node_labels_to_integers(graph)
        self.graph = Graph(self.graph)

        self.query = query
        # 用于指出查询意图为某归属属性的情况
        self.intention_tail = ''

        self.entities = dict()
        self.init_entities()

        self.rels = list()
        self.init_rels()
        self.intentions = list()
        self.init_intention()
        self.query_dict = dict()

        self.serial_process()
        self.add_rels_to_entities()
        self.final_delete()
        self.init_query_dict()

    def add_rels_to_entities(self):
        """
        将关系挂到相关实体上
        :return:
        """
        for rel in self.rels:
            rel_id = rel['id']
            entity_1, entity_2 = rel['rel'].split('-')
            self.add_rel_to_entities(rel_id, entity_1)
            self.add_rel_to_entities(rel_id, entity_2)

    def add_rel_to_entities(self, rel_id, entity_id):
        """
        将一个关系的id挂到相关实体上
        :param rel_id:
        :param entity_id:
        :return:
        """
        for _, entities in self.entities.items():
            for e in entities:
                if e['id'] == entity_id:
                    if not e.get('rel'):
                        e['rel'] = list()
                    e['rel'].append(rel_id)
                    return

    def literal_node_reduction(self):
        """
        将图上所有字面值节点规约为与其直接相连的对象节点的一个属性值
        :return: new graph
        """
        new_graph = deepcopy(self.graph)
        for node in self.graph.nodes:
            if self.graph.nodes[node]['label'] == 'literal':
                key = self.graph.nodes[node]['entity']['type']
                value = self.graph.nodes[node]['entity']['value']
                temp_dict = dict()
                temp_dict[key] = value
                for p in self.graph.predecessors(node):
                    if 'data' not in new_graph.nodes[p].keys():
                        new_graph.nodes[p]['data'] = dict()
                    if key not in new_graph.nodes[p]['data'].keys():
                        new_graph.nodes[p]['data'][key] = list()
                    """
                    new_graph.nodes[p]['data'].update(temp_dict)
                    """
                    new_graph.nodes[p]['data'][key].append(value)
                    new_graph.remove_edge(p, node)
                    new_graph.remove_node(node)
        return new_graph

    def node_rename(self):
        """
        将节点按类型信息改名
        :return:
        """
        # 此Dict用于将图中节点改名
        map_dict = dict()
        for node in self.graph.nodes:
            if not isinstance(node, int):
                continue
            if self.graph.nodes[node]['label'] == 'concept':
                map_dict[node] = self.graph.nodes[node]['type'].lower() + '%d' % node
            if self.graph.nodes[node].get('intent') and self.graph.is_none_node(node):
                """
                # map_dict[node] = self.graph.nodes[node]['type'].upper() + 'S'
                """
                map_dict[node] = get_complex(self.graph.nodes[node]['type']).upper()
        new_graph = nx.relabel_nodes(self.graph, mapping=map_dict)
        self.graph = new_graph

    def is_belong_property(self, edge):
        """
        判断一条边是否对应归属属性
        :param edge: (n, m, k)三元组，表示从n-k->m
        :return:
        """
        n, m, k = edge
        for key, value in RELATION_DATA.items():
            if k == key and value['belong']:
                dom = self.graph.nodes[n]['type']
                ran = self.graph.nodes[m]['type']
                if dom == value['domain'] and ran == value['range']:
                    return True
        return False

    def belong_reduction(self):
        """
        按边是否属于归属属性，对图进行规约
        :return:
        """
        new_graph = deepcopy(self.graph)
        for edge in self.graph.edges:
            if self.is_belong_property(edge):
                # 如果这条边对应归属属性
                # 将后一个节点的信息添加到前一个节点
                # 还要将后一个点的所有边添加到前一个点
                # 删除后一个节点
                n1, n2, k = edge
                if n1 not in new_graph.nodes or n2 not in new_graph.nodes:
                    continue
                if n2.isupper():
                    # 说明后一个节点为查询意图，不再规约
                    self.intention_tail = '.%s' % new_graph.nodes[n2].get('type')
                    # new_graph.remove_node(n2)
                    continue
                remain_belong_reduction(new_graph, n1, n2)
        return new_graph

    def graph_reduction(self):
        """
        对图结构进行规约
        :return:
        """
        self.node_rename()
        self.graph = self.literal_node_reduction()
        self.graph = self.belong_reduction()

    def init_entities(self):
        """
        将图中的实体进行处理，得到接口中对应的实体
        :return:
        """
        self.graph_reduction()
        for node in self.graph.nodes:
            # 空节点也占一个
            temp_dict = dict()
            node_type = self.graph.nodes[node]['type']
            if node_type not in self.entities.keys():
                self.entities[node_type] = list()
            temp_dict['id'] = node
            temp_data = self.graph.nodes[node].get('data')
            if temp_data:
                temp_dict.update(self.graph.nodes[node].get('data'))
            self.entities[node_type].append(temp_dict)

    def init_rels(self):
        for i, edge in enumerate(self.graph.edges):
            n, m, k = edge
            if self.is_belong_property((n, m, k)):
                continue
            edge_id = i+1
            temp_dict = dict()

            temp_dict['id'] = 'relation%d' % edge_id
            self.graph.get_edge_data(n, m, k)['edge_id'] = 'relation%d' % edge_id
            temp_dict['rel'] = '%s-%s' % (str(n), str(m))
            temp_dict['type'] = k
            temp_dict['value'] = self.graph.get_edge_data(n, m, k).get('value')
            self.rels.append(temp_dict)

    def get_intent_node(self):
        for node in self.graph.nodes:
            if self.graph.nodes[node].get('intent'):
                return node

    def isolated_node_process(self, shortest_path):
        for node in self.graph.nodes:
            if node not in shortest_path:
                for p in self.graph.predecessors(node):
                    if 'data' not in self.graph.nodes[p].keys():
                        self.graph.nodes[p]['data'] = dict()
                    for k, v in self.graph.get_edge_data(p, node).items():
                        temp_dict = {k: node}
                        self.graph.nodes[p]['data'].update(temp_dict)

    def init_intention(self):
        top_sort = nx.topological_sort(self.graph)
        current = next(top_sort)
        header = current
        intention_str = str(header)

        intent_node = self.get_intent_node()
        shortest_path = nx.shortest_path(self.graph, header, intent_node)

        for node in shortest_path:
            if node == header:
                continue
            old = current
            current = node
            edge = self.graph.get_edge_data(old, current, default=None)
            k = list(edge.keys())[0]
            if self.is_belong_property((old, current, k)):
                continue
            if edge:
                for v in edge.values():
                    edge_id = v['edge_id']
                    intention_str += '.%s' % str(edge_id)
        intention_str += self.intention_tail
        self.intentions.append(intention_str)
        # 未在最短路径上的点，处理
        self.isolated_node_process(shortest_path)
        # self.init_entities()

    def init_query_dict(self):
        self.query_dict['query'] = self.query
        self.query_dict['intentions'] = self.intentions
        self.query_dict['entities'] = self.entities
        self.query_dict['rels'] = self.rels

    def get_query_data(self):
        q_data = dict_low_case(self.query_dict)
        return q_data

    def serial_process(self):
        """
        对查询实体重新按顺序编号
        :return:
        """
        for e_type in self.entities:
            temp_type = e_type.lower()
            flag = False
            for n, e in enumerate(self.entities[e_type]):
                entity_id = e['id']
                if entity_id == entity_id.upper():
                    # 存在一个全大写的实体
                    flag = True
                    continue
                if flag:
                    new_id = '%s%d' % (temp_type, n)
                else:
                    new_id = '%s%d' % (temp_type, n + 1)

                self.find_replace(entity_id, new_id)
                e['id'] = new_id

    def find_replace(self, entity_id, new_id):
        """
        在intention和rels查找entity_id替换为new_id
        :param entity_id:
        :param new_id:
        :return:
        """
        intent_str = self.intentions[0]
        intent_str = intent_str.replace(entity_id, new_id)
        self.intentions[0] = intent_str
        for relation in self.rels:
            relation['rel'] = relation['rel'].replace(entity_id, new_id)

    def final_delete(self):
        """
        针对测试需求，删除全大写的实体
        :return:
        """
        for e_type in self.entities:
            for e in self.entities[e_type]:
                entity_id = e['id']
                if entity_id == entity_id.upper() and not e.get('rel'):
                    self.entities[e_type].remove(e)
                    break
            if len(self.entities[e_type]) == 0:
                self.entities.pop(e_type)
                break


def get_complex(word):
    """
    获取一个词的复数形式
    :param word:
    :return:
    """
    word = word.lower()
    mapping = {'company': 'companies', 'entity': 'entities'}
    if word[-1] == 's':
        return word
    if word in mapping.keys():
        return mapping[word]
    else:
        return '%ss' % word


def dict_low_case(input_obj):
    """
    将input_dict全改为小写
    :param input_obj:
    :return:
    """
    if isinstance(input_obj, dict):
        new_dict = dict()
        for k, v in input_obj.items():
            if isinstance(v, list):
                k = get_complex(k)
            new_dict[k.lower()] = dict_low_case(v)
        return new_dict
    elif isinstance(input_obj, list):
        new_list = list()
        for i in input_obj:
            new_list.append(dict_low_case(i))
        return new_list
    elif isinstance(input_obj, str):
        return input_obj.lower()
    else:
        return input_obj


def add_succ_to_pre(new_graph, n1, n2, succ):
    """
    将n2的所有后继节点给n1
    :param new_graph:
    :param n1:
    :param n2:
    :param succ
    :return:
    """
    for s in succ:
        for p1, p2, k in new_graph.edges:
            if p1 == n2 and p2 == s:
                edge_data = new_graph.get_edge_data(p1, p2, k)
                new_graph.add_edge(n1, s, k, **edge_data)


def remain_belong_reduction(new_graph, n1, n2):
    """
    belong_reduction函数拆分出来的部分，以减少复杂度
    :return:
    """
    if n1 not in new_graph.nodes or n2 not in new_graph.nodes:
        return
    succ = new_graph.successors(n2)
    succ = list(succ)
    if len(succ) > 0:
        add_succ_to_pre(new_graph, n1, n2, succ)
    n2_dict = new_graph.nodes[n2].get('data')
    if 'data' not in new_graph.nodes[n1].keys():
        new_graph.nodes[n1]['data'] = dict()
    if n2_dict:
        """
        new_graph.nodes[n1]['data'].update(n2_dict)
        """
        for k, v in n2_dict.items():
            if k in new_graph.nodes[n1]['data'].keys():
                new_graph.nodes[n1]['data'][k].extend(v)
            else:
                new_graph.nodes[n1]['data'][k] = v
        new_graph.remove_node(n2)
    else:
        k = new_graph.nodes[n2]['type']
        new_graph.nodes[n1]['data'][k] = list()
        new_graph.remove_node(n2)


if __name__ == '__main__':
    case_num = 1
    # [1, 2, 4]
    if os.path.basename(os.getcwd()) == 'qa_graph':
        path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    else:
        path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'test_case', 'case%d.json' % case_num)
    path = os.path.abspath(path)

    with open(path, 'r') as fr:
        data = json.load(fr)
    print(data)
    q = data['query']

    qg = QueryParser(data)
    qg.query_graph.show()
    qi = QueryInterface(qg.query_graph, q)
    qi.graph.show()

    output_path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'output', 'graph_output')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    example_output_path = os.path.join(output_path, 'example.json')
    qg.query_graph.export(example_output_path)

    interface_path = os.path.join(output_path, 'interface.json')
    json.dump(qi.get_query_data(), open(interface_path, 'w'))
