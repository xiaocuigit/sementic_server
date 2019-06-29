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

    def correct(self, query: str):
        """
        纠错函数
        :param query:   原始查询
        :return:    纠错列表
        """
        start_time = time()
        res_corr = {"correct_query": query, "correct": []}
        record = []
        # change the query to the lower.
        for item in self.corr.query4type(query.lower()):
            item["value"] = query[item["begin"]: item["end"]]
            res_corr["correct"].append(item)
            record.append((item['begin'], item['end'], item['type']))

        cq = ""
        sz = len(record)
        if sz > 0:
            p = 0
            cursor = (record[p][0], record[p][1])   # 指针指向第一个begin, end
            for i, c in enumerate(query):
                if cursor[0] < i < cursor[1] - 1:
                    ...
                elif i == cursor[0]:
                    cq += record[p][2]
                elif i == cursor[1] - 1:    # 更新游标指向
                    if p == sz - 1:         # 如果没有纠错项目
                        cursor = (-1, -1)
                    else:
                        p += 1
                        cursor = (record[p][0], record[p][1])
                else:
                    cq += c  # 加上原句中的字符
            res_corr['correct_query'] = cq

        self.correct_logger.info(f"{construt_log(raw_query=query, correct_info=res_corr, using_time=time()-start_time)}")
        server_logger.info(f"Correcting the query time used: {time()-start_time}")
        return res_corr

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

    def correct_with_filter(self, query, ban_list):
        """
        纠错函数，能够过滤账号识别的中的账号
        :param query:   原始查询
        :param ban_list: 应当屏蔽的位置
        :return:    纠错列表
        """
        start_time = time()
        res_corr = {"correct_query": query, "correct": []}
        record = []
        # change the query to the lower.
        for item in self.corr.query4type(query.lower()):
            item["value"] = query[item["begin"]: item["end"]]
            res_corr["correct"].append(item)
            record.append((item['begin'], item['end'], item['type']))



        self.correct_logger.info(f"{construt_log(raw_query=query, correct_info=res_corr, using_time=time()-start_time)}")
        server_logger.info(f"Correcting the query time used: {time()-start_time}")
        return res_corr

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
            "account": accounts_info
        }

        if need_correct:
            # 记录unlabel标签
            labelled_list = []
            for account in accounts_info["accounts"]:
                if account['account_label'] is not UNLABEL:
                    labelled_list.append((account['begin'], account['end']))

            self.correct_with_filter(query, labelled_list)




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


if __name__ == '__main__':
    i = "张三的奶奶是lailai"
    from pprint import pprint
    im = ItemMatcher(new_actree=True, is_test=True)

    # r = im.match(i)
    # pprint(r)
    # while 1:
    #     i = input()
    #     pprint(im.match(i))
    #     get_account_labels_info(i)
