#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  system.py
@Time    :  2024/04/21 20:04:11
@Version :  1.0
@Desc    :  系统设置模块
'''
from typing import Union
import re
from flask import Blueprint, request, jsonify, g
from app.src.models import db_session, Setting, Log, WhiteList
from app.utils import redisClient, methods, crmLogger, verify

system = Blueprint("system", __name__)

def readConfig(all: bool=True, filter: str="") -> Union[str, tuple]:
    '''
    获取配置
    :param all: 是否查询所有
    :param filter: 指定某个
    :return:
    '''
    if all:
        # 先从redis查询,没有的话再查mysql,写入redis
        enable_failed = redisClient.getData("enable_failed")
        if enable_failed is None:  # 是否开启失败锁定
            enable_failed = db_session.query(Setting.value).filter(Setting.type == "enable_failed").first()[0]
            redisClient.setData("enable_failed", enable_failed)
        enable_white = redisClient.getData("enable_white")
        if enable_white is None:  # 是否开启白名单
            enable_white = db_session.query(Setting.value).filter(Setting.type == "enable_white").first()[0]
            redisClient.setData("enable_white", enable_white)
        enable_single = redisClient.getData("enable_single")
        if enable_single is None:  # 是否开启单点登录
            enable_single = db_session.query(Setting.value).filter(Setting.type == "enable_single").first()[0]
            redisClient.setData("enable_single", enable_single)
        failed_count = redisClient.getData("failed_count")
        if failed_count is None:  # 失败次数
            failed_count = db_session.query(Setting.value).filter(Setting.type == "failed_count").first()[0]
            redisClient.setData("failed_count", failed_count)
        return enable_failed, enable_white, enable_single, failed_count
    else:
        condition = redisClient.getData(filter)
        if condition is None:
            condition = db_session.query(Setting.value).filter(Setting.type == filter).first()[0]
            redisClient.setData(filter, condition)
        return condition

@system.route("/config", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询配置", is_admin=True)
def getConfig():
    '''
    读取配置
    '''
    enable_failed, enable_white, enable_single, failed_count = readConfig()
    query_log = Log(ip=g.ip_addr, operate_type="查询配置", operate_content="查询系统配置", operate_user=g.username)
    db_session.add(query_log)
    db_session.commit()
    crmLogger.info(f"用户{g.username}查询系统配置")
    return jsonify({
        "code": 0,
        "message": {
            "enable_failed": bool(enable_failed),
            "enable_white": bool(enable_white),
            "enable_single": bool(enable_single),
            "failed_count": failed_count
        }
    }), 200

@system.route("/update", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改配置", is_admin=True)
def updateConfig():
    '''
    更新配置
    '''
    configData = request.get_json()
    # 更新数据库记录
    db_session.query(Setting).filter(Setting.type == "enable_failed").update({"value": int(configData["enable_failed"])})
    db_session.query(Setting).filter(Setting.type == "enable_white").update({"value": int(configData["enable_white"])})
    db_session.query(Setting).filter(Setting.type == "enable_single").update({"value": int(configData["enable_single"])})
    db_session.query(Setting).filter(Setting.type == "failed_count").update({"value": int(configData["failed_count"])})
    db_session.commit()
    # 写入redis
    redisClient.setData("enable_failed", int(configData["enable_failed"]))
    redisClient.setData("enable_white", int(configData["enable_white"]))
    redisClient.setData("enable_single", int(configData["enable_single"]))
    redisClient.setData("failed_count", int(configData["failed_count"]))
    update_log = Log(ip=g.ip_addr, operate_type="修改配置", operate_content="修改系统配置", operate_user=g.username)
    db_session.add(update_log)
    db_session.commit()
    crmLogger.info(f"用户{g.username}更新配置")
    # 数据库日志记录
    return jsonify({
        "code": 0,
        "message": "配置更新成功"
    }), 200

@system.route("/get_white_list", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询白名单", is_admin=True)
def getWhiteList():
    '''
    查询白名单
    '''
    args = request.args          # 获取请求参数
    ip = args.get("ip", None)
    page = int(args.get("page", 1))
    limit = int(args.get("limit", 3))
    if ip:
        count = db_session.query(WhiteList).filter(WhiteList.ip.like(f"%{ip}%")).count()
        if count == 0:
            return jsonify({
                "code": 0,
                "message": {
                    "count": 0,
                    "data": []
                }
            }), 200
        result = db_session.query(WhiteList).filter(WhiteList.ip.like(f"%{ip}%")).offset((page - 1) * limit).limit(limit).all()
    else:
        count = db_session.query(WhiteList).count()
        if count == 0:
            return jsonify({
                "code": 0,
                "message": {
                    "count": 0,
                    "data": []
                }
            }), 200
        result = db_session.query(WhiteList).offset((page - 1) * limit).limit(limit).all()
    if result:
        return jsonify({
            "code": 0,
            "message": {
                "count": count,
                "data": [{"id": item.id, "ip": item.ip, "desc": item.description} for item in result]
            }
        }), 200
    
@system.route("/add_white_list", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="添加白名单", is_admin=True)
def addWhiteList():
    '''
    添加白名单
    '''
    userData = request.get_json()
    # 使用正则判断是否是IP
    if not re.match(r"^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$", userData["ip"]):
        return jsonify({
            "code": -1,
            "message": "请输入正确的IP地址"
        }), 400
    # 判断是否存在
    if db_session.query(WhiteList).filter(WhiteList.ip == userData["ip"]).first():
        return jsonify({
            "code": -1,
            "message": "IP已存在"
        }), 200
    # 写入mysql
    white_list = WhiteList(ip=userData["ip"], description=userData["description"])
    db_session.add(white_list)
    add_log = Log(ip=g.ip_addr, operate_type="添加白名单", operate_content="添加白名单{}".format(userData["ip"]), operate_user=g.username)
    db_session.add(add_log)
    db_session.commit()
    # 写入redis
    redisClient.setSet("white_ip_list", userData["ip"])
    crmLogger.info("用户{}添加白名单ip({})".format(g.username, userData["ip"]))
    return jsonify({
        "code": 0,
        "message": "添加白名单成功"
    }), 200
