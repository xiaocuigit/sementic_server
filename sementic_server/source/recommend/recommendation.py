"""
@description: 推荐模块核心代码
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""
import os
import gensim
import networkx as nx


def google_matrix(graph, alpha=0.85, personalization=None,
                  nodelist=None, weight='weight', dangling=None):
    """Returns the graphoogle matrix of the graph.

    Parameters
    ----------
    graph : graph
      A NetworkX graph.  Undirected graphs will be converted to a directed
      graph with two directed edges for each undirected edge.

    alpha : float
      The damping factor.

    personalization: dict, optional
      The "personalization vector" consisting of a dictionary with a
      key some subset of graph nodes and personalization value each of those.
      At least one personalization value must be non-zero.
      If not specfiied, a nodes personalization value will be zero.
      By default, a uniform distribution is used.

    nodelist : list, optional
      The rows and columns are ordered according to the nodes in nodelist.
      If nodelist is None, then the ordering is produced by graph.nodes().

    weight : key, optional
      Edge data key to use as weight.  If None weights are set to 1.

    dangling: dict, optional
      The outedges to be assigned to any "dangling" nodes, i.e., nodes without
      any outedges. The dict key is the node the outedge points to and the dict
      value is the weight of that outedge. By default, dangling nodes are given
      outedges according to the personalization vector (uniform if not
      specified) This must be selected to result in an irreducible transition
      matrix (see notes below). It may be common to have the dangling dict to
      be the same as the personalization dict.

    Returns
    -------
    A : NumPy matrix
       Google matrix of the graph

    """
    import numpy as np

    if nodelist is None:
        nodelist = list(graph)

    M = nx.to_numpy_matrix(graph, nodelist=nodelist, weight=weight)
    N = len(graph)
    if N == 0:
        return M

    # Personalization vector
    if personalization is None:
        p = np.repeat(1.0 / N, N)
    else:
        p = np.array([personalization.get(n, 0) for n in nodelist], dtype=float)
        p /= p.sum()

    # Dangling nodes
    if dangling is None:
        dangling_weights = p
    else:
        # Convert the dangling dictionary into an array in nodelist order
        dangling_weights = np.array([dangling.get(n, 0) for n in nodelist],
                                    dtype=float)
        dangling_weights /= dangling_weights.sum()
    dangling_nodes = np.where(M.sum(axis=1) == 0)[0]

    # Assign dangling_weights to any dangling nodes (nodes with no out links)
    for node in dangling_nodes:
        M[node] = dangling_weights

    M /= M.sum(axis=1)  # Normalize rows to sum to 1

    return alpha * M + (1 - alpha) * p


def pagerank_numpy(graph, alpha=0.85, personalization=None, weight='weight',
                   dangling=None):
    """Returns the PageRank of the nodes in the graph.

    PageRank computes a ranking of the nodes in the graph graph based on
    the structure of the incoming links. It was originally designed as
    an algorithm to rank web pages.

    Parameters
    ----------
    graph : graph
      A NetworkX graph.  Undirected graphs will be converted to a directed
      graph with two directed edges for each undirected edge.

    alpha : float, optional
      Damping parameter for PageRank, default=0.85.

    personalization: dict, optional
      The "personalization vector" consisting of a dictionary with a
      key some subset of graph nodes and personalization value each of those.
      At least one personalization value must be non-zero.
      If not specfiied, a nodes personalization value will be zero.
      By default, a uniform distribution is used.

    weight : key, optional
      Edge data key to use as weight.  If None weights are set to 1.

    dangling: dict, optional
      The outedges to be assigned to any "dangling" nodes, i.e., nodes without
      any outedges. The dict key is the node the outedge points to and the dict
      value is the weight of that outedge. By default, dangling nodes are given
      outedges according to the personalization vector (uniform if not
      specified) This must be selected to result in an irreducible transition
      matrix (see notes under google_matrix). It may be common to have the
      dangling dict to be the same as the personalization dict.

    Returns
    -------
    pagerank : dictionary
       Dictionary of nodes with PageRank as value.

    """
    import numpy as np
    if len(graph) == 0:
        return {}
    M = google_matrix(graph, alpha, personalization=personalization,
                      weight=weight, dangling=dangling)
    # use numpy LAPACK solver
    eigenvalues, eigenvectors = np.linalg.eig(M.T)
    ind = np.argmax(eigenvalues)
    # eigenvector of largest eigenvalue is at ind, normalized
    largest = np.array(eigenvectors[:, ind]).flatten().real
    norm = float(largest.sum())
    return dict(zip(graph, map(float, largest / norm)))


class DynamicGraph(object):
    """
    根据数据构建动态子图
    """

    def __init__(self, multi=False):
        """
        Load data and init the networkx graph
        :param data: nodes and edges
        :param multi: check is it a multi-graph
        """
        if multi:
            self.graph = nx.MultiDiGraph()
        else:
            self.graph = nx.DiGraph()

        self.node_count = {}
        self.edges_count = {}

    def update_graph(self, nodes, edges):
        """
        清空图里面的节点和边，并更新成最新的节点和边
        :param nodes:
        :param edges:
        :return:
        """
        self.graph.clear()
        self.node_count.clear()
        self.edges_count.clear()

        for node in nodes:
            node_info = dict()
            for pro in node["properties"]:
                node_info[pro["propertyKey"]] = pro["propertyValue"]
            node_info["type"] = node["primaryValue"][:3]

            self.graph.add_node(node["primaryValue"], value=node_info)
            if node_info["type"] not in self.node_count:
                self.node_count[node_info["type"]] = 1
            else:
                self.node_count[node_info["type"]] += 1

        for relation in edges:
            edge_info = dict()
            edge_info["type"] = relation["relationshipType"]
            start, end = None, None
            for pro in relation["properties"]:
                edge_info[pro["propertyKey"]] = pro["propertyValue"]
                if pro["propertyKey"] == "from":
                    start = pro["propertyValue"]
                if pro["propertyKey"] == "to":
                    end = pro["propertyValue"]
            if len(start) != 0 and len(end) != 0:
                self.graph.add_edge(start[0], end[0], type=relation["relationshipType"], value=edge_info)
            if relation["relationshipType"] not in self.edges_count:
                self.edges_count[relation["relationshipType"]] = 1
            else:
                self.edges_count[relation["relationshipType"]] += 1

    def get_similarity_rel_type(self, node_id=None, rel_type=None, rel_name=None, top_num=3):
        """
        获取与 node_id 的 rel_type 关系相近的节点
        :param node_id:
        :param rel_type:
        :param rel_name:
        :param top_num:±
        :return:
        """
        if self.graph is None or node_id is None or rel_type is None:
            return None
        if not self.graph.has_node(node_id):
            return None
        results = list()
        for s, e, rel_info in self.graph.out_edges(node_id, data=True):
            if rel_info["type"] == rel_type:
                results.append({"start_id": s, "end_id": e, "rel_info": rel_info})
        for s, e, rel_info in self.graph.in_edges(node_id, data=True):
            if rel_info["type"] == rel_type:
                results.append({"start_id": s, "end_id": e, "rel_info": rel_info})
        if len(results) != 0:
            return self.__most_similarity_relations(results, rel_name, top_num)
        else:
            return None

    def __most_similarity_relations(self, results, rel_name, top_num):
        """
        从 results 中计算与 rel_name 最相似的 top_num 个关系并返回。
        :param results:
        :param top_num:
        :return:
        """
        pass

    def get_edges_start_end(self, start_id, end_id):
        """
        返回从 start_id 节点到 end_id 节点的所有边的信息
        :param start_id:
        :param end_id:
        :return:
        """
        if self.graph is None:
            return None
        if start_id not in self.graph.nodes or end_id not in self.graph.nodes:
            return None
        edges_info = list()
        for u, v, edge_info in self.graph.out_edges(start_id, data=True):
            if v == end_id:
                edges_info.append((edge_info["type"], edge_info["value"]["relInfo"]))
        return edges_info

    def get_candidate_nodes(self, start_node_id, limited_node_type):
        """
        获取与 start_node_id 节点相连的属于 limited_node_type 类型的节点和边
        :param start_node_id:
        :param limited_node_type:
        :return:
        """
        if self.graph is None:
            return None
        if start_node_id not in self.graph.nodes:
            return None
        results = list()
        # 遍历 start_node_id 节点的所有出边
        for from_id, to_id, edge_info in self.graph.out_edges(start_node_id, data=True):
            node = self.graph.nodes[to_id]
            # 节点是人物或公司节点才会加入推荐候选列表
            if node["value"]["type"] in limited_node_type:
                results.append((to_id, node["value"]["type"], edge_info["type"], edge_info["value"]["relInfo"]))
        # 遍历 start_node_id 节点的所有入边
        for from_id, to_id, edge_info in self.graph.in_edges(start_node_id, data=True):
            node = self.graph.nodes[from_id]
            if node["value"]["type"] in limited_node_type:
                results.append((from_id, node["value"]["type"], edge_info["type"], edge_info["value"]["relInfo"]))
        return results

    def get_page_rank(self):
        """
        return the page rank value of all nodes.
        :return: list
        """
        if self.graph.number_of_nodes() == 0:
            raise ValueError("The graph is empty...")
        pr = pagerank_numpy(self.graph)
        return pr

    def get_nodes(self):
        """
        return all nodes on the graph
        :return:
        """
        return self.graph.nodes(data=True)

    def get_edge_tuples(self):
        """
        return edges info with tuple format.
        :return: list
        """
        edges_tuples = []
        for u, v, t in self.graph.edges.data('type', default='None'):
            edges_tuples.append((v, t, v))
        return edges_tuples

    def get_graph(self):
        """
        return the networkx graph
        :return:
        """
        return self.graph

    def get_degree(self):
        return self.graph.degree(self.graph.nodes)

    def get_in_degree(self):
        return self.graph.in_degree(self.graph.nodes)

    def get_out_degree(self):
        return self.graph.out_degree(self.graph.nodes)

    def get_nodes_edges_count(self):
        return self.node_count, self.edges_count
