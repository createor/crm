#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  config.py
@Time    :  2024/04/18 19:03:44
@Version :  1.0
@Desc    :  应用项目配置
'''
import os
from flask import Flask
from datetime import timedelta
from app.utils import BASE_DIR

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"), template_folder=os.path.join(BASE_DIR, "templates"))

# 设置json响应显示中文
app.config["JSON_AS_ASCII"] = False
# 设置密钥
app.config["SECRET_KEY"] = "Ths56#9yCXzlo08*7WEf"
# 设置session有效期
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
