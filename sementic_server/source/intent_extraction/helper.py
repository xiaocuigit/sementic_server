"""
@description: 一些必要的辅助函数
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-07-18
@version: 0.0.1
"""


def replace_items_in_sentence(sentence, items):
    """
    替换句子在item中出现的元素
    :param sentence: 原始句子
    :param items: 需要替换的item ((begin, end, value),())
    :return:
    """
    size = len(items)
    if size < 1:
        return sentence
    sentence_after_replace = ""
    index = 0
    for position, char in enumerate(sentence):
        if position is items[index][0]:
            sentence_after_replace += items[index][2]
        elif position not in range(items[index][0] + 1, items[index][1]):
            sentence_after_replace += char

        if position is items[index][1] - 1 and index < size - 1:
            index += 1

    return sentence_after_replace


def resolve_list_confilct(raw_list, ban_list):
    """
    消解raw_list和ban_list的冲突
    :param raw_list: 需要被消解冲突的部分
    :param ban_list: 禁止出现的位置索引
    :return:
    """
    if ban_list == list():
        return raw_list

    res_list = []
    index_ban = set()
    for ban in ban_list:
        if type(ban) in {list, tuple}:
            index_ban.update(list(range(ban[0], ban[1])))
        else:
            index_ban.update(list(range(ban["begin"], ban["end"])))

    for item in raw_list:
        if type(item) in {list, tuple}:
            item_range = list(range(item[0], item[1]))
        else:
            item_range = list(range(item["begin"], item["end"]))
        if index_ban.intersection(item_range) == set():
            res_list.append(item)
    return res_list


def update_account_in_sentence(accounts: list, sentence: str):
    """
    更新账号在句子中的位置
    :param accounts:
    :param sentence:
    :return:
    """
    for index, info in enumerate(accounts):
        begin = sentence.find(info["value"])
        if begin is not info["begin"]:
            accounts[index]["begin"] = begin
            accounts[index]["end"] = begin + len(info["value"])


def power_set(l: list):
    """
    生成列表l的幂集
    :param l:一个列表
    """
    res = [[]]
    for i in l:
        sz = len(res)
        for j in range(sz):
            tmp = res[j].copy()
            tmp.append(i)
            res.append(tmp)
    return res


def replace_position_with_another_by_combination(word, another, combination):
    """
    根据组合更改位置上的值
    :param word:目标词
    :param another:更改的词
    :param combination:位置组合
    :return:替换后的新词
    """
    w = ""
    for i in range(len(word)):
        if i in combination:
            w += another[i]
        else:
            w += word[i]

    return w
