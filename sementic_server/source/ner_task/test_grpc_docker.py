"""
@description: 测试代码   测试模型在Docker上部署是否成功
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-05-27
@version: 0.0.1
"""

from sementic_server.source.ner_task.model_tf_serving import ModelServing

if __name__ == '__main__':
    """
    如果可以请求NER服务，输出: NER service test success.
    """
    sen = "在东莞常平司马村珠江啤酒厂斜对面合租的15842062826的老婆"
    model_serving = ModelServing('NER')

    ner_result = model_serving.test_send_grpc_request_ner(sen)

    if ner_result:
        print('NER service test success.')
