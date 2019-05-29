"""
@description: 问答图测试接口
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import os
import json
from sementic_server.source.qa_graph.query_parser import QueryParser


if __name__ == '__main__':
    case_num = 2
    # [1, 2, 4]
    if os.path.basename(os.getcwd()) == 'qa_graph':
        path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    else:
        path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'test_case', 'case%d.json' % case_num)
    path = os.path.abspath(path)

    try:
        with open(path, 'r') as fr:
            data = json.load(fr)
        print(data)
        qg = QueryParser(data)
        qg.query_graph.show()

        output_path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'output')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_path = os.path.join(output_path, 'example.json')
        qg.query_graph.export(output_path)
    except Exception as e:
        print(e)




