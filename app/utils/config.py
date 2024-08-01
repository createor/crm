#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  config.py
@Time    :  2024/04/22 13:47:25
@Version :  1.0
@Desc    :  配置模块
'''
import os, sys
import hashlib
import uuid
import configparser
from typing import Union
from datetime import date

# 程序路径
if getattr(sys, "frozen", False):
    # 生成可执行exe程序时的路径
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "app")
elif __file__:
    # 代码文件的路径
    # crm->app->utils
    BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app")

def readConfig() -> configparser.ConfigParser:
    '''
    读取配置文件
    :return:
    '''
    if not os.path.exists(os.path.join(BASE_DIR, "server.ini")):
        raise FileNotFoundError("配置文件server.ini不存在")
    config = configparser.ConfigParser()
    config.read(os.path.join(BASE_DIR, "server.ini"), encoding="utf-8")  # 读取配置文件
    return config

cfg = readConfig()  # 实例化

# 服务监听地址
SERVER_HOST = cfg.get("server", "host")

# 服务监听端口
SERVER_PORT = cfg.getint("server", "port")

# 用户默认密码
DEFAULT_PASSWORD = hashlib.md5("Password@123_".encode()).hexdigest()

# 系统默认数据表
SYSTEM_DEFAULT_TABLE = ["crm_user", "crm_setting", "crm_log", "crm_header", "crm_manage", "crm_white_list", "crm_file", "crm_echart", "crm_options", "crm_task", "crm_detect_result", "crm_notify", "crm_notice", "crm_notify_message", "crm_history"]

# 允许上传的文件后缀
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "xls", "xlsx"]

# 表格文件上传保存路径
UPLOAD_EXCEL_DIR = os.path.join(BASE_DIR, cfg.get("server", "upload"), "excels")
if not os.path.exists(UPLOAD_EXCEL_DIR):
    os.makedirs(UPLOAD_EXCEL_DIR)  # 如果不存在则创建

# 图片文件上传保存路径
UPLOAD_IMAGE_DIR = os.path.join(BASE_DIR, cfg.get("server", "upload"), "images")
if not os.path.exists(UPLOAD_IMAGE_DIR):
    os.makedirs(UPLOAD_IMAGE_DIR)  # 如果不存在则创建

# 存放临时文件用于下载
TEMP_DIR = os.path.join(BASE_DIR, cfg.get("server", "download"))
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)  # 如果不存在则创建

# 日志文件路径
LOG_PATH = os.path.join(BASE_DIR, cfg.get("server", "log"))
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)  # 如果不存在则创建

# 是否开启资产审批
ASSET_APPROVAL = cfg.getboolean("process", "approval")

# 应用是否联网
CONNECT_INTERNET = cfg.getboolean("network", "internet")

# 是否扫描上传的文件
SCAN_UPLOAD_FILE = cfg.getboolean("security", "clamav")

# clamav的地址信息
CLAMAV_HOST = cfg.get("security", "host")
CLAMAV_PORT = cfg.getint("security", "port")

# 日志级别
LOG_LEVEL = cfg.get("server", "level")

class Methods:
    '''flask的methods允许的方法'''
    def __init__(self):
        self.methods = ["GET", "POST"]
    
    @property
    def ALL(self):
        return self.methods

methods = Methods()

def getUuid() -> str:
    '''
    获取36位uuid
    :return:
    '''
    return str(uuid.uuid1())

def formatDate(time: Union[date, None], mode: int = 1) -> str:
    '''
    格式化时间
    :param time: 需要格式化的时间
    :param mode: 模式
    :return:
    '''
    if not time:
        return ""
    if mode == 1:
        return time.strftime("%Y-%m-%d")
    elif mode == 2:
        return time.strftime("%Y-%m-%d %H:%M:%S")
