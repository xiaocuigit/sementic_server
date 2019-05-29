from os.path import join, exists
from recognizer import Recognizer
import pickle
import yaml


class ItemMatcher:
    def __init__(self, new=False):
        self.reg = None
        self.dir_yml = join("yml")
        self.dir_data = join("data")
        self.path = join(self.dir_data, "reg.pkl")
        self.rel2id = yaml.load(open(join(self.dir_yml, "rel2id.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
        self.int2id = yaml.load(open(join(self.dir_yml, "int2id.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
        if exists(self.path) and not new:
            with open(self.path, "rb") as f:
                self.reg = pickle.load(f)
        else:
            relations = yaml.load(open(join(self.dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
            ques_word = yaml.load(open(join(self.dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
            wrong_word = yaml.load(open(join(self.dir_yml, "wrong_table.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
            concepts = relations
            concepts.update(ques_word)
            concepts.update(wrong_word)
            self.reg = Recognizer(concepts)
            pickle.dump(self.reg, open(self.path, "wb"))

    def matcher(self, q: str):
        res = {"relation": [], "intent": '0', "raw_query": q, "correct_query": None, "correct": []}
        for item in self.reg.query4type(q):
            if item["type"] in self.rel2id:
                item.update({"id": self.rel2id[item["type"]]})
                res["relation"].append(item)
            elif item["type"] in self.int2id:
                if res["intent"] != '0' and res["intent"] != self.int2id[item["type"]]:
                    res["intent"] = '1'  # 冲突
                else:
                    res["intent"] = self.int2id[item["type"]]

            else:
                res["correct"].append(item)
                res ["correct_query"] = q.replace(item["mention"], item["type"])
        return res


if __name__ == '__main__':
    from pprint import pprint
    im = ItemMatcher(True)
    r = im.matcher("张三的老婆是谁")
    pprint(r)
