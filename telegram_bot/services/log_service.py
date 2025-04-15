# telegram_bot/services/log_service.py

import logging
import sys

def setup_logger(name="PGB_BOT", log_to_file: bool = False, log_file: str = "bot.log") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger  # Не переинициализируем, если уже есть обработчики

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
