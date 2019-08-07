"""
@description: 该文件里面是一些帮助函数
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""

import os
import json
import yaml


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
