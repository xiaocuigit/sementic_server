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
from collections import OrderedDict
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
            self.base_path = os.path.join(os.path.pardir, os.path.pardir)
        else:
            self.base_path = os.path.join(os.getcwd(), 'sementic_server')

        log_path = os.path.join(self.base_path, 'output', 'recommend_logs')
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_file = os.path.join(log_path, 'recommendation.log')
        self.logger = get_logger(name='recommend', path=log_file)

        config_file = os.path.join(self.base_path, 'config', 'recommend.config')
        if not os.path.exists(config_file):
            self.logger.error("Please self.config redis first.")
            raise ValueError("Please self.config redis first.")

        self.config = json.load(open(config_file, 'r', encoding='utf-8'))
        self.connect = self.__connect_redis()
        self.dynamic_graph = DynamicGraph()

    def __connect_redis(self):
        """
        与 redis 建立连接
        :return:
        """
        try:
            # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
            pool = redis.ConnectionPool(host=self.config["redis"]["ip_address"],
                                        port=self.config["redis"]["port"],
                                        password=self.config["redis"]["password"],
                                        db=self.config["redis"]["db"],
                                        decode_responses=True, socket_timeout=1,
                                        socket_connect_timeout=1, retry_on_timeout=True)
            connect = redis.Redis(connection_pool=pool)
            if not connect.ping():
                pprint("ping redis error...")
                self.logger("Redis connect error, please start redis service first.")
                return None
            else:
                pprint("Connect redis success...")
                self.logger.info("Connect redis success...")
                return connect
        except Exception as e:
            pprint("Connect redis error: {0}".format(e))
            self.logger.info("Connect redis error: {0}".format(e))
            return None

    def load_data_from_redis(self, key=None):
        """
        从 Redis 中加载查询子图数据
        :return:
        """
        if self.connect is None or self.connect.ping() is False:
            self.logger.error("cannot connect to redis, rebuild connection...")
            self.logger.error("Please try again.")
            self.connect = self.__connect_redis()
        else:
            data = self.connect.get(name=key)
            if data is not None:
                data = json.loads(data)
                pprint(len(data["nodes"]))
                return data
        return None

    def save_data_to_redis(self, data_file, key=None):
        """
        将测试数据写入到 Redis 中
        :param data_file:
        :param key:
        :return:
        """
        if self.connect is None or self.connect.ping() is False:
            self.logger.error("cannot connect to redis, rebuild connection...")
            self.logger.error("Please try again.")
            self.connect = self.__connect_redis()
        else:
            if key is not None:
                test_data = json.load(open(data_file, 'r', encoding='utf-8'))
                self.connect.set(name=key, value=json.dumps(test_data))
                pprint("write done.")

    def get_page_rank_result(self, data=None, key=None):
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
        self.dynamic_graph.update_graph(data["nodes"], data["edges"])
        self.logger.info("There are {0} nodes in graph of {1}.".format(len(self.dynamic_graph.get_nodes()), key))
        pr_value = self.dynamic_graph.get_page_rank()
        pr_value = sorted(pr_value.items(), key=lambda d: d[1], reverse=True)
        self.logger.info("Done.  PageRank Algorithm time consume: {0} S".format(timeit.default_timer() - start))
        return pr_value

    def get_recommend_result(self, key, top_num=10, node_type=None):
        data = self.load_data_from_redis(key=key)
        nodes = self.dynamic_graph.get_nodes()
        index = 0
        results = OrderedDict()
        pr_value = self.get_page_rank_result(data, key)
        if pr_value is None:
            return {"error": "the graph is empty"}
        for node_id, pr in pr_value:
            if node_type and node_id in nodes:
                node = nodes[node_id]["value"]
                if node[:3] == node_type:
                    index += 1
                    results[str(node_id)] = str(pr)
            else:
                index += 1
                results[str(node_id)] = str(pr)
            if index == top_num:
                break

        return results

    def degree_count(self, data):
        """
        统计子图中节点的入度和出度信息
        :param data:
        :return:
        """
        self.dynamic_graph.update_graph(data["nodes"], data["edges"])
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
