#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  pinyin.py
@Time    :  2024/05/29 10:30:42
@Version :  1.0
@Desc    :  中文转拼音模块
'''

import pypinyin

def converWords(words: list = []) -> dict:
    '''
    中文转换为拼音
    :param words: 需要转换的中文列表
    :return:
    '''
    result = {}
    hasConver = []
    for index, word in enumerate(words):
        py = "".join([j for i in pypinyin.lazy_pinyin(word) for j in i])
        while py in hasConver:
            py = py + "1"
        result[word] = {
            "pinyin": py,
            "index": index
        }
    return result
