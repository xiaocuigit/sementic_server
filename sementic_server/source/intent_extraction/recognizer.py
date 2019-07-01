"""
@description: 实现关系、疑问词的识别
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-05-29
@version: 0.0.1
"""
from sementic_server.source.intent_extraction.actree import Aho
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
        word2type.update({vi: k for vi in v if vi is not None})

        for vi in v:
            if vi is not None:
                for vii in vi:
                    char_pool.add(vii)

    char_pool = list(char_pool)
    char2id = {c: i+1 for i, c in enumerate(char_pool)}
    id2char = {i+1: c for i, c in enumerate(char_pool)}

    return word2type, char2id, id2char


def word2id(c2id: dict, word: str):
    """
    将一个词用词典c2id组织成列表的形式

    :param c2id: 字符->id的词典
    :param word: 输入的单词
    :return:    输入单词对应的字符索引列表
    """
    word_id = list()

    for i, c in enumerate(word):
        if c in c2id:
            word_id.append(c2id[c])
        else:
            word_id.append(0)
    return word_id


def id2word(id2c: dict, ids: list):
    """
    将一个字符索引列表组织成单词

    :param id2c: id->字符的词典
    :param ids:  输入的字符索引列表
    :return:     字符列表对应的单词
    """
    word = ""
    for i in ids:
        if i in id2c:
            word += id2c[i]
        else:
            return ""
    return word


def cmp(x, y):
    """
    比较函数
    :param x:数1
    :param y:数2
    :return:
    """
    if x[1] < y[1]:
        return -1
    elif x[1] > y[1]:
        return 1
    if x[2] > y[2]:
        return -1
    else:
        return 1


def _find_word_range_in_sentence(word, query, words_info):
    """
    在query查找word的位置信息
    :param word:
    :param query:
    :param words_info:
    :return:
    """
    index = 0
    while index != -1:
        index = query.find(word, index)
        if index != -1:
            words_info.append((index, index + len(word) - 1, word))
            index += 1


class Recognizer(object):
    """
    @description: 实现关系、疑问词的识别
    @author: Wu Jiang-Heng
    @email: jiangh_wu@163.com
    @time: 2019-05-29
    @version: 0.0.1
    """
    def __init__(self, vocab: dict):
        """
        利用词典建树
        :param vocab:
        """
        self.w2tp, self.c2id, self.id2c = build_vocab(vocab)
        self.actree = Aho()
        for vls in vocab.values():
            for vl in vls:
                if vl is not None:
                    self.actree.insert(word2id(self.c2id, vl))
        self.actree.build()

    def query(self, q: str):
        """
        利用AC自动机查询q中包含的词典词汇
        :param q:
        :return:
        """
        q2id = word2id(self.c2id, q)
        match_node = self.actree.match(q2id)
        res_word_id = self.actree.parse(match_node)
        return [id2word(self.id2c, rwi) for rwi in res_word_id]

    def query4type(self, query: str):
        """
        将词典词汇和其类型对应
        :param query: 查询词汇
        :return:
        """
        words = self.query(query)
        words_info = list()
        res = list()

        # find positions of words
        for word in words:
            _find_word_range_in_sentence(word, query, words_info)

        words_info = sorted(words_info, key=cmp_to_key(cmp))

        # 是否有重叠的关键词
        last_end = -1   # 记录上一个关键词结束的位置
        for i, t in enumerate(words_info):
            if t[0] <= last_end:     # 如果本关键词开始的位置位于上个关键词内，则跳过此关键词
                continue
            ok = True
            for j in range(i - 1, -1, -1):
                if t[1] <= words_info[j][1]:
                    ok = False
                    break
            if ok:
                last_end = t[1]
                res.append({
                    "type": self.w2tp.get(t[2], "NIL"),
                    "value": t[2],
                    "begin": t[0],
                    "end":  t[1] + 1
                })

        return res





