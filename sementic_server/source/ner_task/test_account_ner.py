"""
@description: 测试代码   测试账户识别和命名实体识别功能是否正常
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-05-27
@version: 0.0.1
"""

from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.ner_task.account import get_account_sets

if __name__ == '__main__':
    semantic = SemanticSearch(test_mode=True)
    while True:
        sentence = input("please input:")
        result_account = get_account_sets(sentence)
        result = semantic.sentence_ner_entities(result_account)
        print(result)
