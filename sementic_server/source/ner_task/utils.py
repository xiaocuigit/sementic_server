"""
@description: 提供一些工具函数
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-02-27
@version: 0.0.1
"""
from collections import defaultdict

import os
import codecs
import json
import logging
import timeit
import numpy as np

ACCOUNT_MAP = {"QQ_NUM": "QQ",
               "MOB_NUM": "Tel",
               "PHONE_NUM": "Ftel",
               "IDCARD_VALUE": "Idcard",
               "EMAIL_VALUE": "Email",
               "WECHAT_VALUE": "WechatNum",
               "QQ_GROUP_NUM": "QQGroup",
               "WX_GROUP_NUM": "WeChatGroup",
               "ALIPAY_VALUE": "Alipay",
               "DOUYIN_VALUE": "DouYin",
               "JD_VALUE": "JD",
               "TAOBAO_VALUE": "TaoBao",
               "MICROBLOG_VALUE": "MblogUid",
               "VEHCARD_VALUE": "VEHCARD_VALUE",
               "IMEI_VALUE": "IMEI_VALUE",
               "MAC_VALUE": "MAC_VALUE",
               "UNLABEL": "UNLABEL"}


def load_config(config_dir):
    """
    根据 model 值加载对应模型的配置文件
    :return: config dictionaries
    """

    config_file = os.path.join(config_dir, 'model.config')

    assert os.path.isfile(config_file), "please change parm path to file"

    with open(config_file, encoding='utf-8') as f:
        return json.load(f)


def cos_sim(vector_a, vector_b):
    """
    计算两个向量之间的余弦相似度
    :param vector_a:
    :param vector_b:
    :return:
    """
    vector_a = np.mat(vector_a)
    vector_b = np.mat(vector_b)
    num = float(vector_a * vector_b.T)
    denom = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
    if denom == 0:
        cos = 0
    else:
        cos = num / denom
    sim = 0.5 + 0.5 * cos
    return sim


def get_logger(log_file):
    """
    将logger信息输出到log_file文件中
    :param log_file:
    :return:
    """
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


def is_chinese(uchar):
    """
    判断一个unicode是否是汉字
    :param uchar:
    :return:
    """
    if (uchar >= u'\u4e00') and (uchar <= u'\u9fa5'):
        return True
    else:
        return False


def get_consume_time(start_time):
    """
    计算程序从 start_time 到当前时间的的运行时间
    :param start_time:
    :return:
    """
    end_time = timeit.default_timer()
    tt = end_time - start_time
    m, s = divmod(tt, 60)
    h, m = divmod(m, 60)
    return h, m, s


def get_file_name(path, suffix):
    """
    获取path路径下指定后缀的所有文件名
    :param path:
    :param suffix:
    :return:
    """
    f_list = os.listdir(path)
    files = []
    for i in f_list:
        if os.path.splitext(i)[1] == suffix:
            files.append(i)
    return files


def print_config(config, logger):
    """
    Print configuration of the model
    """
    for k, v in config.items():
        logger.info("{}:\t{}".format(k.ljust(15), v))


def save_predict_results(save_path, id_to_char, id_to_tag, sentences, sentences_len_list, tags_pred, tags_real=None):
    """
    将模型的预测结果保存到 save_path 文件中

    :param id_to_tag:
    :param save_path:
    :param id_to_char:
    :param sentences:
    :param sentences_len_list:
    :param tags_real:
    :param tags_pred:
    :return: 没一行有三个元素： [汉字，真实标签，预测标签]。
    """
    with codecs.open(save_path, 'w', 'utf-8') as file:
        for i in range(len(sentences)):
            length = sentences_len_list[i]
            chars = sentences[i][:length]
            pred = tags_pred[i][:length]

            if tags_real is not None:
                real = tags_real[i][:length]
                for c, r, p in zip(chars, real, pred):
                    line = str(id_to_char[c]) + " " + str(id_to_tag[r]) + " " + str(id_to_tag[p]) + "\n"
                    file.write(line)
            else:
                for c, p in zip(chars, pred):
                    line = str(id_to_char[c]) + " " + str(id_to_tag[p]) + "\n"
                    file.write(line)
                file.write('\n')


def convert_id_to_label(pred_ids_result, idx2label):
    """
    将id形式的结果转化为真实序列结果
    :param pred_ids_result:
    :param idx2label:
    :return:
    """
    curr_seq = []
    for ids in pred_ids_result:
        if ids == 0:
            break
        curr_label = idx2label[ids]
        if curr_label in ['[CLS]', '[SEP]']:
            continue
        curr_seq.append(curr_label)
    return curr_seq


def convert_data_format(data):
    accounts = data.get('accounts', None)
    ner_entities = data.get('entity', None)
    relations = data.get('relation', None)

    result = dict()
    result['query'] = data.get('query', "")
    result['templateMatch'] = {'similarity': '0.00', 'template': "", 'code': '0'}
    entity = dict()
    if accounts:
        acc = list()
        for t in accounts:
            if t["type"] in ACCOUNT_MAP:
                acc.append({"tag": ACCOUNT_MAP[t["type"]], "value": t["value"], "code": t["code"]})
        entity["account"] = acc

    if ner_entities:
        ner_name = list()
        ner_add_com = list()
        for n in ner_entities:
            if n["type"] == "NAME":
                ner_name.append(n["value"])
            elif n["type"] == "CPNY_NAME" or n["type"] == "ADDR_VALUE":
                ner_add_com.append(n["value"])

        if len(ner_name) != 0:
            entity["name"] = ner_name
        if len(ner_add_com) != 0:
            entity["addrOrInstitution"] = ner_add_com

    if relations:
        rels = list()
        for rel in relations:
            rels.append({"tag": rel["type"], "value": rel["value"], "code": rel["code"]})
        if len(rels) != 0:
            entity["relName"] = rels

    result["entities"] = entity
    return result
