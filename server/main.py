import sys

from kokuban_server import KokubanServer
from loguru import logger

if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stdout, format="[{time:HH:mm:ss}] {level}: {message}", level="DEBUG", colorize=True, enqueue=True)
    logger.add("{time:YYYY-MM-DD}.log", enqueue=True, rotation="03:00")

    ks = KokubanServer()
    ks.start()
