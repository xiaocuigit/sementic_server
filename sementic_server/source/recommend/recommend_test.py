"""
@description: 测试代码
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""

from pprint import pprint
from sementic_server.source.recommend.recommend_server import RecommendServer

if __name__ == '__main__':
    recommend = RecommendServer()
    key = 2
    # recommend.save_data_to_redis(key=key)
    data = recommend.load_data_from_redis(key=key)
    recommend.degree_count(data=data)
    pr_sort = recommend.get_page_rank_result(data)
    nodes = recommend.get_graph_nodes()
    pprint(len(nodes))
    index = 1
    num = 0
    for key, value in pr_sort.items():
        num += 1
        if key in nodes:
            node = nodes[key]["value"]
            if node[:3] == "100":
                index += 1
                pprint("{0} {1} {2}".format(key, value, node))
                print("\n")
        if index == 10:
            break
    print(num)
