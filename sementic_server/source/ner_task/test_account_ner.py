"""
@description: 测试代码   测试账户识别和命名实体识别功能是否正常
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-06-05
@version: 0.1.1
"""

from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from pprint import pprint

if __name__ == '__main__':
    semantic = SemanticSearch(test_mode=False)
    item_matcher = ItemMatcher(True, is_test=False)
    while True:
        sentence = input("please input:")
        result = item_matcher.match(sentence)
        result_ner = semantic.sentence_ner_entities(result)
        pprint(result_ner)
        entity = result.get('entity') + result.get('accounts')
        relation = result.get('relation')
        intention = result.get('intent')
        data = dict(entity=entity, relation=relation, intent=intention)
        pprint(data)
