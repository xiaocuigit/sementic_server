"""
@description: 构建纠错词典
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-05-29
@version: 0.0.1
"""

from os.path import join
import yaml
from pypinyin import lazy_pinyin
from collections import Counter
from sementic_server.source.intent_extraction.system_info import SystemInfo
from sementic_server.source.intent_extraction.recognizer import cmp, cmp_to_key
from sementic_server.source.intent_extraction.helper \
    import replace_items_in_sentence, power_set, replace_position_with_another_by_combination
import logging
logger = logging.getLogger("server_log")

PINYIN_CAUTION = {
    "en": "eng",
    "in": "ing",
    "on": "ong",
    }


def find_the_key_and_add_to_candidate(word, key, value, pos_list: list):
    """
    在word中查找key的位置并加入到pos_list中
    :param word:
    :param key:
    :param value:
    :param pos_list:
    :return:无
    """

    i = word.find(key)
    if i < 0:
        return
    caution = False
    if key in PINYIN_CAUTION.keys():
        caution = True
    size = len(word)

    while i > -1:
        if caution and word.find(PINYIN_CAUTION[key], i, size) is i:
            ...
        else:
            pos_list.extend([(i, i + len(key), v) for v in value])
        # find the next key word
        i = word.find(key, i + 1, size)


# 规则库
def transformer(word: str, replace: dict):
    """
    纠错词库生成规则
    :param word:  某个词
    :param replace:  替换规则

    """
    res = list()

    outer = {chr(i) for i in range(ord("a"), ord("z") + 1)}
    outer.update(list(range(10)))

    # 包含英文的都舍弃
    if set(word.lower()) & outer != set():
        return res

    range_n = [i for i in range(len(word))]

    combinations = power_set(range_n)
    word_py = lazy_pinyin(word)

    for combination in combinations:
        # for each combination
        # 考虑每一种组合的拼音替代方案
        word_change = replace_position_with_another_by_combination(word, word_py, combination)
        res.append(word_change)

        # 在可替换词典列表中寻找可替代字符
        pos_list = []
        for key, value in replace.items():
            find_the_key_and_add_to_candidate(word_change, key, value, pos_list)

        pos_list = sorted(pos_list, key=cmp_to_key(cmp))
        pos_list = power_set(pos_list)[1:]

        for pos_item in pos_list:
            word_change_ex = replace_items_in_sentence(word_change, pos_item)
            res.append(word_change_ex)

    res.remove(word) if word in res else None
    return res


def build_wrong_table():
    """
    构建纠错词库
    """
    si = SystemInfo()
    dir_yml = join(si.base_path, "data", "yml")
    _int = yaml.load(open(join(dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    _rel = yaml.load(open(join(dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    all_words = [v for vs in list(_rel.values()) + list(_int.values()) for v in vs if v is not None and len(v) > 1]
    replace = yaml.load(open(join(dir_yml, "replace.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)

    # 运行
    wrong_table = {}
    for word in all_words:
        wrong_table[word] = transformer(word, replace)

    # 去重
    all_res = []
    for v in wrong_table.values():
        all_res.extend(v)

    c = Counter(all_res)
    c = {i for i in c.keys() if c[i] > 1}

    for k, v in wrong_table.items():
        x = c & set(v)
        for xi in x:
            wrong_table[k].remove(xi)

    logger.info(f"Building correction table....")

    path_restable = join(dir_yml, "wrong_table.yml")
    yaml.dump(wrong_table, open(path_restable, "w", encoding="utf-8"), allow_unicode=True, default_flow_style=False)


if __name__ == '__main__':
    build_wrong_table()
