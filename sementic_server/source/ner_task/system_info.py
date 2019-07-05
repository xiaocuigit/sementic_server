"""
@description: 系统配置信息
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""

import os
import json


class SystemInfo(object):
    """
    系统内部配置信息
    """

    # 系统全局设置信息
    THRESHOLD = 0.1  # 相似度阈值
    MIN_SENTENCE_LEN = 2  # 最短可处理的句子长度
    MAX_SENTENCE_LEN = 127  # 最长可处理的句子长度

    # 通过 TF_Serving 来提供的预测服务模式
    MODE_NER = 'NER'  # NER任务
    MODE_SEN = 'SEN_VEC'  # 获取句子向量表示

    # status 字段编码
    # 20X 标识的是服务器正常工作情况下可能返回的字段
    OK = '200'  # 无任何异常情况
    SIMILARITY_LOWER = '201'  # 计算的相似度低于设定的阈值

    # 30X 标识的是服务器请求错误，一旦发生此类错误，直接返回错误标识，不进行其他处理
    INIT_BERT_SERVING_ERROR = '301'  # 初始化BERT-SERVING错误
    BERT_SERVING_TIMEOUT = '302'  # 请求BERT-SERVING超时
    SENTENCE_TOO_SHORT = '303'  # 用户输入句子长度太短
    SENTENCE_TOO_LONG = '304'  # 用户输入句子长度太长

    # 40X 标识的是用户输入数据中存在的错误情况
    MISMATCH_ERROR = '401'  # 账户类型与实际输入不匹配
    ID_CARD_ERROR = '402'  # 用户输入身份证信息有误
    PHONE_ERROR = '403'  # 用户输入手机号格式错误
    LABEL_CODE_ERROR = '404'  # 获取label对应编码错误
    LABEL_UN_DEFINE = '405'  # 未定义的label

    _instance = None  # 单例模式-用来存放实例

    def __init__(self):
        rootpath = str(os.getcwd()).replace("\\", "/")
        if 'source' in rootpath.split('/'):
            self.base_path = os.path.join(os.path.pardir, os.path.pardir)
        else:
            self.base_path = os.path.join(os.getcwd(), 'sementic_server')

        self.config_path = os.path.join(self.base_path, "config")
        self.config_file = "model.config"
        self.config = None

        self.label_path = os.path.join(self.base_path, 'data', 'labels')
        self.account_label_path = os.path.join(self.base_path, 'data', 'yml', 'account_label.yml')

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def get_config(self):
        if self.config is not None:
            return self.config
        else:
            if not os.path.exists(os.path.join(self.config_path, self.config_file)):
                print("The config file is not exists.")

            with open(os.path.join(self.config_path, self.config_file), 'r', encoding='utf-8') as f_r:
                self.config = json.load(f_r)
                return self.config

    def get_labels_path(self):
        return self.label_path

    def get_account_label_path(self):
        return self.account_label_path
