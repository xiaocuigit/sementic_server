from os import getcwd
from os.path import abspath, join


class SystemInfo(object):
    """
    系统内部配置信息
    """

    _instance = None  # 单例模式-用来存放实例

    def __init__(self, is_test=False):
        if is_test:
            self.base_path = join(abspath(getcwd()), "..", "..")
        else:
            self.base_path = join(abspath(getcwd()), "sementic_server", "data")
