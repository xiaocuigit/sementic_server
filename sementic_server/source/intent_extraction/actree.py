"""
    @description: Ac自动机的实现
    @author: Wu Jiang-Heng
    @email: jiangh_wu@163.com
    @time: 2019-05-29
    @version: 0.0.1
"""

from queue import Queue


def _build(q, st):
    """
    :param q:队列
    :param st:状态树
    :return:
    """
    u = q.get()

    for i, x in st[u].next.items():  # 为当前结点的孩子结点x构建fail指针
        if x <= 0:
            continue
        if u == 0:
            """
                根节点的孩子结点的fail都为根节点
            """
            st[st[u].next[i]].fail = 0
        """
            取出当前结点的fail指针指向结点v，如果v存在边上为i的孩子结点，那么fail指向v
            否则 v = v.fail
        """
        v = st[u].fail
        while v > -1:
            if st[v].next.get(i, 0) > 0:
                st[st[u].next[i]].fail = st[v].next[i]
                break
            v = st[v].fail

        if v == -1:
            st[st[u].next[i]].fail = 0
        q.put(st[u].next[i])


def _match(i, now, s, st, res_set):
    """
    just for sonar
    :param i:
    :param now:
    :param s:
    :param st:
    :param res_set:
    :return:
    """
    if st[now].next.get(s[i], 0) > 0:
        now = st[now].next[s[i]]
    else:
        f = st[now].fail
        while f != -1 and st[f].next.get(s[i], 0) == 0:
            f = st[f].fail
        if f == -1:
            now = 0
        else:
            now = st[f].next.get(s[i], 0)
    if st[now].cnt:
        # 将树上的结束结点加入到结果集合中
        res_set.add(now)

    return now


class State(object):
    """
        @description: AC自动机的结点类
        @author: Wu Jiang-Heng
        @email: jiangh_wu@163.com
        @time: 2019-05-29
        @version: 0.0.1
    """
    def __init__(self):
        self.next = dict()      # 下一个结点的序号列表，用dict实现
        self.pre = -1       # 上一个结点的序号
        self.s_pre = -1     # 回溯到上一个结点对应的字符
        self.fail = 0       # 此结点的失配指针
        self.cnt = 0        # 是否有词在此结点结束


class Aho(object):
    """
        @description: Ac自动机
        @author: Wu Jiang-Heng
        @email: jiangh_wu@163.com
        @time: 2019-05-29
        @version: 0.0.1
    """
    def __init__(self):
        # 初始化所有值
        self.size = 1                   # 记录AC自动机结点个数
        self.state_table = dict()       # AC自动机结点数组，用dict实现
        self.state_table[0] = State()   # 初始化首结点

    def insert(self, s: list):
        """
            构建trie树
            输入代表了词典中的 某个词 的 字符列表。
        """
        st = self.state_table
        sz = len(s)
        now = 0     # 当前的游标：指向某个结点

        for i in range(sz):
            if s[i] not in st[now].next:        # 如果游标指向的结点没有孩子结点s[i]
                st[now].next[s[i]] = self.size  # 将游标指向的结点孩子列表中加入s[i]
                self.size += 1
            tmp = now                           # 利用临时标量记住游标
            now = st[now].next[s[i]]            # 更新游标结点
            st[now] = st.get(now, State())
            st[now].pre = tmp                   # 将更新后的游标结点的父指针指向之前的结点
            st[now].s_pre = s[i]                # 将更新后的游标结点指向父指针的边记录

        st[now].cnt += 1                        # 有字符串在当前游标结点结束，记录

    def build(self):
        """
            利用广度优先搜索，构建AC自动机的失配指针
        """
        st = self.state_table
        q = Queue()         # 广度优先搜索的队列
        st[0].fail = -1     # 根节点的失配指针置空
        q.put(0)

        while not q.empty():
            _build(q, st)

    def match(self, s: list):
        """
            利用AC自动机搜索当前串
        """
        st = self.state_table
        n = len(s)
        res_set = set()
        now = 0         # 游标指针

        # 对目标串遍历
        for i in range(n):
            now = _match(i, now, s, st, res_set)

        return res_set

    def parse(self, res_set: set):
        """
            解析答案
        """
        st = self.state_table
        res_ids = list()    # list of list

        for r in list(res_set):
            list_id = list()
            while r > 0:
                list_id.append(st[r].s_pre)
                r = st[r].pre
            list_id.reverse()
            res_ids.append(list_id)
        return res_ids

