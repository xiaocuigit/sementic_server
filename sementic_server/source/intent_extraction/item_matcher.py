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
from sementic_server.source.intent_extraction.recognizer import Recognizer
from sementic_server.source.intent_extraction.system_info import SystemInfo
from sementic_server.source.intent_extraction.dict_builder import build_wrong_table
from sementic_server.source.intent_extraction.logger import construt_log, get_logger
from sementic_server.source.intent_extraction.helper \
    import replace_items_in_sentence, resolve_list_confilct, update_account_in_sentence

server_logger = logging.getLogger("server_log")
UNLABEL = 'UNLABEL'


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


class ItemMatcher(object):
    """
    @description: 匹配接口类
    @author: Wu Jiang-Heng
    @email: jiangh_wu@163.com
    @time: 2019-05-29
    @version: 0.0.1
    """

    def __init__(self, new_actree=False):
        self.aho_recognizer = None  # 识别AC
        self.aho_correction = None  # 纠错AC
        si = SystemInfo()
        self.correct_logger = get_logger("correction", si.log_path_corr)

        # 获得根目录的地址
        dir_data = join(si.base_path, "data")
        dir_yml = join(dir_data, "yml")

        dir_output = join(si.base_path, "output")
        dir_pkl = join(dir_output, "pkl")

        # 获得关系词和疑问词的类型词典和纠错词典
        self.relations, self.relation_code, self.ques_word, wrong_word, validation = \
            dict(), dict(), dict(), dict(), dict()
        try:
            self.relations = yaml.load(open(join(dir_yml, "relation.yml"),
                                            encoding="utf-8"), Loader=yaml.SafeLoader)
            self.relation_code = yaml.load(open(join(dir_yml, "relation_code.yml"),
                                                encoding="utf-8"), Loader=yaml.SafeLoader)
            self.ques_word = yaml.load(open(join(dir_yml, "quesword.yml"),
                                            encoding="utf-8"), Loader=yaml.SafeLoader)
            wrong_word = yaml.load(open(join(dir_yml, "wrong_table.yml"),
                                             encoding="utf-8"), Loader=yaml.SafeLoader)
            validation = yaml.load(open(join(dir_yml, "intent_validation.yml"),
                                             encoding="utf-8"), Loader=yaml.SafeLoader)
        except FileNotFoundError as e:
            server_logger.error(f"Cannot find the file in {dir_yml}, {e}")

        all_kv_pair = self.relations.copy()
        all_kv_pair.update(self.ques_word)
        all_values = {value for values in all_kv_pair.values() for value in values}

        if validation is None:
            is_valid = False
        else:
            is_valid = all_values == set(validation)

        if not is_valid:
            build_wrong_table()
            yaml.dump(
                list(all_values),
                open(join(dir_yml, "intent_validation.yml"), "w", encoding="utf-8"),
                allow_unicode=True,
                default_flow_style=False
            )

        if not exists(dir_pkl):
            mkdir(dir_pkl)
        path_corr = join(dir_pkl, "corr.pkl")
        path_reg = join(dir_pkl, "reg.pkl")

        if new_actree:
            self.aho_correction = build_actree(dict_info=wrong_word, pkl_path=path_corr)
            self.aho_recognizer = build_actree(dict_info=all_kv_pair, pkl_path=path_reg)
        else:
            if not exists(path_corr) or not is_valid:
                self.aho_correction = build_actree(dict_info=wrong_word, pkl_path=path_corr)
            else:
                self.aho_correction = load_actree(pkl_path=path_reg)

            if not exists(path_reg):
                self.aho_recognizer = build_actree(dict_info=all_kv_pair, pkl_path=path_reg)
            else:
                self.aho_recognizer = load_actree(pkl_path=path_reg)

    def correct(self, query, ban_list=None):
        """
        纠错函数，能够过滤账号识别的中的账号
        :param query:   原始查询
        :param ban_list: 应当屏蔽的位置
        :return:    纠错列表
        """
        start_time = time()
        res_correction = {"correct_query": query, "correct": []}

        query4type = self.aho_correction.query4type(query.lower())

        # 处理与账号识别冲突的部分
        if ban_list is not None:
            query4type = resolve_list_confilct(query4type, ban_list)

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

    def match(self, query: str, need_correct=True, accounts_info=None):
        """
        :param query:   用户的原始查询
        :param need_correct:    是否需要纠错
        :return:    纠错、关系识别的结果
        :param accounts_info:

        语义解析模块只需要关注'query'字段的结果。
        """
        # 找出所有账号
        accounts_info = accounts_info if accounts_info is not None else {}
        accounts = accounts_info.get("accounts", [])
        res = {
            "relation": [],
            "intent": None,
            "raw_query": query,
            "query": query,  # 如果有纠错之后的查询，则为纠错之后的查询，否则为原句
            "is_corr": need_correct,
            "correct_info": None,
            "accounts": accounts
        }

        if need_correct:
            # 记录unlabel标签

            labelled_list = [(account['begin'], account['end']) for account in accounts
                             if account['type'] is not UNLABEL]
            correct_info = self.correct(query, labelled_list)  # 纠错
            res["correct_info"] = correct_info  # 赋值
            res["query"] = res["correct_info"]["correct_query"]

            res["accounts"] = \
                resolve_list_confilct(res["accounts"], res["correct_info"]["correct"])
            update_account_in_sentence(res["accounts"], res["query"])

        for item in self.aho_recognizer.query4type(res["query"]):  # 寻找query中的关系词、疑问词
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

    i = "住在陕西省汉中市市辖区的QQ号码1170591840的人的fuqin是谁？"
    from sementic_server.source.ner_task.account import Account

    account = Account()
    im = ItemMatcher(new_actree=True)

    pprint(im.match(i, accounts_info=account.get_account_labels_info(i)))
    while True:
        i = input()
        pprint(im.match(i))
