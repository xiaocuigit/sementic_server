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
from sementic_server.source.intent_extraction.item_matcher import replace_items_in_sentence
import logging
logger = logging.getLogger("server_log")


def power_set(l: list):
    """
    生成 0~l的幂集
    :param l:  某个词的长度

    """
    res = [[]]
    for i in l:
        sz = len(res)
        for j in range(sz):
            tmp = res[j].copy()
            tmp.append(i)
            res.append(tmp)
    return res


def _replace_position_with_another_by_combination(word, another, combination):
    w = ""
    for i in range(len(word)):
        if i in combination:
            w += another[i]
        else:
            w += word[i]

    return w


def _find_the_key_and_add_to_candidate(word, key, value, pos_list: list):
    if key not in word:
        return
    i, b, e = word.find(key), 0, len(word)

    while i > -1:
        pos_list.extend([(i, i + len(key), v) for v in value])
        # find the key word
        i = word.find(key, i + 1, e)


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

    n = len(word)
    range_n = list(range(n))
    # 拼音替换
    combinations = power_set(range_n)[1:]
    word_py = lazy_pinyin(word)

    for combination in combinations:
        # for each combination
        # 拼音
        word_change = _replace_position_with_another_by_combination(word, word_py, combination)
        res.append(word_change)

        # other wrong
        pos_list = []
        for key, value in replace["pinyin"].items():
            _find_the_key_and_add_to_candidate(word_change, key, value, pos_list)


        pos_list = sorted(pos_list, key=cmp_to_key(cmp))
        pos_list = power_set(pos_list)[1:]

        for pos_item in pos_list:
            word_change_ex = replace_items_in_sentence(word_change, pos_item)
            res.append(word_change_ex)
    return res


def build_wrong_table(is_test=False):
    """
    构建纠错词库
    :param is_test:  是否测试模式
    """
    si = SystemInfo(is_test)
    dir_yml = join(si.base_path, "data", "yml")
    _int = yaml.load(open(join(dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    _rel = yaml.load(open(join(dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    all_word = [v for vs in list(_rel.values()) + list(_int.values()) for v in vs if v is not None and len(v) > 1]
    repl = yaml.load(open(join(dir_yml, "replace.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)

    # 运行
    res_dict = {}
    for aw in all_word:
        res_dict[aw] = transformer(aw, repl)

    # 去重
    all_res = []
    for v in res_dict.values():
        all_res.extend(v)

    c = Counter(all_res)
    c = {i for i in c.keys() if c[i] > 1}

    conflict = 0
    for k, v in res_dict.items():
        x = c & set(v)
        conflict += len(x)
        for xi in x:
            res_dict[k].remove(xi)

    logger.info(f"Build correct table - conflict count: {conflict}")

    path_restable = join(dir_yml, "wrong_table.yml")
    yaml.dump(res_dict, open(path_restable, "w", encoding="utf-8"), allow_unicode=True, default_flow_style=False)


if __name__ == '__main__':
    build_wrong_table(is_test=True)
    si = SystemInfo(True)
    dir_yml = join(si.base_path, "data", "yml")
    rep = yaml.load(open(join(dir_yml, "replace.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
