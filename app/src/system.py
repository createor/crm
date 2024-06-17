#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  system.py
@Time    :  2024/04/21 20:04:11
@Version :  1.0
@Desc    :  系统设置模块
'''
import re
from flask import Blueprint, request, jsonify, g
from app.src.models import db_session, Setting, Log, WhiteList
from app.utils import redisClient, methods, crmLogger, verify

system = Blueprint("system", __name__)

@system.route("/config", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询系统配置", is_admin=True, check_ip=True)
def getConfig():
    '''
    读取系统配置
    '''
    query_log = Log(ip=g.ip_addr, operate_type="查询配置", operate_content="查询系统配置", operate_user=g.username)
    db_session.add(query_log)
    db_session.commit()
    crmLogger.info(f"用户{g.username}查询系统配置")
    return jsonify({
        "code": 0,
        "message": {
            "enable_failed": bool(int(redisClient.getData("crm:system:enable_failed"))),
            "enable_white": bool(int(redisClient.getData("crm:system:enable_white"))),
            "enable_single": bool(int(redisClient.getData("crm:system:enable_single"))),
            "failed_count": int(redisClient.getData("crm:system:failed_count")),
            "enable_watermark": bool(int(redisClient.getData("crm:system:enable_watermark")))
        }
    }), 200

@system.route("/update", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改系统配置", is_admin=True, check_ip=True)
def updateConfig():
    '''
    更新系统配置
    '''
    configData = request.get_json()  # 获取请求数据
    # 更新数据库记录
    db_session.query(Setting).filter(Setting.type == "enable_failed").update({"value": int(configData["enable_failed"])})
    db_session.query(Setting).filter(Setting.type == "enable_white").update({"value": int(configData["enable_white"])})
    db_session.query(Setting).filter(Setting.type == "enable_single").update({"value": int(configData["enable_single"])})
    db_session.query(Setting).filter(Setting.type == "failed_count").update({"value": int(configData["failed_count"])})
    db_session.query(Setting).filter(Setting.type == "enable_watermark").update({"value": int(configData["enable_watermark"])})
    db_session.commit()
    # 更新redis信息
    redisClient.setData("crm:system:enable_failed", int(configData["enable_failed"]))
    redisClient.setData("crm:system:enable_white", int(configData["enable_white"]))
    redisClient.setData("crm:system:enable_single", int(configData["enable_single"]))
    redisClient.setData("crm:system:failed_count", int(configData["failed_count"]))
    redisClient.setData("crm:system:enable_watermark", int(configData["enable_watermark"]))
    update_log = Log(ip=g.ip_addr, operate_type="修改配置", operate_content="修改系统配置", operate_user=g.username)
    db_session.add(update_log)
    db_session.commit()
    crmLogger.info("用户{}更新配置: enable_failed={}, enable_white={}, enable_single={}, enable_watermark={}, failed_count={}".format(g.username, configData["enable_failed"], configData["enable_white"], configData["enable_single"], configData["enable_watermark"], configData["failed_count"]))
    # 数据库日志记录
    return jsonify({
        "code": 0,
        "message": "配置更新成功"
    }), 200

@system.route("/get_white_list", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询白名单", is_admin=True, check_ip=True)
def getWhiteList():
    '''
    查询白名单
    '''
    args = request.args          # 获取请求参数
    ip = args.get("ip", None)    # IP搜索
    page = int(args.get("page", 1))
    limit = int(args.get("limit", 3))
    if ip:
        count = db_session.query(WhiteList).filter(WhiteList.ip.like(f"%{ip}%")).count()  # 模糊搜索
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
@verify(allow_methods=["POST"], module_name="添加白名单", is_admin=True, check_ip=True)
def addWhiteList():
    '''
    添加白名单
    '''
    userData = request.get_json()  # 获取请求数据
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
