#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  logger.py
@Time    :  2024/04/21 21:01:35
@Version :  1.0
@Desc    :  系统日志文件模块
'''
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from app.utils.config import LOG_PATH, LOG_LEVEL

class logger:
    '''系统日志文件'''
    def __init__(self, level: str="info") -> None:
        '''
        :param level: 日志级别
        '''
        level = level.upper()
        if level == "INFO":
            self.level = logging.INFO
        if level == "DEBUG":
            self.level = logging.DEBUG
        if level == "ERROR":
            self.level = logging.ERROR
        if level == "WARNING":
            self.level = logging.WARNING
        if level == "CRITICAL":
            self.level = logging.CRITICAL
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.level)  # 设置日志级别
        # 设置文件格式的handler,保留7天
        self.handler = TimedRotatingFileHandler(os.path.join(LOG_PATH, "crm.log"), when="D", interval=1, backupCount=7)
        self.handler.setLevel(self.level)
        # 设置日志格式
        self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    def error(self, msg) -> None:
        '''
        error级别日志
        :param msg: 日志
        '''
        self.logger.error(msg)
    
    def info(self, msg) -> None:
        '''
        info级别日志
        :param msg: 日志
        '''
        self.logger.info(msg)

    def debug(self, msg) -> None:
        '''
        debug级别日志
        :param msg: 日志
        '''
        self.logger.debug(msg)

    def warning(self, msg) -> None:
        '''
        warning级别日志
        :param msg: 日志
        '''
        self.logger.warning(msg)

    def critical(self, msg) -> None:
        '''
        critical级别日志
        :param msg: 日志
        '''
        self.logger.critical(msg)

crmLogger = logger(LOG_LEVEL)
