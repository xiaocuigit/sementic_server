"""
@description: 推荐模块
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-11
@version: 0.0.1
"""
import os
import json
import redis
import timeit

from pprint import pprint
from sementic_server.source.recommend.recommendation import DynamicGraph
from sementic_server.source.recommend.utils import *


class RecommendServer(object):
    """提供推荐服务"""

    def __init__(self):
        """
        推荐模块初始化操作
        """
        rootpath = str(os.getcwd()).replace("\\", "/")
        if 'source' in rootpath.split('/'):
            base_path = os.path.join(os.path.pardir, os.path.pardir)
        else:
            base_path = os.path.join(os.getcwd(), 'sementic_server')

        log_path = os.path.join(base_path, 'output', 'recommend_logs')
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_file = os.path.join(log_path, 'recommendation.log')
        self.logger = get_logger(name='recommend', path=log_file)

        config_file = os.path.join(base_path, 'config', 'recommend.config')
        if not os.path.exists(config_file):
            self.logger.error("Please config redis first.")
            raise ValueError("Please config redis first.")

        config = json.load(open(config_file, 'r', encoding='utf-8'))

        self.test_data_file = os.path.join(base_path, 'data', 'test_recommend_data',
                                           '1001807032151001902000419975.json')

        # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
        pool = redis.ConnectionPool(host=config["redis"]["ip_address"], port=config["redis"]["port"],
                                    db=config["redis"]["db"], decode_responses=True)
        self.connect = redis.Redis(connection_pool=pool)
        if not self.connect.ping():
            self.logger("Redis connect error, please start redis service first.")
            raise ValueError("Redis connect error, please start redis service first.")

        self.dynamic_graph = DynamicGraph()

    def load_data_from_redis(self, key=None):
        """
        从 Redis 中加载查询子图数据
        :return:
        """
        data = self.connect.hget(name="sub_graph", key=key)
        if data is not None:
            data = json.loads(data)
            pprint(len(data["node"]))
            return data
        return None

    def save_data_to_redis(self, key=None):
        test_data = json.load(open(self.test_data_file, 'r', encoding='utf-8'))
        self.connect.hset(name='sub_graph', key=key, value=json.dumps(test_data))
        print("write done.")

    def get_page_rank_result(self, data=None):
        """
        返回推荐结果
        :param data:
        :return:
        """
        if data is None:
            self.logger.error("data is empty...")
            return None
        self.logger.info("Begin compute PageRank value...")
        start = timeit.default_timer()
        self.dynamic_graph.update_graph(data["node"], data["edges"])
        pr_value = self.dynamic_graph.get_page_rank()
        sorted(pr_value.items(), key=lambda d: d[1], reverse=True)
        self.logger.info("Done.  PageRank Algorithm time consume: {0} S".format(timeit.default_timer() - start))
        return pr_value

    def degree_count(self, data):
        """
        统计子图中节点的入度和出度信息
        :param data:
        :return:
        """
        self.dynamic_graph.update_graph(data["node"], data["edges"])
        in_deg_count = {}
        for id, in_degree in self.dynamic_graph.get_in_degree():
            if in_degree not in in_deg_count:
                in_deg_count[in_degree] = 1
            else:
                in_deg_count[in_degree] += 1

        out_deg_count = {}
        for id, out_degree in self.dynamic_graph.get_out_degree():
            if out_degree not in out_deg_count:
                out_deg_count[out_degree] = 1
            else:
                out_deg_count[out_degree] += 1

        node_count, edge_count = self.dynamic_graph.get_nodes_edges_count()

        pprint("nodes is {0}: ".format(len(self.dynamic_graph.get_nodes())))
        pprint("edges is {0}: ".format(len(self.dynamic_graph.get_edge_tuples())))
        pprint(node_count)
        pprint(edge_count)

        pprint("in_degree")
        pprint(in_deg_count)

        pprint("out_degree")
        pprint(out_deg_count)

    def get_graph_nodes(self):
        return self.dynamic_graph.get_nodes()
