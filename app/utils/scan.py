#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  scan.py
@Time    :  2024/05/08 10:01:09
@Version :  1.0
@Desc    :  扫描文件、扫描IP
'''
import pyclamd
import traceback
import ping3
from app.utils.config import CLAMAV_HOST, CLAMAV_PORT
from app.utils.logger import crmLogger

def scan_file(filename: str) -> bool:
    '''
    扫描文件
    :param filename: 文件路径
    :return bool:
    '''
    try:
        conn = pyclamd.ClamdNetworkSocket(CLAMAV_HOST, CLAMAV_PORT)
        if not conn.ping():  # clamav服务不可用
            return True
        result = conn.scan_file(filename)
        if result[filename] == "OK":
            return True
        else:
            return False        
    except pyclamd.ScanError:
        crmLogger.error(f"[scan_file]扫描文件时发生错误: {traceback.format_exc()}")
        return True
    except pyclamd.ConnectionError:
        crmLogger.error(f"[scan_file]连接到clamav时发生错误: {traceback.format_exc()}")
        return True
    finally:
        conn.disconnect()

def scan_ip(ip: str) -> bool:
    '''
    扫描IP
    :param ip: ip地址
    :return:
    '''
    try:
        resp = ping3.ping(ip, 2)
        if resp is not None:
            return True
        else:
            return False
    except:
        crmLogger.error(f"[scan_ip]ping {ip} 时出现错误: {traceback.format_exc()}")
        return False
