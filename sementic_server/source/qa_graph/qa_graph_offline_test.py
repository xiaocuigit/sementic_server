"""
@description: 问答图到查询接口自测模块
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-06-02
@version: 0.0.1
"""


import os
import json
from pprint import pprint
from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.qa_graph.query_interface import QueryInterface

if __name__ == '__main__':
    case_num = 19
    p = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    print(p)
    p = os.path.abspath(p)
    print(p)

    with open(p, 'r') as fr:
        data = json.load(fr)
    # print(data)
    print('query', data['query'])
    print('entity', data['entity'])
    print('relation', data['relation'])
    qg = QueryParser(data)
    qg.query_graph.show()
    if qg.error_info:
        print(qg.error_info)

    # try:
    qi = QueryInterface(qg.query_graph, data['query'])
    interface_data = qi.get_query_data()
    # except Exception as e:
    #     print(e)
    #     print('查询接口转化失败！')

    print(interface_data)
    query_graph = qg.query_graph.get_data()
    query_interface = interface_data
    query_graph_result = {'query_graph': query_graph, 'query_interface': query_interface}
    pprint(query_graph_result)
    json.dump(query_graph_result, open('test.json', 'w'))
    if qg.error_info:
        print(qg.error_info)
