#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  system.py
@Time    :  2024/04/21 20:04:11
@Version :  1.0
@Desc    :  系统设置模块
'''
import re
import traceback
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
    # 写入log表
    try:
        query_log = Log(ip=g.ip_addr, operate_type="查询系统配置", operate_content="查询系统配置", operate_user=g.username)
        db_session.add(query_log)
        db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    # 写入日志文件
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
    reqData = request.get_json()  # 获取请求数据
    # 更新数据库记录
    try:
        db_session.query(Setting).filter(Setting.type == "enable_failed").update({"value": int(reqData["enable_failed"])})
        db_session.query(Setting).filter(Setting.type == "enable_white").update({"value": int(reqData["enable_white"])})
        db_session.query(Setting).filter(Setting.type == "enable_single").update({"value": int(reqData["enable_single"])})
        db_session.query(Setting).filter(Setting.type == "failed_count").update({"value": int(reqData["failed_count"])})
        db_session.query(Setting).filter(Setting.type == "enable_watermark").update({"value": int(reqData["enable_watermark"])})
        db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"更新setting表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    # 更新redis信息
    redisClient.setData("crm:system:enable_failed", int(reqData["enable_failed"]))
    redisClient.setData("crm:system:enable_white", int(reqData["enable_white"]))
    redisClient.setData("crm:system:enable_single", int(reqData["enable_single"]))
    redisClient.setData("crm:system:failed_count", int(reqData["failed_count"]))
    redisClient.setData("crm:system:enable_watermark", int(reqData["enable_watermark"]))
    # 写入log表
    try:
        update_log = Log(ip=g.ip_addr, operate_type="修改系统配置", operate_content="修改系统配置", operate_user=g.username)
        db_session.add(update_log)
        db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    # 写入日志文件
    crmLogger.info("用户{}更新配置: enable_failed={}, enable_white={}, enable_single={}, enable_watermark={}, failed_count={}".format(g.username, reqData["enable_failed"], reqData["enable_white"], reqData["enable_single"], reqData["enable_watermark"], reqData["failed_count"]))
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
    page = int(args.get("page", 1))    # 页码
    limit = int(args.get("limit", 3))  # 每页数量
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
        try:
            # 写入log表
            query_log = Log(ip=g.ip_addr, operate_type="查询白名单", operate_content=f"查询白名单,搜索IP:{ip}", operate_user=g.username)
            db_session.add(query_log)
            db_session.commit()
        except:  # 发生异常事务回滚
            db_session.rollback()
            crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
        # 写入日志文件
        crmLogger.info(f"用户{g.username}查询白名单,搜索IP:{ip}")
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
        try:
            # 写入log表
            query_log = Log(ip=g.ip_addr, operate_type="查询白名单", operate_content="查询白名单", operate_user=g.username)
            db_session.add(query_log)
            db_session.commit()
        except:  # 发生异常事务回滚
            db_session.rollback()
            crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
        # 写入日志文件
        crmLogger.info(f"用户{g.username}查询白名单")
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
    reqData = request.get_json()  # 获取请求数据
    # 使用正则判断是否是IP
    if not re.match(r"^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$", reqData["ip"]):
        return jsonify({
            "code": -1,
            "message": "请输入正确的IP地址"
        }), 400
    # 判断是否存在
    if db_session.query(WhiteList).filter(WhiteList.ip == reqData["ip"]).first():
        return jsonify({
            "code": -1,
            "message": "IP已存在"
        }), 200
    # 写入mysql
    try:
        white_list = WhiteList(ip=reqData["ip"], description=reqData["description"])
        db_session.add(white_list)
        db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"写入white_list表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        # 写入log表
        add_log = Log(ip=g.ip_addr, operate_type="添加白名单", operate_content="添加白名单{}".format(reqData["ip"]), operate_user=g.username)
        db_session.add(add_log)
        db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    # 写入redis
    redisClient.setSet("crm:system:white_ip_list", reqData["ip"])
    # 写入日志文件
    crmLogger.info("用户{}添加白名单ip({})".format(g.username, reqData["ip"]))
    return jsonify({
        "code": 0,
        "message": "添加白名单成功"
    }), 200

@system.route("/delete_white_list", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="删除白名单", is_admin=True, check_ip=True)
def deleteWhiteList():
    '''
    删除白名单
    '''
    reqData = request.get_json()  # 获取请求数据
    try:
        # 数据库删除白名单IP
        _ip = db_session.query(WhiteList).filter(WhiteList.id == reqData["id"], WhiteList.ip == reqData["ip"]).first()
        if _ip:
            db_session.delete(_ip)
            db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"删除white_list表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        # 写入log表
        delete_log = Log(ip=g.ip_addr, operate_type="删除白名单", operate_content="删除白名单{}".format(reqData["ip"]), operate_user=g.username)
        db_session.add(delete_log)
        db_session.commit()
    except:  # 发生异常事务回滚
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    # redis中删除白名单IP
    redisClient.delSet("crm:system:white_ip_list", reqData["ip"])
    # 写入日志文件
    crmLogger.info("用户{}删除白名单ip({})".format(g.username, reqData["ip"]))
    return jsonify({
        "code": 0,
        "message": "删除白名单成功"
    }), 200
