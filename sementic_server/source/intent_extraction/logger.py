"""
@description: 日志文件
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-06-29
@version: 0.0.1
"""


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

