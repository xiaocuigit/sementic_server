"""
@description: 联调测试接口
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import os
import json
from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.ner_task.account import get_account_sets
from sementic_server.source.intent_extraction.ItemMatcher import ItemMatcher

if __name__ == '__main__':
    semantic = SemanticSearch(test_mode=True)
    item_matcher = ItemMatcher(new=True)
    while True:
        sentence = input("please input:")
        intent = item_matcher.matcher(sentence)
        result_account = get_account_sets(sentence)
        result = semantic.sentence_ner_entities(result_account)
        print(dict(result))
        print(intent)

        entity = dict(result).get('entity')
        relation = intent.get('relation')
        intention = intent.get('intent')
        if intention == '0':
            intention = 'PERSON'
        data = dict(entity=entity, relation=relation, intent=intention)

        try:
            qg = QueryParser(data)
            qg.query_graph.show()

            output_path = os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'output', 'graph_output')
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_path = os.path.join(output_path, 'example.json')
            qg.query_graph.export(output_path)
        except Exception as e:
            print(e)



