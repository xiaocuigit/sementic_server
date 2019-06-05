import os
import json
import networkx as nx
from sementic_server.source.qa_graph.query_parser import QueryParser


class QueryInterface(object):
    def __init__(self, graph):
        self.graph = graph
        self.graph_data = nx.node_link_data(graph)

    def to_query_interface(self):
        pass


if __name__ == '__main__':
    case_num = 2
    # [1, 2, 4]
    if os.path.basename(os.getcwd()) == 'qa_graph':
        path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'test_case', 'case%d.json' % case_num)
    else:
        path = os.path.join(os.getcwd(), 'sementic_server', 'data', 'test_case', 'case%d.json' % case_num)
    path = os.path.abspath(path)

    with open(path, 'r') as fr:
        data = json.load(fr)
    print(data)
    query = data['query']
    start_entity = data['entity'][0]
    qg = QueryParser(data)
    qg.query_graph.show()
    output_path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'output/graph_output')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_path = os.path.join(output_path, 'example.json')
    qg.query_graph.export(output_path)






