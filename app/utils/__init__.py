#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  __init__.py
@Time    :  2024/04/18 19:03:00
@Version :  1.0
@Desc    :  None
'''
from app.utils.logger import crmLogger
from app.utils.redisClient import redisClient
from app.utils.captcha import getCaptcha
from app.utils.auth import verify
from app.utils.scan import scan_file, scan_ip
from app.utils.excel import readExcel, createExcel
from app.utils.desense import undesense
from app.utils.pinyin import converWords
from app.utils.cronJob import job
from app.utils.config import *
