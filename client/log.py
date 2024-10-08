import logging
from logging.handlers import RotatingFileHandler


formatter = logging.Formatter(
    "[%(levelname)s] %(asctime)s - %(filename)s:%(lineno)d - %(message)s"
)


logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
# file_handler = RotatingFileHandler("logs/main.log")
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
