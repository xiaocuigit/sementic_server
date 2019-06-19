"""
@description: 联调测试接口
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import os
from pprint import pprint

from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.ner_task.account import get_account_sets
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from sementic_server.source.qa_graph.query_interface import QueryInterface

if __name__ == '__main__':
    semantic = SemanticSearch(test_mode=True)
    item_matcher = ItemMatcher(True, is_test=True)
    while True:
        sentence = input("please input:")
        intent = item_matcher.match(sentence)
        result_account = get_account_sets(intent["query"])
        result = semantic.sentence_ner_entities(result_account)
        print(dict(result))
        print(intent)

        entity = dict(result).get('entity')
        relation = intent.get('relation')
        intention = intent.get('intent')

        data = dict(entity=entity, relation=relation, intent=intention)

        query_graph_result = dict()
        try:
            qg = QueryParser(data)
            # 这里有问题
            query_graph = qg.query_graph.get_data()
            qi = QueryInterface(qg.query_graph, sentence)
            query_interface = qi.get_query_data()
            query_graph_result = {'query_graph': query_graph, 'query_interface': query_interface}
            pprint(query_graph_result)
        except Exception as e:
            pprint(e)



