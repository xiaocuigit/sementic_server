"""
@description: 与知识库对应的实体编码表
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""

import yaml
import os


class EntityCode:
    def __init__(self):

        self.account = ['QQ', 'MobileNumber', 'FixedPhone', 'Idcard_DL', 'Idcard_TW', 'Email', 'WeChat', 'QQGroup',
                        'WeChatGroup', 'Alipay', 'DouYin', 'JD', 'TaoBao', 'MicroBlog', 'UNLABEL']

        self.ner_entities_dics = {'NAME': 'Person', 'COMPANY': 'Company', 'ADDR': 'Addr', 'DATE': 'DATE'}

        if os.getcwd().split('/')[-1] == 'sementic_server_v2':
            f_r = open(os.path.join(os.getcwd(), 'sementic_server', 'data', 'yml', 'node_code.yml'), encoding='utf-8')
        else:
            f_r = open(os.path.join(os.getcwd(), '../../', 'data', 'yml', 'node_code.yml'), encoding='utf-8')

        self.entities_code = yaml.load(f_r, Loader=yaml.SafeLoader)

    def get_entities(self):
        return list(self.ner_entities_dics.values()) + self.account

    def get_ner_entities(self):
        return self.ner_entities_dics

    def is_account(self, account):
        if account in self.account:
            return True
        else:
            return False

    def get_entity_code(self):
        return self.entities_code
