import os
import json
from query_parser import QueryParser
from graph import Graph


if __name__ == '__main__':
    path = os.path.join(os.getcwd(), 'data', 'case5.json')
    with open(path, 'r') as fr:
        data = json.load(fr)
    print(data)

    qg = QueryParser(data)
    g = Graph(qg.query_graph)
    g.show()




