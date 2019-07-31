"""
@description: 测试代码
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""

import os
import json

from pprint import pprint
from sementic_server.source.recommend.recommend_server import RecommendServer

if __name__ == '__main__':
    recommend = RecommendServer()
    test_data_file = os.path.join(recommend.base_path, 'data', 'test_recommend_data',
                                  '1001508312246002855000840648-0.json')
    key = "5"
    # recommend.save_data_to_redis(file_path=test_data_file, key=key)
    data = recommend.load_data_from_redis(key=key)
    recommend.degree_count(data=data)
    return_data = {"100": "5", "220": "5", "521": "5"}
    bi_direction_edges = "True"
    results = recommend.get_recommend_results(key, return_data, True, True, bi_direction_edges)
    pprint(results)
