import time
import logging
import logging.handlers
import os
import inspect

logger = None

def getLogger():
    # logger = logging.getLogger('[PythonService]')
    
    this_file = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(this_file))
    
    log_dir = os.path.join(dirpath,'log')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    name = os.path.join(dirpath, log_dir,"service")

    # logging初始化工作
    logging.basicConfig()
    # myapp的初始化工作
    logger = logging.getLogger('[PythonService]')
    logger.setLevel(logging.INFO)
    # 添加TimedRotatingFileHandler
    # 定义一个1秒换一次log文件的handler
    # 保留3个旧log文件
    filehandler = logging.handlers.TimedRotatingFileHandler(name, when='H', interval=6, backupCount=10)
    # 设置后缀名称，跟strftime的格式一样
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    filehandler.setFormatter(formatter)
    filehandler.suffix = "%Y-%m-%d_%H-%M-%S.log"
    logger.addHandler(filehandler)
    
    return logger

def log_info(info):
    global logger
    if logger == None:
        logger = getLogger()
    logger.info(info)
    print(info)

def log_error(info):
    global logger
    if logger == None:
        logger = getLogger()
    logger.error(info)
    print(info)

if __name__ == "__main__":
    while 1:
        log_info('66655555555555555555555555')
        log_info('666555555555555555555555558888')
        log_error('666555555555555555555555577775')