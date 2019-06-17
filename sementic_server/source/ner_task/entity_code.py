"""
@description: 与知识库对应的实体编码表
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""


class EntityCode:
    def __init__(self):

        self.account = ['QQNUM', 'MOB', 'PHONE', 'CERT_CODE', 'WEIBO_UID', 'Email', 'WX', 'GROUP_NUM',
                        'WANGWANG', 'UNLABEL']

        self.entities = ['NAME', 'CPNY_NAME', 'ADDR', 'DATE', 'QQNUM', 'MOB', 'PHONE', 'CERT_CODE', 'WEIBO_UID',
                         'Email', 'WX', 'GROUP_NUM', 'WANGWANG', 'UNLABEL']
        self.ner_entities = ['NAME', 'CPNY_NAME', 'ADDR', 'DATE']

    def get_top_label(self, word):
        if word in self.account:
            return "ACCOUNT"
        elif word in self.ner_entities:
            return "NER"
        else:
            return "RELNAME"

    def get_entities(self):
        return self.entities

    def is_account(self, account):
        if account in self.account:
            return True
        else:
            return False
