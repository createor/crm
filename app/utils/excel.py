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
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
# from openpyxl.styles import DropDown

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


def createExcel(filepath: str, filename: str, sheet_name: str, header: dict, data: dict, is_template: bool = False, passwd: str="") -> bool:
    '''
    创建表格
    :param filepath: 文件存放目录
    :param filename: 文件名
    :param sheet_name: 工作簿名称
    :param header: 表头
    :param data: 数据
    :param is_template: 是否为模板
    :param passwd: 加密密码
    :return:
    '''
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name  # 
        # 写入表头
        for col, value in header.items():
            ws.cell(row=1, column=col, value=value)
        # 给表格添加密码
        if passwd != "":
            ws.protection.password = passwd
        # 设置样式,data中type如果为1-字符串,2-下拉列表,取值data中的options
        # for col, value in data.items():
        #     if value["type"] == 1:
        #         ws.cell(row=2, column=col, value=value["value"])
        #     elif value["type"] == 2:
        #         ws.cell(row=2, column=col, value=value["value"])
        #         ws.cell(row=2, column=col).data_type = "d"
        if not is_template:
            # 写入数据
            pass
        wb.save(os.path.join(filepath, filename), sheet_name, index=None)
        return True
    except Exception as e:
        crmLogger.error(f"写入表格时发生错误: {e}")
        return False
