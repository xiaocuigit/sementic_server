"""
@description: 匹配接口
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-05-29
@version: 0.0.1
"""


from os.path import join, exists
from os import mkdir
from sementic_server.source.intent_extraction.recognizer import Recognizer
from sementic_server.source.intent_extraction.system_info import SystemInfo
import pickle
import yaml
from sementic_server.source.intent_extraction.logger import construt_log, get_logger
import logging
from time import time


correct_logger = get_logger()
server_logger = logging.getLogger("server_log")


def load_actree(pkl_path):
    start = time()
    with open(pkl_path, "rb") as f:
        aho = pickle.load(f)
        logging.info(f"Loading AC-Tree \"{pkl_path.split('/')[-1]}\", time used: {time() - start}")
        return aho


def build_actree(dict_info, pkl_path):
    start = time()
    reg = Recognizer(dict_info)
    pickle.dump(reg, open(pkl_path, "wb"))
    logging.info(f"Building AC-Tree \"{pkl_path.split('/')[-1]}\", time used: {time() - start}")

    return reg


class ItemMatcher:
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

        # 获得根目录的地址
        self.dir_data = join(si.base_path, "data")
        self.dir_yml = join(self.dir_data, "yml")
        self.dir_pkl = join(self.dir_data, "pkl")

        # 获得关系词和疑问词的类型词典
        self.relations, self.ques_word, self.wrong_word = dict(), dict(), dict()
        try:
            self.relations = yaml.load(open(join(self.dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
            self.ques_word = yaml.load(open(join(self.dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
            self.wrong_word = yaml.load(open(join(self.dir_yml, "wrong_table.yml"), encoding="utf-8"),
                                        Loader=yaml.SafeLoader)
        except FileNotFoundError as e:
            logging.error(f"Cannot find the file in {self.dir_yml}, {e}")

        self.reg_dict = self.relations.copy()
        self.reg_dict.update(self.ques_word)

        # 纠错词典

        # actree
        if not exists(self.dir_pkl):
            mkdir(self.dir_pkl)
        self.path_corr = join(self.dir_pkl, "corr.pkl")
        self.path_reg = join(self.dir_pkl, "reg.pkl")
        self.corr = None
        self.reg = None

        try:
            if new_actree:
                self.corr = build_actree(dict_info=self.wrong_word, pkl_path=self.path_corr)
                self.reg = build_actree(dict_info=self.reg_dict, pkl_path=self.path_reg)
            elif not exists(self.path_corr):
                self.corr = build_actree(dict_info=self.wrong_word, pkl_path=self.path_corr)
            elif not exists(self.path_reg):
                self.reg = build_actree(dict_info=self.reg_dict, pkl_path=self.path_reg)
            else:
                self.corr = load_actree(pkl_path=self.path_corr)
                self.reg = load_actree(pkl_path=self.path_reg)
        except Exception as e:
            logging.error(f"Building or Loading AC-Tree failed. {e}")

        del self.wrong_word

    def correct(self, q: str):
        """
        纠错函数
        :param q:   原始查询
        :return:    纠错列表
        """
        start_time = time()
        res_corr = {"correct_query": q, "correct": []}
        record = []
        for item in self.corr.query4type(q):
            res_corr["correct"].append(item)
            record.append((item['begin'], item['end'], item['type']))

        cq = ""
        sz = len(record)
        if sz > 0:
            p = 0
            cursor = (record[p][0], record[p][1])   # 指针指向第一个begin, end
            for i, c in enumerate(q):
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
                    cq += c
            res_corr['correct_query'] = cq

        correct_logger.info(f"{construt_log(raw_query=q, correct_info=res_corr, using_time=time()-start_time)}")
        logging.info(f"Correcting the query time used: {time()-start_time}")
        return res_corr

    def match(self, q: str, need_correct=True):
        """

        :param q:   用户的原始查询
        :param need_correct:    是否需要纠错
        :return:    纠错、关系识别的结果

        语义解析模块只需要关注'query'字段的结果。
        """
        res = {"relation": [], "intent": '0', "raw_query": q, "query": q, "is_corr": need_correct, "correct_info": None}
        if need_correct:
            res["correct_info"] = self.correct(q)
            res["query"] = res["correct_info"]["correct_query"]

        for item in self.reg.query4type(res["query"]):  # 寻找query中的关系词、疑问词
            if item["type"] in self.relations.keys():
                res["relation"].append(item)
            elif item["type"] in self.ques_word:
                if res["intent"] != '0' and res["intent"] != item["type"]:
                    res["intent"] = '1'  # 冲突
                else:
                    res["intent"] = item["type"]

        return res


if __name__ == '__main__':
    from pprint import pprint
    from time import time
    im = ItemMatcher(new_actree=True, is_test=True)
    r = im.match("张三的爸爸祖父的naopoo的是谁")
    pprint(r)
    while 1:
        i = input()
        s = time()
        pprint(im.match(i))
        print(time() - s)
