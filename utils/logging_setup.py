import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(default_level=logging.INFO):
    """
    全局日志初始化
    """

    # 项目根目录
    project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    # logs/
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "desk_pet.log")

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(default_level)

    # 防止重复初始化
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # 文件日志
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(
        "日志初始化完成 | level=%s | file=%s",
        logging.getLevelName(default_level),
        log_file
    )