"""
@description: 与知识库对应的实体编码表
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""


class EntityCode:
    def __init__(self):
        self.codes = {
            'PersonHasAddr': "1008",
            'PersonHasNplace': "1009",
            'PersonHasHplace': "1010",
            'ParentToChild': "1101",
            'HusbandToWife': "1102",
            'BrotherOrSister': "1103",
            'MotherSiblingToChild': "1104",
            'FatherSiblingToChild': "1105",
            'CousinFromFatherSide': "1106",
            'CousinFromMotherSide': "1107",
            'Relative': "1108",
            'SchoolMate': "1109",
            'HotelRoommate': "1201",
            'CheckInHotel': "1202",
            'CompanyHasRegAuthority': "2001",
            'Login': "3001",
            'StaticContact': "3002",
            'GroupHasCreator': "4001",
            'GroupHasMember': "4002",
            'Idcard': "101",
            'Tel': "201",
            'Qiu': "202",
            'MblogUid': "203",
            'Email': "204",
            'WechatNum': "205",
            'Ftel': "303",
            'ADDR': "301",
            'NAME': "901",
            'COMPANY': "902"
        }

        self.account = ['Qiu', 'Tel', 'Ftel', 'Idcard', 'MblogUid', 'Email', 'WechatNum', 'QiuGroup', 'AliPay', 'JD',
                        'UNLABEL']

        self.entities = ['NAME', 'COMPANY', 'ADDR', 'DATE', 'Qiu', 'Tel', 'Ftel', 'Idcard', 'MblogUid', 'Email',
                         'WechatNum', 'QiuGroup', 'AliPay', 'JD', 'UNLABEL']
        self.ner_entities = ['NAME', 'COMPANY', 'ADDR', 'DATE']

    def get_entity_or_relation_code(self, word):
        if word in self.codes:
            return self.codes[word]
        else:
            return None

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
