import logging


def apply_logger(
    log_name: str,
    is_dev: bool = False,
) -> logging.Logger:

    if is_dev:
        log_level = logging.DEBUG
        log_format = "%(levelname)s - %(name)s - %(message)s"
    else:
        log_level = logging.WARNING
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 创建新的 handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))

    # 如果指定了 log_name，单独配置该记录器
    if log_name:
        logger = logging.getLogger(log_name)
        logger.setLevel(log_level)
        logger.addHandler(console_handler)
        return logger
    else:
        logger = logging.getLogger()
        # 移除现有的 handlers（避免重复配置）
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        logger.addHandler(console_handler)

        # 设置日志级别
        logger.setLevel(log_level)
        return logger
