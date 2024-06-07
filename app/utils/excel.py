#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  excel.py
@Time    :  2024/04/21 21:03:43
@Version :  1.0
@Desc    :  表格模块
'''
import os
import pandas as pd
from app.utils.logger import crmLogger
from typing import Union

def readExcel(filePath: str) -> Union[pd.DataFrame, None]:
    '''
    读取表格
    :param filepath: 文件路径
    :return:
    '''
    try:
        return pd.read_excel(filePath)
    except Exception as e:
        crmLogger.error(f"读取表格时发生错误: {e}")
        return None


def createExcel(filepath: str, filename: str, sheet_name: str, data: dict, passwd: str="") -> bool:
    '''
    创建表格
    :param filepath: 文件存放目录
    :param filename: 文件名
    :param sheet_name: 工作簿名称
    :param data: 数据
    :param passwd: 加密密码
    :return:
    '''
    try:
        df = pd.DataFrame(data)
        if passwd:
            df["password"] = passwd  # 给表格添加密码
        df.to_excel(os.path.join(filepath, filename), sheet_name, index=None)
        return True
    except Exception as e:
        crmLogger.error(f"写入表格时发生错误: {e}")
        return False
