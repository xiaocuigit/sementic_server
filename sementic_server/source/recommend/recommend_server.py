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
from gensim.models import KeyedVectors
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

        embedding_file = os.path.join(self.base_path, 'data', 'embeddings', 'embedding_relation.txt')
        if not os.path.exists(embedding_file):
            raise ValueError("Relation embedding file do not exist, please add first.")
        self.embedding = None
        try:
            model = KeyedVectors.load_word2vec_format(embedding_file, binary=False)
            model.init_sims()
            self.embedding = model.wv
        except Exception as e:
            self.logger.error("Load Relation Embedding Error: {0}".format(e))
        self.connect = self.__connect_redis()
        self.dynamic_graph = DynamicGraph(multi=True)
        self.person_node_type = "100"
        self.company_node_type = "521"

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
                pprint(len(data["Nodes"]))
                return data
        return None

    def save_data_to_redis(self, file_path, key=None):
        """
        将测试数据写入到 Redis 中
        :param file_path:
        :param key:
        :return:
        """
        if self.connect is None or self.connect.ping() is False:
            self.logger.error("cannot connect to redis, rebuild connection...")
            self.logger.error("Please try again.")
            self.connect = self.__connect_redis()
        else:
            if key is not None:
                test_data = json.load(open(file_path, 'r', encoding='utf-8'))
                self.connect.set(name=key, value=json.dumps(test_data))
                pprint("write done.")

    def get_page_rank_result(self, data=None, key=None):
        """
        返回 PageRank 计算结果
        :param key:
        :param data:
        :return:
        """
        if data is None:
            self.logger.error("data is empty...")
            return None
        self.logger.info("Update the recommend graph...")
        self.dynamic_graph.update_graph(data["Nodes"], data["Edges"])
        self.logger.info("Update the recommend graph done.")
        self.logger.info("There are {0} nodes in graph of {1}.".format(len(self.dynamic_graph.get_nodes()), key))

        self.logger.info("Begin compute PageRank value...")
        start = timeit.default_timer()
        pr_value = self.dynamic_graph.get_page_rank()
        pr_value = sorted(pr_value.items(), key=lambda d: d[1], reverse=True)
        self.logger.info("Done.  PageRank Algorithm time consume: {0} S".format(timeit.default_timer() - start))

        return pr_value

    def get_recommend_entities(self, data, key, person_node_num, company_node_num):
        """
        根据 PageRank 算法推荐指定个数的人物节点和公司节点
        :param data: 图的数据
        :param key: 当前推荐的 key
        :param person_node_num: 指定推荐人物节点的个数
        :param company_node_num: 指定推荐公司节点的个数
        :return:
        """
        pr_value = self.get_page_rank_result(data, key)
        if pr_value is None:
            return {"error": "the graph is empty"}

        person_num = 0
        company_num = 0
        person_uid = list()
        company_uid = list()
        all_uid = list()
        nodes = self.dynamic_graph.get_nodes()
        for node_id, pr in pr_value:
            node = nodes[node_id]["value"]
            node_type = node["type"]
            if node_type == self.person_node_type and person_num < person_node_num:
                person_uid.append({str(node_id): str(pr)})
                all_uid.append({str(node_id): str(pr)})
                person_num += 1
            elif node_type == self.company_node_type and company_num < company_node_num:
                company_uid.append({str(node_id): str(pr)})
                all_uid.append({str(node_id): str(pr)})
                company_num += 1
            elif company_num == company_node_num and person_num == person_node_num:
                break
        return person_uid, company_uid, all_uid

    def get_recommend_relations(self, query_path):
        """
        推荐查询路径上起始节点和终止节点之间存在的所有关系
        :param query_path: 用户查询路径
        :return: 存在的潜在关系
        """
        start_node_id, end_node_id = None, None
        for index, path in enumerate(sorted(query_path.items(), key=lambda x: x[0])):
            if index == 0:
                start_node_id = path[1]["From"]

            if index == len(query_path) - 1:
                end_node_id = path[1]["To"]

        edges_info = None
        if start_node_id and end_node_id:
            edges_info = self.dynamic_graph.get_edges_start_end(start_node_id, end_node_id)
        if edges_info is not None and len(edges_info) != 0:
            result = list()

            # 提取边的 relname 信息，并将其与边的类型对应起来
            # 两个人物节点相连的边的 relInfo 字段信息示例如下，需要解析出 relname 字段的值
            # 'relInfo': ['{fname=王华道, relname=夫妻, dtime=201907011930, domain=kindred.com, tname=王晓萍}']
            for edge_type, info in edges_info:
                rel_name = self.get_rel_name(info)
                if rel_name:
                    result.append({edge_type: rel_name})
            if len(result) != 0:
                return result
            else:
                for edge_type, info in edges_info:
                    info = list(info)
                    info = info[0].lstrip('{').rstrip('}')
                    result.append({edge_type: info})
                return result

        return edges_info

    def get_no_answer_results(self, query_path, person_node_num, company_node_num):
        """
        从查询路径上找到第一个 To 字段为空的子路径，然后获取到该子路径上用户输入的关系名称
        最终推荐给用户与当前查询关系相似的关系连接的实体
        :param query_path:
        :param person_node_num:
        :param company_node_num:
        :return:
        """
        # 解析查询路径
        start_node_id, query_rel_name = None, None
        for index, path in enumerate(sorted(query_path.items(), key=lambda x: x[0])):
            if path[1]["To"] == "0":
                start_node_id = path[1]["From"]
                query_rel_name = path[1]["QueryRel"]
                break
        candidate_list = list()
        if start_node_id is None or query_rel_name is None:
            return candidate_list
        # 以 start_node_id 节点为起始节点遍历其所有边，推荐与当前 query_rel_name 最相似的关系所连接的实体
        # 限制推荐的实体类型：人物实体 和 公司实体
        limited_node_type = [self.person_node_type, self.company_node_type]
        candidate_nodes = self.dynamic_graph.get_candidate_nodes(start_node_id, limited_node_type)
        if len(candidate_nodes) != 0:
            for node_id, node_type, edge_type, edge_info in candidate_nodes:
                rel_name = self.get_rel_name(edge_info)
                if rel_name and rel_name in self.embedding and query_rel_name in self.embedding:
                    # 计算图库中边的 relname 与 query_rel_name 的相似度
                    sim_val = self.embedding.similarity(query_rel_name, rel_name)
                    candidate_list.append((sim_val, node_id, node_type, rel_name, edge_type))
            if len(candidate_list) != 0:
                return self.get_sorted_no_answer_results(candidate_list, person_node_num, company_node_num)

        return candidate_list

    def get_sorted_no_answer_results(self, candidate_list, person_node_num, company_node_num):
        """

        :param candidate_list:
        :param person_node_num:
        :param company_node_num:
        :return:
        """
        person_num = 0
        company_num = 0
        result = list()
        for sim_val, node_id, node_type, rel_name, edge_type in sorted(candidate_list, key=lambda x: x[0],
                                                                       reverse=True):
            if person_num >= person_node_num and company_num >= company_node_num:
                break
            if node_type == self.person_node_type and person_num < person_node_num:
                person_num += 1
                result.append(
                    {"Uid": node_id, "Similarity": str(sim_val), "RelName": rel_name, "RelType": edge_type})
            if node_type == self.company_node_type and company_num < company_node_num:
                company_num += 1
                result.append(
                    {"Uid": node_id, "Similarity": str(sim_val), "RelName": rel_name, "RelType": edge_type})

        return result

    def get_rel_name(self, edge_info, filter="relname"):
        """
        提取图库中边的 filter 字段指定的信息
        :param edge_info:
        :param filter:
        :return:
        """
        try:
            edge_info = list(edge_info)
            edge_info = edge_info[0].lstrip('{').rstrip('}').split(',')
            for line in edge_info:
                line = line.strip()
                if filter in line:
                    return line[len(filter) + 1:]
        except Exception as e:
            self.logger.error("Get {0} error: {1}".format(filter, e))
        return None

    def get_recommend_results(self, key, person_node_num, company_node_num, need_related_relation, no_answer):
        """
        返回最终推荐结果
        :param key:
        :param person_node_num:
        :param company_node_num:
        :param need_related_relation:
        :param no_answer:
        :return:
        """
        result = dict()
        if key is None:
            result["error"] = "RedisKey is empty."
            return result
        data = self.load_data_from_redis(key=key)
        person_uid, company_uid, all_uid = self.get_recommend_entities(data, key, person_node_num, company_node_num)
        result["PersonUid"] = person_uid
        result["CompanyUid"] = company_uid
        result["AllUid"] = all_uid
        query_path = data["QueryPath"]

        if need_related_relation:
            relations = self.get_recommend_relations(query_path)
            if relations is None:
                result["RelatedRelationship"] = list()
            else:
                result["RelatedRelationship"] = relations
        if no_answer:
            no_answer_result = self.get_no_answer_results(query_path, person_node_num, company_node_num)
            result["NoAnswer"] = no_answer_result

        return result

    def degree_count(self, data):
        """
        统计子图中节点的入度和出度信息
        :param data:
        :return:
        """
        self.dynamic_graph.update_graph(data["Nodes"], data["Edges"])
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
