import requests
import urllib
import json
from server_config import config


class ServerRequest:

    # 初始化服务器参数
    def __init__(self):
        self.server_ip = config['server_ip']
        self.server_port = config['server_port']
        self.annotators = config['server_type']['depparse']

    # 发送请求到服务器
    def get_dependency(self,data):
        url = 'http://'+self.server_ip+':'+self.server_port+'/?properties={"annotators":"'+self.annotators+'","outputFormat":"json"}'

        # 请求的数据必须编码为UTF-8
        response_json = requests.post(url, data=data.encode('utf-8'))
        response_dict = json.loads(response_json.text)

        dependency_tree = response_dict['sentences'][0]['enhancedPlusPlusDependencies']
        tokens = response_dict['sentences'][0]['tokens']

        return dependency_tree,tokens

if __name__ == '__main__':
    dependency_tree,tokens = ServerRequest().get_dependency('张三的老婆是谁')

    print(dependency_tree)
    print('--------------')
    print(tokens)