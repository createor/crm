#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  system.py
@Time    :  2024/04/21 20:04:11
@Version :  1.0
@Desc    :  系统设置模块
'''
from flask import Blueprint, request, jsonify
from app.src.models import db_session, Setting
from app.utils import redisClient, methods, crmLogger

system = Blueprint("system", __name__)

@system.route("/config", methods=methods.ALL)
def getConfig():
    '''
    获取配置
    '''
    if request.method == "GET":
        # 先从redis查询,没有的话再查mysql,写入redis
        enable_failed = redisClient.getData("enable_failed")
        if enable_failed is None:
            enable_failed = db_session.query(Setting.value).filter(Setting.type == "enable_failed").first()[0]
            redisClient.setData("enable_failed", enable_failed)
        enable_white = redisClient.getData("enable_white")
        if enable_white is None:
            enable_white = db_session.query(Setting.value).filter(Setting.type == "enable_white").first()[0]
            redisClient.setData("enable_white", enable_white)
        enable_single = redisClient.getData("enable_single")
        if enable_single is None:
            enable_single = db_session.query(Setting.value).filter(Setting.type == "enable_single").first()[0]
            redisClient.setData("enable_single", enable_single)
        failed_count = redisClient.getData("failed_count")
        if failed_count is None:
            failed_count = db_session.query(Setting.value).filter(Setting.type == "failed_count").first()[0]
            redisClient.setData("failed_count", failed_count)
        return jsonify({
            "code": 0,
            "message": {
                "enable_failed": bool(int(enable_failed)),
                "enable_white": bool(int(enable_white)),
                "enable_single": bool(int(enable_single)),
                "failed_count": int(failed_count)
            }
        }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405

@system.route("/update", methods=methods.ALL)
def updateConfig():
    '''
    更新配置
    '''
    if request.method == "POST":
        try:
            configData = request.get_json()
            print(configData)
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
            # 数据库日志记录
            return jsonify({
                "code": 0,
                "message": "配置更新成功"
            }), 200
        except Exception as e:
           crmLogger.error(f"更新配置模块功能异常: {e}")
           return jsonify({
                "code": -1,
                "message": "服务器内部异常"
            }), 500
    else:
        return jsonify({
            "code": -1,
            "message": "只支持POST方法"
        }), 405
