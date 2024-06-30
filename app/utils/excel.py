#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  excel.py
@Time    :  2024/04/21 21:03:43
@Version :  1.0
@Desc    :  表格模块
'''
import os
import re
from typing import Union
import traceback
import pandas as pd
from app.utils.logger import crmLogger
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Protection
from openpyxl.cell.text import InlineFont
from openpyxl.cell.rich_text import TextBlock, CellRichText

def readExcel(filePath: str) -> Union[pd.DataFrame, None]:
    '''
    读取表格
    :param filepath: 文件路径
    :return:
    '''
    try:
        return pd.read_excel(filePath).fillna(value="")  # 替换表中的空值nan
    except Exception as e:
        crmLogger.error(f"读取表格时发生错误: {traceback.format_exc()}")
        return None


def createExcel(filepath: str, filename: str, sheet_name: str, header: dict, data: dict, styles: dict, is_template: bool = False, passwd: str="") -> bool:
    '''
    创建表格
    :param filepath: 文件存放目录
    :param filename: 文件名
    :param sheet_name: 工作簿名称
    :param header: 表头 {"column_name": "A/B/C..."}
    :param data: 数据 {"clumn_name": ["d1", "d2"...]}
    :param styles: 样式 {"column_name": {"type": 2, "options": "选项1,选项2..."}}"}
    :param is_template: 是否为模板
    :param passwd: 加密密码
    :return:
    '''
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name  # 设置工作簿名称
        # 写入表头
        for value, index in header.items():
            if value.endswith("*"):
                # 如果有星号则将星号标红表示必填选项
                red = InlineFont(color="FF0000")  # 设置字体颜色
                temp_value = value.split("*")[0]
                richText = TextBlock(red, "*")
                ws[f"{index}1"] = CellRichText(temp_value + richText)
            else:
                ws[f"{index}1"] = value
        # 写入数据
        if not is_template:
            for r in dataframe_to_rows(data, index=False, header=True):
                ws.append(r)
        # 设置样式,type如果为1-字符串,2-下拉列表,取值options
        for col, val in styles.items():
            if val["type"] == 2:
                dv = DataValidation(type="list", formula1='{}'.format(val["options"]), showDropDown=False, allow_blank=True)  # showDropDown-是否显示下拉箭头,allow_blank-是否允许空值
                ws.add_data_validation(dv)
                dv.add(f"{col}2:{col}{ws.max_row}")
        # 给表格添加密码
        if passwd:
            ws.protection.password = passwd
        # 保护工作表
        ws.protection.sheet = True
        ws.protection.options = Protection(locked=True)
        # 保存文件
        wb.save(os.path.join(filepath, f"{filename}.xlsx"))
        return True
    except Exception as e:
        crmLogger.error(f"写入表格时发生错误: {traceback.format_exc()}")
        return False
