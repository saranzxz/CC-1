import logging

logging.basicConfig(
    filename = 'logs.txt',
    filemode = 'a',
    format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    dateFmt = '%H:%M:%S',
    level = logging.DEBUG
)

def log(level, message):
    logger.debug('testtest')