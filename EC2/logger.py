import logging

logging.basicConfig(
    filename = './EC2/logs.txt',
    filemode = 'a',
    #format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt = '%H:%M:%S',
    level = logging.DEBUG
)

def log(level, message):
    print(level, message)
    logging.debug(message)
