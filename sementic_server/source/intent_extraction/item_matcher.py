"""
@description: 匹配接口
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-05-29
@version: 0.0.1
"""

from os.path import join, exists
from os import mkdir
import pickle
import yaml
import logging
from time import time
from sementic_server.source.ner_task.account import get_account_labels_info, UNLABEL
from sementic_server.source.intent_extraction.recognizer import Recognizer
from sementic_server.source.intent_extraction.system_info import SystemInfo
from sementic_server.source.intent_extraction.logger import construt_log, get_logger


server_logger = logging.getLogger("server_log")


def load_actree(pkl_path):
    """
    加载已保存的Recognizer实例
    :param pkl_path:
    :return:ac自动机对象
    """
    start = time()
    with open(pkl_path, "rb") as f:
        reg = pickle.load(f)
        server_logger.info(f"Loading AC-Tree \"{pkl_path.split('/')[-1]}\", time used: {time() - start}")
        return reg


def build_actree(dict_info, pkl_path):
    """
    创建Recognizer实例
    :param pkl_path:
    :return:ac自动机对象
    """
    start = time()
    reg = Recognizer(dict_info)
    pickle.dump(reg, open(pkl_path, "wb"))
    server_logger.info(f"Building AC-Tree \"{pkl_path.split('/')[-1]}\", time used: {time() - start}")

    return reg


def _resolve_list_confilct(raw_list, ban_list):
    """
    消解raw_list和ban_list的冲突
    :param raw_list: 需要被消解冲突的部分
    :param ban_list: 禁止出现的位置索引
    :return:
    """
    if ban_list == list():
        return raw_list

    res_list = []
    index_ban = set()
    for ban in ban_list:
        if type(ban) in {list, tuple}:
            index_ban.update(list(range(ban[0], ban[1])))
        else:
            index_ban.update(list(range(ban["begin"], ban["end"])))

    for item in raw_list:
        if type(item) in {list, tuple}:
            item_range = list(range(item[0], item[1]))
        else:
            item_range = list(range(item["begin"], item["end"]))
        if index_ban.intersection(item_range) == set():
            res_list.append(item)
    return res_list


def replace_items_in_sentence(sentence, items):
    """
    替换句子在item中出现的元素
    :param sentence: 原始句子
    :param items: 需要替换的item ((begin, end, value),())
    :return:
    """
    size = len(items)
    if size < 1:
        return sentence
    sentence_after_replace = ""
    index = 0
    range_cursor = (items[index][0], items[index][1])  # 指针指向index指向的begin, end
    for position, char in enumerate(sentence):
        if range_cursor[0] < position <= range_cursor[1] - 1:
            continue
        elif position is range_cursor[0]:      # 如果这个位置是items中某个item的开始位置，则加上这个item的值
            sentence_after_replace += items[index][2]
        else:
            sentence_after_replace += char

        if position is range_cursor[1] - 1:
            index += 1
            range_cursor = (items[index][0], items[index][1]) if index <= size - 1 else (-1, -1)

    return sentence_after_replace


def _update_account_in_sentence(accounts: list, sentence: str):
    """
    更新账号在句子中的位置
    :param accounts:
    :param sentence:
    :return:
    """
    for index, info in enumerate(accounts):
        begin = sentence.find(info["value"])
        if begin is not info["begin"]:
            accounts[index]["begin"] = begin
            accounts[index]["end"] = begin + len(info["value"])


class ItemMatcher(object):
    """
    @description: 匹配接口类
    @author: Wu Jiang-Heng
    @email: jiangh_wu@163.com
    @time: 2019-05-29
    @version: 0.0.1
    """
    def __init__(self, new_actree=False, is_test=False):
        self.reg = None     # 识别AC
        self.corr = None    # 纠错AC
        si = SystemInfo(is_test)
        self.correct_logger = get_logger("correction", si.log_path_corr)

        # 获得根目录的地址
        self.dir_data = join(si.base_path, "data")
        self.dir_yml = join(self.dir_data, "yml")

        self.dir_output = join(si.base_path, "output")
        self.dir_pkl = join(self.dir_output, "pkl")

        # 获得关系词和疑问词的类型词典和纠错词典
        self.relations, self.relation_code, self.ques_word, self.wrong_word = dict(), dict(), dict(), dict()
        try:
            self.relations = yaml.load(open(join(self.dir_yml, "relation.yml"),
                                            encoding="utf-8"), Loader=yaml.SafeLoader)
            self.relation_code = yaml.load(open(join(self.dir_yml, "relation_code.yml"),
                                            encoding="utf-8"), Loader=yaml.SafeLoader)
            self.ques_word = yaml.load(open(join(self.dir_yml, "quesword.yml"),
                                            encoding="utf-8"), Loader=yaml.SafeLoader)
            self.wrong_word = yaml.load(open(join(self.dir_yml, "wrong_table.yml"),
                                            encoding="utf-8"), Loader=yaml.SafeLoader)

        except FileNotFoundError as e:
            server_logger.error(f"Cannot find the file in {self.dir_yml}, {e}")

        self.reg_dict = self.relations.copy()
        self.reg_dict.update(self.ques_word)

        # actree
        if not exists(self.dir_pkl):
            mkdir(self.dir_pkl)
        self.path_corr = join(self.dir_pkl, "corr.pkl")
        self.path_reg = join(self.dir_pkl, "reg.pkl")

        if new_actree:
            self.corr = build_actree(dict_info=self.wrong_word, pkl_path=self.path_corr)
            self.reg = build_actree(dict_info=self.reg_dict, pkl_path=self.path_reg)
        else:
            if not exists(self.path_corr):
                self.corr = build_actree(dict_info=self.wrong_word, pkl_path=self.path_corr)
            else:
                self.corr = load_actree(pkl_path=self.path_corr)

            if not exists(self.path_reg):
                self.reg = build_actree(dict_info=self.reg_dict, pkl_path=self.path_reg)
            else:
                self.reg = load_actree(pkl_path=self.path_reg)

        del self.wrong_word
        del si

    def main_match(self, query: str, need_correct=True):
        """

        :param query:   用户的原始查询
        :param need_correct:    是否需要纠错
        :return:    纠错、关系识别的结果

        语义解析模块只需要关注'query'字段的结果。
        """
        res = {
            "relation": [],
            "intent": None,
            "raw_query": query,
            "query": query,             # 如果有纠错之后的查询，则为纠错之后的查询，否则为原句
            "is_corr": need_correct,
            "correct_info": None
        }

        if need_correct:
            res["correct_info"] = self.correct(query)
            res["query"] = res["correct_info"]["correct_query"]

        for item in self.reg.query4type(res["query"]):  # 寻找query中的关系词、疑问词
            if item["type"] in self.relations.keys():
                item["code"] = self.relation_code[item["type"]]
                res["relation"].append(item)
            elif item["type"] in self.ques_word:
                if res["intent"] is not None and res["intent"] != item["type"]:
                    res["intent"] = 'conflict'  # 冲突
                else:
                    res["intent"] = item["type"]

        return res

    def correct(self, query, ban_list=None):
        """
        纠错函数，能够过滤账号识别的中的账号
        :param query:   原始查询
        :param ban_list: 应当屏蔽的位置
        :return:    纠错列表
        """
        start_time = time()
        res_correction = {"correct_query": query, "correct": []}

        query4type = self.corr.query4type(query.lower())
        if ban_list is not None:
            query4type = _resolve_list_confilct(query4type, ban_list)

        record = []
        # change the query to the lower.
        for item in query4type:
            item["value"] = query[item["begin"]: item["end"]]
            res_correction["correct"].append(item)
            record.append((item['begin'], item['end'], item['type']))

        res_correction["correct_query"] = replace_items_in_sentence(query, record)

        self.correct_logger.info(
            f"{construt_log(raw_query=query, correct_info=res_correction, using_time=time()-start_time)}")
        server_logger.info(f"Correcting the query time used: {time()-start_time}")
        return res_correction

    def match(self, query: str, need_correct=True):
        """
        :param query:   用户的原始查询
        :param need_correct:    是否需要纠错
        :return:    纠错、关系识别的结果

        语义解析模块只需要关注'query'字段的结果。
        """
        # 找出所有账号
        accounts_info = get_account_labels_info(query)
        res = {
            "relation": [],
            "intent": None,
            "raw_query": query,
            "query": query,             # 如果有纠错之后的查询，则为纠错之后的查询，否则为原句
            "is_corr": need_correct,
            "correct_info": None,
            "accounts": accounts_info["accounts"]
        }

        if need_correct:
            # 记录unlabel标签
            labelled_list = [(account['begin'], account['end']) for account in accounts_info["value"]
                             if account['type'] is not UNLABEL]
            correct_info = self.correct(query, labelled_list)   # 纠错
            res["correct_info"] = correct_info  # 赋值
            res["query"] = res["correct_info"]["correct_query"]

            res["accounts"] = \
                _resolve_list_confilct(res["accounts"], res["correct_info"]["correct"])
            _update_account_in_sentence(res["accounts"], res["query"])

        for item in self.reg.query4type(res["query"]):  # 寻找query中的关系词、疑问词
            if item["type"] in self.relations.keys():
                item["code"] = self.relation_code[item["type"]]
                res["relation"].append(item)
            elif item["type"] in self.ques_word:
                if res["intent"] is not None and res["intent"] != item["type"]:
                    res["intent"] = 'conflict'  # 冲突
                else:
                    res["intent"] = item["type"]

        return res


if __name__ == '__main__':
    from pprint import pprint
    i = "lailai的wxid_lainai是谁"
    im = ItemMatcher(new_actree=True, is_test=True)
    pprint(im.match(i))
    while True:
        i = input()
        pprint(im.match(i))
