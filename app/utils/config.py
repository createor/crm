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

# 用户默认密码
DEFAULT_PASSWORD = hashlib.md5("Password@123_".encode()).hexdigest()

# 允许上传的文件后缀
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "xls", "xlsx"]

# 程序路径
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
elif __file__:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 表格文件上传保存路径
UPLOAD_EXCEL_DIR = os.path.join(BASE_DIR, "files", "excels")
# 图片文件上传保存路径
UPLOAD_IMAGE_DIR = os.path.join(BASE_DIR, "files", "images")

# 存放临时文件用于下载
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# 日志文件路径
LOG_PATH = os.path.join(BASE_DIR, "logs")

class Methods:
    '''
    flask的methods允许的方法
    '''
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
