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
import logging
logger = logging.getLogger("server_log")


def power_set(l):
    res = [[]]
    for i in l:
        sz = len(res)
        for j in range(sz):
            tmp = res[j].copy()
            tmp.append(i)
            res.append(tmp)
    return res


# 规则库
def transformer(word:str, repl):
    res = list()

    outer = {chr(i) for i in range(ord("a"), ord("z") + 1)}
    outer.update(list(range(10)))

    # 包含英文的都舍弃
    if set(word.lower()) & outer != set():
        return res

    n = len(word)
    # 拼音替换
    pset = power_set(list(range(n)))[1:]
    word_py = lazy_pinyin(word)

    for l in pset:
        # for each combination
        # pinyin
        w = ""
        for i in range(len(word)):
            if i in l:
                try:
                    w += word_py[i]
                except IndexError as e:
                    logger.error(f"dict_builder , {e}")
            else:
                w += word[i]
        res.append(w)

        # other wrong
        pos_list = []
        for kre, vre in repl["pinyin"].items():
            if kre in w:
                for v in vre:
                    i, b, e = w.find(kre), 0, len(w)

                    while i > -1:
                        pos_list.append((v, i, i+len(kre)))
                        # find the key word
                        i = w.find(kre, i + 1, e)

        pos_list = sorted(pos_list, key=cmp_to_key(cmp))
        pos_list = power_set(pos_list)[1:]

        for pl in pos_list:
            sz = len(pl)
            ix, b, e = 0, pl[0][1], pl[0][2]

            w_mod = ""
            for p, c in enumerate(w):
                if p not in range(b, e):
                    w_mod += w[p]
                else:
                    if p == b:
                        w_mod += pl[ix][0]

                    if p == e - 1:
                        # update
                        ix = ix + 1
                        if ix == sz:
                            b = e = -1
                        else:
                            b, e = pl[ix][1], pl[ix][2]

            res.append(w_mod)
    return res


def build_wrong_table(is_test=False):
    si = SystemInfo(is_test)
    dir_yml = join(si.base_path, "data", "yml")
    _int = yaml.load(open(join(dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    _rel = yaml.load(open(join(dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    all_word = [v for vs in list(_rel.values()) + list(_int.values()) for v in vs if len(v) > 1]
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
    yaml.dump(res_dict, open(path_restable, "w", encoding="utf-8"), allow_unicode=True)


if __name__ == '__main__':
    build_wrong_table(is_test=True)
