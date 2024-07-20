#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  captcha.py
@Time    :  2024/04/21 18:40:25
@Version :  1.0
@Desc    :  验证码模块
'''
from typing import Tuple
from captcha.image import ImageCaptcha
import random
import string
import base64
import io
import traceback
from app.utils import crmLogger

def getCaptcha(length: int = 4) -> Tuple[str, str]:
    '''
    获取验证码和验证码图片
    :param length: 验证码长度
    :return: 验证码,验证码图片base64编码
    '''
    captcha_code = "".join(random.choices(string.ascii_uppercase + string.digits, k = length))  # 生成验证码
    try:
        image = ImageCaptcha().generate_image(captcha_code)  # 生成图片
    except Exception:
        crmLogger.error(f"[getCaptcha]生成验证码失败: {traceback.format_exc()}")
        return "", ""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    img_str = base64.b64encode(buffer.getvalue()).decode()  # 图片转成base64编码
    return captcha_code.lower(), img_str
