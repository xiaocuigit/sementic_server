"""
@description: 测试代码   测试账户识别和命名实体识别功能是否正常
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-06-05
@version: 0.1.1
"""

from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from sementic_server.source.ner_task.account import Account
from pprint import pprint

if __name__ == '__main__':
    semantic = SemanticSearch()
    item_matcher = ItemMatcher(True)
    account = Account()
    while True:
        sentence = input("please input:")
        accounts_info = account.get_account_labels_info(sentence)
        result = item_matcher.match(sentence, accounts_info=accounts_info)
        result_ner = semantic.sentence_ner_entities(result)
        pprint(result_ner)
        entity = result.get('entity') + result.get('accounts')
        relation = result.get('relation')
        intention = result.get('intent')
        data = dict(entity=entity, relation=relation, intent=intention)
        pprint(data)
