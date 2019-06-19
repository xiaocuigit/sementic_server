import requests
import urllib
from server_config import config


class ServerRequest:

    # 初始化服务器参数
    def __init__(self):
        self.server_ip = config['server_ip']
        self.server_port = config['server_port']
        self.annotators = config['server_type']['depparse']

    # 发送请求到服务器
    def send_request(self, data):
        url = 'http://'+self.server_ip+':'+self.server_port+'/?properties={"annotators":"'+self.annotators+'","outputFormat":"json"}'

        # 请求的数据必须编码为UTF-8
        result = requests.post(url, data=data.encode('utf-8'))
        return result.text

if __name__ == '__main__':
    print(ServerRequest().send_request('张三的老婆是谁'))