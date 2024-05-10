#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  desense.py
@Time    :  2024/05/10 13:57:16
@Version :  1.0
@Desc    :  脱敏模块
'''

def undesense(source: str) -> str:
    '''
    字段脱敏
    :param source: 需要脱敏的字段
    :return:
    '''
    if len(source) == 2:
        return source[:1] + "*"
    if len(source) == 3:
        return source[:1] + "*" + source[2:]
    if len(source) == 4:
        return source[:1] + "**" + source[3:]
    if len(source) >= 5:
        temp = int((len(source) - 3) / 2)
        return source[:temp] + "***" + source[temp + 3:]
    return source

