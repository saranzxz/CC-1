# import logging

# logging.basicConfig(
#     filename = './EC2/logs.txt',
#     filemode = 'a',
#     #format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#     datefmt = '%H:%M:%S',
#     level = logging.DEBUG
# )

# def log(level, message):
#     print(level, message)
#     logging.debug(message)

from datetime import datetime

file = './EC2/logs.txt'

def log(level, message):
    fh = open(file, 'a')
    fh.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\t' + level + '\t' + message + '\n')
    fh,close()