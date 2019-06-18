import logging
from logging.handlers import TimedRotatingFileHandler
from sementic_server.source.intent_extraction.system_info import SystemInfo, join


def get_logger():
    # 定义日志文件
    si = SystemInfo()
    logger = logging.getLogger("intent_extraction")  # 不加名称设置root logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    # 使用FileHandler输出到文件, 文件默认level:ERROR
    fh = TimedRotatingFileHandler(join(si.log_path_corr, "record"), when="D")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def construt_log(raw_query, correct_info, using_time):
    return {
        "raw_query": raw_query,
        "correct_info": correct_info,
        "using_time": using_time
    }
