"""
@description: 实体对应的子图组件生成过程
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import logging
import networkx as nx
from sementic_server.source.qa_graph.graph import Graph


logger = logging.getLogger("server_log")


class QueryGraphComponent(Graph):
    """
    获取实体，生成相对应的子图组件
    """
    def __init__(self, entity):
        logger.info('Getting Graph Component......')
        logger.info('Type: %s \t Value: %s' % (entity['type'], entity['value']))
        nx.MultiDiGraph.__init__(self)
        self.entity = entity

        self.account = ['QQ_NUM', 'MOB_NUM', 'PHONE_NUM', 'IDCARD_VALUE', 'EMAIL_VALUE', 'WECHAT_VALUE', 'QQ_GROUP_NUM',
                        'WX_GROUP_NUM', 'ALIPAY_VALU', 'DOUYIN_VALUE', 'JD_VALUE', 'TAOBAO_VALUE', 'MICROBLOG_VALUE',
                        'UNLABEL', 'VEHCARD_VALUE', 'IMEI_VALUE', 'MAC_VALUE']

        self.ner_entities_dics = {'NAME': 'NAME', 'COMPANY': 'CPNY_NAME', 'ADDR': 'ADDR_VALUE', 'DATE': 'DATE'}

        self.p_has_account_list = ['QQ', 'MobileNum', 'FixedPhone', 'Idcard', 'Email', 'WeChat', 'QQGroup',
                                   'WeChatGroup', 'Alipay', 'DouYin', 'JD', 'TaoBao', 'MicroBlog', 'UNLABEL',
                                   'PlateNum', 'IMEI', 'MAC']
        if entity['type'] in self.account:
            self.init_account_component()
        elif entity['type'] == 'NAME':
            self.add_edge('p', 'p_name', 'NAME')
            self.nodes['p']['label'] = 'concept'
            self.nodes['p']['type'] = 'Person'
            self.nodes['p_name']['label'] = 'literal'
            self.nodes['p_name']['type'] = 'string'
            self.nodes['p_name']['entity'] = entity
        elif entity['type'] == 'CPNY_NAME':
            self.add_edge('comp', 'comp_name', 'CPNY_NAME')
            self.nodes['comp']['label'] = 'concept'
            self.nodes['comp']['type'] = 'Company'
            self.nodes['comp_name']['label'] = 'literal'
            self.nodes['comp_name']['type'] = 'string'
            self.nodes['comp_name']['entity'] = entity
        elif entity['type'] == 'ADDR_VALUE':
            self.add_edge('addr', 'addr_name', 'ADDR_VALUE')
            self.nodes['addr']['label'] = 'concept'
            self.nodes['addr']['type'] = 'Addr'
            self.nodes['addr_name']['label'] = 'literal'
            self.nodes['addr_name']['type'] = 'string'
            self.nodes['addr_name']['entity'] = entity
        else:
            logger.info('Unknown type: %s' % entity['type'])

    def entity_type_mapping(self):
        """
        由于本体定义与实体定义未统一
        将实体类型做一个映射
        :return:
        """
        mapping = {'NAME': 'Person', 'COMPANY': 'Company', 'ADDR': 'Addr'}
        if self.entity['type'] in mapping.keys():
            temp_type = mapping[self.entity['type']]
        else:
            temp_type = self.entity['type']
        new_type = temp_type
        self.entity['type'] = new_type

    def init_account_component(self):
        t = self.entity['type']
        index = self.account.index(t)
        edge_type = self.p_has_account_list[index]

        self.add_edge('p', 'account', 'Phas%s' % edge_type)
        self.add_edge('account', 'account_num', t)

        self.nodes['p']['label'] = 'concept'
        self.nodes['p']['type'] = 'Person'

        self.nodes['account']['label'] = 'concept'
        self.nodes['account']['type'] = edge_type

        self.nodes['account_num']['label'] = 'literal'
        self.nodes['account_num']['type'] = 'string'
        self.nodes['account_num']['entity'] = self.entity


if __name__ == '__main__':
    e = [{"type": "MOB_NUM", "value": "139999999999", "code": 0}, {"type": "NAME", "value": "李四", "code": 0}]
    c0 = QueryGraphComponent(e[0])
    c0.show()
    c1 = QueryGraphComponent(e[1])
    c1.show()

