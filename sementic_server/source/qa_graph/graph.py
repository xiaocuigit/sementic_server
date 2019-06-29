"""
@description: 图结构的基类
@author: Xu Zhongkai
@email: 1399350807@qq.com
@time: 2019-05-27
@version: 0.0.1
"""

import networkx as nx
import json
import logging

logger = logging.getLogger("server_log")


class Graph(nx.MultiDiGraph):
    """
    图基类实现
    """
    def __init__(self, graph=None, file_path=None):
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as fr:
                    data = json.load(fr)
                graph = nx.node_link_graph(data)
            except Exception as e:
                logger.error(e)
        nx.MultiDiGraph.__init__(self, graph)

    def get_connected_components_subgraph(self):
        # 获取连通子图
        component_list = list()
        for c in nx.weakly_connected_components(self):
            component = self.subgraph(c)
            component_list.append(component)
        return component_list

    def is_none_node(self, node):
        if self.nodes[node]['label'] != 'concept':
            return False
        neighbors = self.neighbors(node)
        for n in neighbors:
            # 目前判断条件为出边没有字面值，认为是空节点
            # 考虑拓扑排序的终点
            if self.nodes[n]['label'] == 'literal':
                return False
        return True

    def get_none_nodes(self, node_type=None):
        # 获取指定节点类型下的空节点
        none_node_list = list()
        for node in self.nodes:
            if self.is_none_node(node):
                if node_type and self.nodes[node].get('type') != node_type:
                    continue
                none_node_list.append(node)
        return none_node_list

    def node_type_statistic(self):
        """
        统计每种类型的节点的个数
        """
        node_type_dict = dict()
        for n in self.nodes:
            if self.nodes[n]['label'] == 'concept':
                node_type = self.nodes[n]['type']
                if node_type not in node_type_dict.keys():
                    node_type_dict[node_type] = list()
                node_type_dict[node_type].append(n)
        return node_type_dict

    def export(self, file_path):
        """将图导出至文件"""
        temp_graph = nx.MultiDiGraph(self)
        data = nx.node_link_data(temp_graph)
        with open(file_path, 'w', encoding='utf-8') as fw:
            json.dump(data, fw)

    def get_data(self):
        """输出结果"""
        temp_graph = nx.MultiDiGraph(self)
        data = nx.node_link_data(temp_graph)
        return data

    def show(self):
        """将图显示至屏幕"""
        if not self:
            logger.info("There is nothing to show!")
            return
        flag = True
        if not self.is_multigraph():
            flag = False
        print('=================The graph have %d nodes==================' % len(self.nodes))
        logger.info('=================The graph have {0} nodes=================='.format(len(self.nodes)))
        for n in self.nodes:
            data = self.nodes[n]
            print(str(n).ljust(30), '\t', str(data).ljust(30))
            logger.info("{0}\t{1}".format(str(n).ljust(30), str(data).ljust(30)))
        # print('=================The graph have %d edges==================' % len(self.edges))
        print('The graph have %d edges'.center(100, '=') % len(self.edges))
        logger.info('The graph have %d edges'.center(100, '=') % len(self.edges))
        for e in self.edges:
            # multigraph的边结构为(u, v, k)
            # 非multigraph的边结构为(u, v)
            if flag:
                data = self.get_edge_data(e[0], e[1], e[2])
            else:
                data = self.get_edge_data(e[0], e[1])
            print(str(e).ljust(30), '\t', str(data).ljust(30))
            logger.info(str(e).ljust(30), '\t', str(data).ljust(30))


if __name__ == '__main__':
    test_graph = nx.complete_graph(5)
    g = Graph(test_graph)
    g.show()
    g.export('text')
