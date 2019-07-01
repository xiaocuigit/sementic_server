"""
@description: 系统配置文件
@author: Wu Jiang-Heng
@email: jiangh_wu@163.com
@time: 2019-06-29
@version: 0.0.1
"""
from os import getcwd, makedirs
from os.path import abspath, join, exists, pardir


class SystemInfo(object):
    """
    系统内部配置信息
    """

    _instance = None  # 单例模式-用来存放实例

    def __init__(self):
        """
        初始化
        """
        rootpath = str(getcwd()).replace("\\", "/")
        if 'source' in rootpath.split('/'):
            self.base_path = join(pardir, pardir)
        else:
            self.base_path = join(getcwd(), 'sementic_server')

        self.base_log_path_corr = join(self.base_path, "output", "correction_record")
        if not exists(self.base_log_path_corr):
            makedirs(self.base_log_path_corr)
        self.log_path_corr = join(self.base_log_path_corr, "record.log")
