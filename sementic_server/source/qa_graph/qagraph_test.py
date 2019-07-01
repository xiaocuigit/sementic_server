"""
@description: 联调测试接口
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""

import os
from pprint import pprint
import json
from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from sementic_server.source.qa_graph.query_interface import QueryInterface
from sementic_server.source.dependency_parser.dependency_parser import DependencyParser

if __name__ == '__main__':
    semantic = SemanticSearch()
    item_matcher = ItemMatcher(new_actree=True)
    dependency_parser = DependencyParser()
    while True:
        sentence = input("please input:")
        intent = item_matcher.match(sentence)
        result = semantic.sentence_ner_entities(intent)
        pprint(result)
        entity = result.get('entity') + result.get('accounts')
        relation = result.get('relation')
        intention = result.get('intent')
        dependency_tree_recovered, tokens_recovered, dependency_graph, entities, relations = \
            dependency_parser.get_denpendency_tree(result["query"], entity, relation)
        pprint(dependency_graph)
        dep = dependency_graph
        data = dict(entity=entity, relation=relation, intent=intention)
        pprint('dep')
        pprint(dep)
        try:
            query_graph_result = dict()
            t = dict(data=data, dep=dep)
            p = os.path.join(os.getcwd(), 'test_case.json')
            json.dump(t, open(p, 'w'))
            qg = QueryParser(data, dep)
            query_graph = qg.query_graph.get_data()
            if not query_graph:
                qg = QueryParser(data)
                query_graph = qg.query_graph.get_data()
            qi = QueryInterface(qg.query_graph, intent["query"])
            query_interface = qi.get_query_data()
            query_graph_result = {'query_graph': query_graph, 'query_interface': query_interface}
            pprint(query_graph_result)
        except Exception as e:
            pprint(e)
