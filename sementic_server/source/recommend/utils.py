"""
@description: 该文件里面是一些帮助函数
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""
from collections import defaultdict

import os
import json
import yaml
import logging

from logging.handlers import TimedRotatingFileHandler


def get_logger(name, path):
    """
    定义日志文件
    :param name:日志名
    :param path:日志路径
    :return:
    """
    # 定义日志文件
    logger = logging.getLogger(name)  # 不加名称设置root logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    # 使用FileHandler输出到文件, 文件默认level:ERROR
    fh = TimedRotatingFileHandler(path, when="D", encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.FATAL)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def data_load(data_file):
    """
    加载图库返回的数据，包括：点和边
    :param data_file:
    :return:
    """
    if not os.path.exists(data_file):
        raise ValueError("data_path is not exist.")
    with open(data_file, 'r', encoding='utf-8') as f_r:
        test_data = json.load(f_r)
        return test_data


def get_node_relation_type():
    """
    获取节点和关系的类型
    :return:
    """
    rootpath = str(os.getcwd()).replace("\\", "/")
    if 'source' in rootpath.split('/'):
        base_path = '../'
    else:
        base_path = os.path.join(os.getcwd(), 'recommendation_kg')

    node_file = os.path.join(base_path, 'data', 'yml', 'node_type.yml')
    node_types = yaml.load(open(node_file, encoding='utf-8'), Loader=yaml.SafeLoader)

    relation_file = os.path.join(base_path, 'data', 'yml', 'relation_type.yml')
    relation_types = yaml.load(open(relation_file, encoding='utf-8'), Loader=yaml.SafeLoader)

    return node_types, relation_types


def construct_edges(data):
    relation_dict = defaultdict(list)
    for edge in data["edges"]:
        relation_dict[edge["startNodeId"]].append({"end": edge["endNodeId"], "type": edge["relationshipType"]})

    node_dict = defaultdict()
    for node in data["nodes"]:
        node_dict[node["nodeId"]] = node

    return node_dict, relation_dict


def write_to_neo4j(data):
    from py2neo import Graph, Node, Relationship

    graph = Graph("http://localhost:7474", username="neo4j", password="123456")
    # CREATE CONSTRAINT ON (N:MyNode) ASSERT N.nodeId IS UNIQUE
    graph.delete_all()
    create_nodes = {}
    for node_raw in data["Nodes"]:
        node = Node("Node", nodeId=node_raw["primaryValue"])

        if node_raw["primaryValue"] not in create_nodes:
            create_nodes[node_raw["primaryValue"]] = node

        node.add_label(node_raw["primaryValue"][:3])
        graph.create(node)

    for edge in data["Edges"]:
        edge_info = dict()
        edge_info["type"] = edge["relationshipType"]
        start, end = None, None
        for pro in edge["properties"]:
            edge_info[pro["propertyKey"]] = pro["propertyValue"]
            if pro["propertyKey"] == "from":
                start = pro["propertyValue"][0]
            if pro["propertyKey"] == "to":
                end = pro["propertyValue"][0]

        if start in create_nodes and end in create_nodes:
            relation = Relationship(create_nodes[start], edge["relationshipType"], create_nodes[end])
            graph.create(relation)
        else:
            print("=========error=========")
            print(start)
            print(end)
            print("=========error=========")


if __name__ == '__main__':
    # data_file = '../../data/test_recommend_data/1001807032313002679000665513-1001903151412004888000003465.json'
    data_file = '../../data/test_recommend_data/1001711081640003790000917493.json'
    write_to_neo4j(data_load(data_file))
