"""
依存分析请求

@Author: Xu Ze
@Time: 2019-06-29
@Version: 0.1.0
"""

import requests
import json
from sementic_server.source.ner_task.system_info import SystemInfo


class ServerRequest(object):
    """依存分析连接器"""

    # 初始化服务器参数
    def __init__(self):
        self.config = SystemInfo().get_config()
        self.server_ip = self.config['server_ip']
        self.server_port = self.config['server_port']
        self.annotators = self.config['server_type']['depparse']

    # 发送请求到服务器
    def get_dependency(self, data):
        url = 'http://' + self.server_ip + ':' + self.server_port + '/?properties={"annotators":"' + \
              self.annotators + '","outputFormat":"json"}&pipelineLanguage=zh'

        # 请求的数据必须编码为UTF-8
        response_json = requests.post(url, data=data.encode('utf-8'))
        response_dict = json.loads(response_json.text)

        dependency_tree = response_dict['sentences'][0]['enhancedPlusPlusDependencies']
        tokens = response_dict['sentences'][0]['tokens']

        return dependency_tree, tokens


if __name__ == '__main__':
    dependency_tree, tokens = ServerRequest().get_dependency('张三的老婆是谁')

    print(dependency_tree)
    print('--------------')
    print(tokens)
