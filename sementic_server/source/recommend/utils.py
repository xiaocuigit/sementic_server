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
    fh = TimedRotatingFileHandler(path, when="D", encoding='utf-8', interval=1, backupCount=0)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.CRITICAL)
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
