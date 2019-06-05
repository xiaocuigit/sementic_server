"""
@description: 匹配接口
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-05-29
@version: 0.0.1
"""


from os.path import join, exists, abspath
from os import getcwd
from sementic_server.source.intent_extraction.recognizer import Recognizer
import pickle
import yaml


class ItemMatcher:
    """
    @description: 匹配接口类
    @author: Wu Jiang-Heng
    @email: jiangh_wu@163.com
    @time: 2019-05-29
    @version: 0.0.1
    """
    def __init__(self, new=False):
        self.reg = None     # 识别AC
        self.corr = None    # 纠错AC

        # 获得根目录的地址
        self.dir_yml = join(abspath(getcwd()), "..", "..", "data", "yml")
        self.dir_data = join(abspath(getcwd()), "..", "..", "data", "pkl")

        # 获得关系词和疑问词的类型词典
        self.relations = yaml.load(open(join(self.dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
        self.ques_word = yaml.load(open(join(self.dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)

        # 构建纠错AC
        self.path_corr = join(self.dir_data, "corr.pkl")
        if exists(self.path_corr) and not new:
            with open(self.path_reg, "rb") as f:
                self.reg = pickle.load(f)
        else:
            wrong_word = yaml.load(open(join(self.dir_yml, "wrong_table.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
            self.corr = Recognizer(wrong_word)
            pickle.dump(self.corr, open(self.path_corr, "wb"))

        # 构建识别AC
        self.path_reg = join(self.dir_data, "reg.pkl")
        if exists(self.path_reg) and not new:
            with open(self.path_reg, "rb") as f:
                self.reg = pickle.load(f)
        else:
            concepts = self.relations.copy()
            concepts.update(self.ques_word)
            self.reg = Recognizer(concepts)
            pickle.dump(self.reg, open(self.path_reg, "wb"))

    def _correct(self, q: str):
        """
        纠错函数
        :param q:   原始查询
        :return:    纠错列表
        """
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
                    pass
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
        return res_corr

    def match(self, q: str, need_correct=True):
        res = {"relation": [], "intent": '0', "raw_query": q, "query": q, "is_corr": need_correct, "correct_info": None}
        if need_correct:
            res["correct_info"] = self._correct(q)
            res["query"] = res["correct_info"]["correct_query"]

        for item in self.reg.query4type(res["query"]):
            if item["type"] in self.relations.keys():
                res["relation"].append(item)
            elif item["type"] in self.ques_word:
                if res["intent"] != '0' and res["intent"] != item["type"]:
                    res["intent"] = '1'  # 冲突
                else:
                    res["intent"] = item["type"]

        return res

    def matcher(self, q: str):
        res = {"relation": [], "intent": '0', "raw_query": q}
        for item in self.reg.query4type(q):
            if item["type"] in self.relations.keys():
                res["relation"].append(item)
            elif item["type"] in self.ques_word:
                if res["intent"] != '0' and res["intent"] != item["type"]:
                    res["intent"] = '1'  # 冲突
                else:
                    res["intent"] = item["type"]

            else:
                res["correct"].append(item)
                res["correct_query"] = q.replace(item["value"], item["type"])
        return res


if __name__ == '__main__':
    from pprint import pprint
    im = ItemMatcher(True)
    r = im.match("张三的爸爸祖父的fuqingfuqin的是谁")
    pprint(r)
