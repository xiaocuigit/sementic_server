"""
    实现意图、关系的识别
"""
from actree import Aho
from functools import cmp_to_key


def build_vocab(vo_dict: dict):
    """
        将原始json转换为词典
        三个词典，分别是：
        - 疑问词->type
        - 词->id
        - id->词
    """
    word2type = dict()
    char_pool = set()
    for k, v in vo_dict.items():
        word2type.update({vi: k for vi in v})
        char_pool.update({vii for vi in v for vii in vi})
    
    char_pool = list(char_pool)
    char2id = {c: i+1 for i, c in enumerate(char_pool)}
    id2char = {i+1: c for i, c in enumerate(char_pool)}

    return word2type, char2id, id2char


def word2id(c2id: dict, word: str):
    word_id = list()

    for i, c in enumerate(word):
        if c in c2id:
            word_id.append(c2id[c])
        else:
            word_id.append(0)
    return word_id


def id2word(id2c: dict, ids: list):
    word = ""
    for i in ids:
        if i in id2c:
            word += id2c[i]
        else:
            word += "---"
    return word


class Recognizer:
    def __init__(self, vocab: dict):
        # 建树
        self.w2tp, self.c2id, self.id2c = build_vocab(vocab)
        self.actree = Aho()
        for vls in vocab.values():
            for vl in vls:
                self.actree.insert(word2id(self.c2id, vl))
        self.actree.build()

    def query(self, q: str):
        q2id = word2id(self.c2id, q)
        match_node = self.actree.match(q2id)
        res_word_id = self.actree.parse(match_node)
        return [id2word(self.id2c, rwi) for rwi in res_word_id]

    def query4type(self, q: str):
        words = self.query(q)
        w_os = list()
        res = list()
        for w in words:
            i = 0
            while i != -1:
                i = q.find(w, i)
                if i != -1:
                    w_os.append((w, i, i + len(w) - 1))
                    i += 1

        def cmp(x, y):
            if x[1] < y[1]:
                return -1
            elif x[1] > y[1]:
                return 1
            else:
                if x[2] > y[2]:
                    return -1
                else:
                    return 1

        w_os = sorted(w_os, key=cmp_to_key(cmp))

        for i, t in enumerate(w_os):
            ok = True
            for j in range(i - 1, -1, -1):
                if t[2] <= w_os[j][2]:
                    ok = False
                    break
            if ok:
                res.append({
                    "type": self.w2tp.get(t[0], "NIL"),
                    "mention": t[0],
                    "offset": t[1],
                })

        return res





