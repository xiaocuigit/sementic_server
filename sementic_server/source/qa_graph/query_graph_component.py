"""
@description: 实体对应的子图组件生成过程
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""


import networkx as nx
from sementic_server.source.qa_graph.graph import Graph


class QueryGraphComponent(Graph):
    """
    获取实体，生成相对应的子图组件
    """
    def __init__(self, entity):
        nx.MultiDiGraph.__init__(self)
        self.entity = entity
        account_type_list = ['TEL', 'FTEL', 'QQ', 'WX', 'EMAIL']
        if entity['type'] in account_type_list:
            self.init_account_component()
        elif entity['type'] == 'NAME':
            self.add_edge('p', 'p_name', 'HAS_NAME')
            self.node['p']['label'] = 'concept'
            self.node['p']['type'] = 'PERSON'
            self.node['p_name']['label'] = 'literal'
            self.node['p_name']['type'] = 'string'
            self.node['p_name']['entity'] = entity
        elif entity['type'] == 'ADDRESS':
            self.add_edge('addr', 'addr_name', 'ADDR_NAME')
            self.node['addr']['label'] = 'concept'
            self.node['addr']['type'] = 'ADDRESS'
            self.node['addr_name']['label'] = 'literal'
            self.node['addr_name']['type'] = 'string'
            self.node['addr_name']['entity'] = entity
        else:
            print(entity)
            print('Unknown entity type!')

    def init_account_component(self):
        self.add_edge('person', 'account', 'HAS_%s' % self.entity['type'])
        self.add_edge('account', 'account_num', 'ACCOUNT_NUM')

        self.node['person']['label'] = 'concept'
        self.node['person']['type'] = 'PERSON'

        self.node['account']['label'] = 'concept'
        self.node['account']['type'] = self.entity['type']

        self.node['account_num']['label'] = 'literal'
        self.node['account_num']['type'] = 'string'
        self.node['account_num']['entity'] = self.entity


if __name__ == '__main__':
    e = [{"type": "TEL", "value": "139999999999", "code": 0}, {"type": "NAME", "value": "李四", "code": 0}]
    c0 = QueryGraphComponent(e[0])
    c0.show()
    c1 = QueryGraphComponent(e[1])
    c1.show()

    # g = nx.disjoint_union_all([Graph(c0), Graph(c1)])
    # # c = QueryGraphComponent(e)
    # # g = Graph(c)
    # g.show()
