"""
@description: 推荐模块核心代码
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""
import networkx as nx
import matplotlib.pyplot as plt


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


def authority_matrix(graph, nodelist=None):
    """Returns the HITS authority matrix."""
    M = nx.to_numpy_matrix(graph, nodelist=nodelist)
    return M.T * M


def hub_matrix(graph, nodelist=None):
    """Returns the HITS hub matrix."""
    M = nx.to_numpy_matrix(graph, nodelist=nodelist)
    return M * M.T


def hits_numpy(graph, normalized=True):
    """Returns HITS hubs and authorities values for nodes.

    The HITS algorithm computes two numbers for a node.
    Authorities estimates the node value based on the incoming links.
    Hubs estimates the node value based on outgoing links.

    Parameters
    ----------
    graph : graph
      A NetworkX graph

    normalized : bool (default=True)
       Normalize results by the sum of all of the values.

    Returns
    -------
    (hubs,authorities) : two-tuple of dictionaries
       Two dictionaries keyed by node containing the hub and authority
       values.
    """
    try:
        import numpy as np
    except ImportError:
        raise ImportError(
            "hits_numpy() requires NumPy: http://scipy.org/")
    if len(graph) == 0:
        return {}, {}
    H = hub_matrix(graph, list(graph))
    e, ev = np.linalg.eig(H)
    m = e.argsort()[-1]  # index of maximum eigenvalue
    h = np.array(ev[:, m]).flatten()
    A = authority_matrix(graph, list(graph))
    e, ev = np.linalg.eig(A)
    m = e.argsort()[-1]  # index of maximum eigenvalue
    a = np.array(ev[:, m]).flatten()
    if normalized:
        h = h / h.sum()
        a = a / a.sum()
    else:
        h = h / h.max()
        a = a / a.max()
    hubs = dict(zip(graph, map(float, h)))
    authorities = dict(zip(graph, map(float, a)))
    return hubs, authorities


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
            self.graph.add_node(node["nodeId"], value=node["primaryValue"], properties=node["properties"])
            if node["primaryValue"][:3] not in self.node_count:
                self.node_count[node["primaryValue"][:3]] = 1
            else:
                self.node_count[node["primaryValue"][:3]] += 1

        for relation in edges:
            self.graph.add_edge(relation["startNodeId"], relation["endNodeId"], type=relation["relationshipType"])
            if relation["relationshipType"] not in self.edges_count:
                self.edges_count[relation["relationshipType"]] = 1
            else:
                self.edges_count[relation["relationshipType"]] += 1

    def show_graph(self, pr_value):
        """
        use matplotlib to show the graph
        :return:
        """
        nx.set_node_attributes(self.graph, name='pr_value', values=pr_value)
        positions = nx.random_layout(self.graph)
        node_size = [x['pr_value'] * 20000 for v, x in self.graph.nodes(data=True)]
        nx.draw_networkx_nodes(self.graph, positions, node_size=node_size, alpha=0.4)
        nx.draw_networkx_edges(self.graph, positions)
        nx.draw_networkx_labels(self.graph, positions, font_size=10)
        plt.show()

    def get_page_rank(self):
        """
        return the page rank value of all nodes.
        :return: list
        """
        if self.graph.number_of_nodes() == 0:
            raise ValueError("The graph is empty...")
        pr = pagerank_numpy(self.graph)
        return pr

    def get_hits(self):
        """
        return the hubs and authorities value of all nodes.
        :return: two list
        """
        hubs, authorities = hits_numpy(self.graph)
        return hubs, authorities

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

    def remove_nodes(self):
        nodes_removed = []
        for node in self.graph.nodes:
            if self.graph.in_degree(node) == 1 and self.graph.out_degree(node) == 0:
                nodes_removed.append(node)
        if len(nodes_removed) != 0:
            self.graph.remove_nodes_from(nodes_removed)

    def get_degree(self):
        return self.graph.degree(self.graph.nodes)

    def get_in_degree(self):
        return self.graph.in_degree(self.graph.nodes)

    def get_out_degree(self):
        return self.graph.out_degree(self.graph.nodes)

    def get_nodes_edges_count(self):
        return self.node_count, self.edges_count
