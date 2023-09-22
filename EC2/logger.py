import logging

logging.basicConfig(
    filename = 'logs.txt',
    filemode = 'a',
    format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt = '%H:%M:%S',
    level = logging.DEBUG
)

logger = logging.getLogger()

def log(level, message):
    logger.debug(message)