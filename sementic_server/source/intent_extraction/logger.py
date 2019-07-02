"""
@description: 日志文件
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-06-29
@version: 0.0.1
"""

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


def construt_log(raw_query, correct_info, using_time):
    """
    构建日志文件结构化输出
    :param raw_query: 原始查询
    :param correct_info: 纠错信息
    :param using_time: 纠错模块使用时间
    :return:
    """
    return {
        "raw_query": raw_query,
        "correct_info": correct_info,
        "using_time": using_time
    }

