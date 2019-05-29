"""
@description: 构建纠错词典
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-05-29
@version: 0.0.1
"""

from os.path import join, abspath
from os import getcwd, listdir
import yaml
from pypinyin import lazy_pinyin
from collections import Counter


dir_yml = join(abspath(getcwd()), "..", "..", "data", "yml")
print(listdir(dir_yml))

_int = yaml.load(open(join(dir_yml, "quesword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
repl = yaml.load(open(join(dir_yml, "replace.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)


def build_wrong_table():
    path_restable = join(dir_yml, "wrong_table.yml")
    _rel = yaml.load(open(join(dir_yml, "relation.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
    all_word = [v for vs in list(_rel.values()) + list(_int.values()) for v in vs if len(v) > 1]

    def power_set(n):
        res = [[]]
        b, e, c = 0, 1, 0
        while b < e:
            x = 0
            if not res[b] == []:
                x = res[b][-1] + 1
            for i in range(x, n):
                c += 1
                tmp = res[b].copy()
                tmp.append(i)
                res.append(tmp)

            b += 1
            e += c
            c = 0
        return res


    # 规则库
    def transformer(word):
        res = list()

        n = len(word)
        # 规则1 拼音替换

        def rep(wd, py, l):
            r = ""
            for i in range(len(word)):
                if i in l:
                    r += py[i]
                else:
                    r += wd[i]

            return r

        pset = power_set(n)[1: ]
        word_py = lazy_pinyin(word)

        for l in pset:
            w = rep(word, word_py, l)
            res.append(w)

            for kre, vre in repl["pinyin"].items():
                if kre in w:
                    for v in vre:
                        res.append(w.replace(kre, v))
        return res


    # 运行
    res_dict = {}
    for aw in all_word:
        res_dict[aw] = transformer(aw)

    # 去重
    all_res = []
    for v in res_dict.values():
        all_res.extend(v)

    c = Counter(all_res)
    c = {i for i in c.keys() if c[i] > 1}

    for k, v in res_dict.items():
        x = c & set(v)
        for xi in x:
            res_dict[k].remove(xi)

    yaml.dump(res_dict, open(path_restable, "w", encoding="utf-8"), allow_unicode=True)


if __name__ == '__main__':
    # build_wrong_table()
    pass