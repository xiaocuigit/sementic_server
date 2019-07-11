"""
@description: 问答图到查询接口自测模块
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-06-02
@version: 0.0.1
"""


import os
import json
from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.qa_graph.query_interface import QueryInterface

if __name__ == '__main__':
    case_num = 11
    p = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    p = os.path.abspath(p)

    with open(p, 'r') as fr:
        data = json.load(fr)
    # print(data)
    print(data['query'])
    print(data['entity'])
    print(data['relation'])
    qg = QueryParser(data, data['dependency'])
    qg.query_graph.show()

    qi = QueryInterface(qg.query_graph, data['query'])
    data = qi.get_query_data()
    print(data)
    query_graph = qg.query_graph.get_data()
    query_interface = data
    query_graph_result = {'query_graph': query_graph, 'query_interface': query_interface}

