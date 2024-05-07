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
from app.utils.config import *
