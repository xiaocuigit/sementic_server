"""The implementation of actree"""
from queue import Queue


class State:
    "state of the actree"
    def __init__(self):
        # 下一个结点的序号
        self.next = {}
        self.pre = -1
        self.s_pre = -1
        self.fail = 0
        self.cnt = 0


class Aho:
    "actree"
    def __init__(self):
        # 初始化所有值
        self.size = 1
        self.state_table = dict()
        self.state_table[0] = State()

    # 构建trie树
    # 这里接收的输入是一个list，代表转化为id的字符串
    def insert(self, s: list):
        st = self.state_table
        n = len(s)
        now = 0
        
        for i in range(n):
            if (s[i] not in st[now].next):
                st[now].next[s[i]] = self.size
                self.size += 1
            tmp = now
            now = st[now].next[s[i]]
            st[now] = st[now] if now in st else State()
            st[now].pre = tmp
            st[now].s_pre = s[i]
        st[now].cnt += 1

    # 构建actree
    # 构建失配指针
    def build(self):
        st = self.state_table
        q = Queue()
        st[0].fail = -1
        q.put(0)

        while (not q.empty()):
            u = q.get()
            for i, x in st[u].next.items():
                if x > 0:
                    if u == 0:
                        st[st[u].next[i]].fail = 0
                    else:
                        v = st[u].fail
                        while v > -1:
                            if st[v].next.get(i, 0) > 0:
                                st[st[u].next[i]].fail = st[v].next[i]
                                break
                            v = st[v].fail

                        if v == -1:
                            st[st[u].next[i]].fail = 0
                    q.put(st[u].next[i])

    # 字符串要转为id
    def match(self, s: list):
        st = self.state_table
        n = len(s)
        res = 0
        res_set = set()
        now = 0 # 在actree上的索引

        # 对目标串遍历
        for i in range(n):
            if s[i] in st[now].next and st[now].next[s[i]] > 0:
                now = st[now].next[s[i]]
            else:
                f = st[now].fail
                while f != -1 and (s[i] not in st[f].next or st[f].next[s[i]] == 0):
                    f = st[f].fail
                if f == -1:
                    now = 0
                else:
                    now = st[f].next[s[i]]
            if st[now].cnt:
                # 将树上的结束结点返回
                res_set.add(now)
        return res_set

    def parse(self, res_set: set):
        """
            解析答案
        """
        st = self.state_table
        res_ids = list() # list of list

        for r in list(res_set):
            list_id = list()
            while r > 0:
                list_id.append(st[r].s_pre)
                r = st[r].pre
            list_id.reverse()
            res_ids.append(list_id)                
        return res_ids


if __name__ == "__main__":
    a = Aho()
    a.insert([7,1,2])
    a.insert([2,3])
    a.insert([4,5])
    a.insert([3])
    a.build()
    r = a.match([2,2,1,3,3,5,6,6,7,0,1,2,3,4,5])
    print(f"res: {r}")

    p = a.parse(r)
    print(f"p: {p}")

