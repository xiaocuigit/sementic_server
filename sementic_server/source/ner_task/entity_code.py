"""
@description: 与知识库对应的实体编码表
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""

import yaml
import os


class EntityCode(object):
    """实体名称及编码类"""

    def __init__(self):

        self.account = ['QQ_NUM', 'MOB_NUM', 'PHONE_NUM', 'IDCARD_VALUE', 'EMAIL_VALUE', 'WECHAT_VALUE', 'QQ_GROUP_NUM',
                        'WX_GROUP_NUM', 'ALIPAY_VALU', 'DOUYIN_VALUE', 'JD_VALUE', 'TAOBAO_VALUE', 'MICROBLOG_VALUE',
                        'UNLABEL']

        self.ner_entities_dics = {'NAME': 'NAME', 'COMPANY': 'CPNY_NAME', 'ADDR': 'ADDR_VALUE', 'DATE': 'DATE'}
        rootpath = str(os.getcwd()).replace("\\", "/")
        if 'source' in rootpath.split('/'):
            f_r = open(os.path.join(os.getcwd(), os.path.pardir, os.path.pardir, 'data', 'yml', 'node_code.yml'),
                       encoding='utf-8')
        else:
            f_r = open(os.path.join(os.getcwd(), 'sementic_server', 'data', 'yml', 'node_code.yml'), encoding='utf-8')

        self.entities_code = yaml.load(f_r, Loader=yaml.SafeLoader)

        self.account_label = {"EMAIL": "EMAIL_VALUE",
                              "MPHONE": "MOB_NUM",
                              "PHONE": "PHONE_NUM",
                              "QQ": "QQ_NUM",
                              "QQ_GROUP": "QQ_GROUP_NUM",
                              "WX_GROUP": "WX_GROUP_NUM",
                              "WECHAT": "WECHAT_VALUE",
                              "ID": "IDCARD_VALUE",
                              "MBLOG": "MICROBLOG_VALUE",
                              "ALIPAY": "ALIPAY_VALU",
                              "DOUYIN": "DOUYIN_VALUE",
                              "TAOBAO": "TAOBAO_VALUE",
                              "JD": "JD_VALUE",
                              "UNLABEL": "UNLABEL"}
        self.punctuation = [',', '，', '~', '!', '！', '。', '.', '?', '？']

    def get_account(self):
        return self.account

    def get_ner_entities(self):
        return self.ner_entities_dics

    def get_entities(self):
        return list(self.ner_entities_dics.values()) + self.account

    def is_account(self, account):
        if account in self.account:
            return True
        else:
            return False

    def get_entity_code(self):
        return self.entities_code

    def get_account_label(self):
        return self.account_label
