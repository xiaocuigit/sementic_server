import logging
from logging.handlers import TimedRotatingFileHandler
from os.path import join


def get_logger(name, path):
    # 定义日志文件
    logger = logging.getLogger(name)  # 不加名称设置root logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    # 使用FileHandler输出到文件, 文件默认level:ERROR
    fh = TimedRotatingFileHandler(path, when="D")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.FATAL)
    logger.addHandler(fh)
    logger.addHandler(sh)
    # logger.propagate = False
    return logger


def construt_log(raw_query, correct_info, using_time):
    return {
        "raw_query": raw_query,
        "correct_info": correct_info,
        "using_time": using_time
    }

