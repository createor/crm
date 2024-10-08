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
    '''读取系统配置'''
    try:  # 写入log表
        query_log = Log(ip=g.ip_addr, operate_type="查询系统配置", operate_content="查询系统配置", operate_user=g.username)
        db_session.add(query_log)
        db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[getConfig]写入log表发生异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    crmLogger.info(f"[getConfig]用户{g.username}成功查询系统配置")  # 写入日志文件

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
    '''修改系统配置'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["enable_failed", "enable_white", "enable_single", "failed_count", "enable_watermark"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    enable_failed = reqData["enable_failed"]
    enable_white = reqData["enable_white"]
    enable_single = reqData["enable_single"]
    failed_count = reqData["failed_count"]
    enable_watermark = reqData["enable_watermark"]

    if not all(map(lambda x: x in [True, False], [enable_failed, enable_white, enable_single, enable_watermark])) or not failed_count:  # 校验参数是否有值
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    if int(failed_count) < 1 or int(failed_count) > 10:  # 检测失败次数
        return jsonify({"code": -1, "message": "失败次数范围1-10"}), 400
    
    try:  # 更新数据库记录
        db_session.query(Setting).filter(Setting.type == "enable_failed").update({"value": int(enable_failed)})
        db_session.query(Setting).filter(Setting.type == "enable_white").update({"value": int(enable_white)})
        db_session.query(Setting).filter(Setting.type == "enable_single").update({"value": int(enable_single)})
        db_session.query(Setting).filter(Setting.type == "failed_count").update({"value": int(failed_count)})
        db_session.query(Setting).filter(Setting.type == "enable_watermark").update({"value": int(enable_watermark)})
        db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[updateConfig]更新setting表发生异常: {traceback.format_exc()}")
        return jsonify({"code": -1, "message": "数据库异常"}), 500
    finally:
        db_session.close()

    # 更新redis信息
    redisClient.setData("crm:system:enable_failed", int(enable_failed))
    redisClient.setData("crm:system:enable_white", int(enable_white))
    redisClient.setData("crm:system:enable_single", int(enable_single))
    redisClient.setData("crm:system:failed_count", int(failed_count))
    redisClient.setData("crm:system:enable_watermark", int(enable_watermark))

    try:  # 写入log表
        update_log = Log(ip=g.ip_addr, operate_type="修改系统配置", operate_content="修改系统配置", operate_user=g.username)
        db_session.add(update_log)
        db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[updateConfig]写入log表发生异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    crmLogger.info(f"[updateConfig]用户{g.username}修改系统配置成功")

    crmLogger.debug(f"[updateConfig]更新后的配置: enable_failed={enable_failed}, enable_white={enable_white}, enable_single={enable_single}, enable_watermark={enable_watermark}, failed_count={failed_count}")  # 写入日志文件

    return jsonify({"code": 0, "message": "配置更新成功"}), 200

@system.route("/get_white_list", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询白名单", is_admin=True, check_ip=True)
def getWhiteList():
    '''查询白名单'''
    args = request.args                # 获取请求参数

    ip = args.get("ip", None)          # IP搜索
    page = int(args.get("page", 1))    # 页码
    limit = int(args.get("limit", 3))  # 每页数量

    if ip:  # 存在IP检索
        try:
            count = db_session.query(WhiteList).filter(WhiteList.ip.like(f"%{ip}%")).count()  # 模糊搜索
        finally:
            db_session.close()

        if count == 0:
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200
            
        try:
            result = db_session.query(WhiteList).filter(WhiteList.ip.like(f"%{ip}%")).order_by(WhiteList.id.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()

        try:  # 写入log表
            query_log = Log(ip=g.ip_addr, operate_type="查询白名单", operate_content=f"查询白名单,通过搜索IP: {ip}", operate_user=g.username)
            db_session.add(query_log)
            db_session.commit()
        except:
            db_session.rollback()  # 发生异常事务回滚
            crmLogger.error(f"[getWhiteList]写入log表发生异常: {traceback.format_exc()}")
        finally:
            db_session.close()

    else:  # 不存在IP检索
        try:
            count = db_session.query(WhiteList).count()
        finally:
            db_session.close()

        if count == 0:
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200
        
        try:            
            result = db_session.query(WhiteList).order_by(WhiteList.id.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()

        try:  # 写入log表           
            query_log = Log(ip=g.ip_addr, operate_type="查询白名单", operate_content="查询白名单信息", operate_user=g.username)
            db_session.add(query_log)
            db_session.commit()
        except:
            db_session.rollback()  # 发生异常事务回滚
            crmLogger.error(f"[getWhiteList]写入log表发生异常: {traceback.format_exc()}")
        finally:
            db_session.close()

    crmLogger.info(f"[getWhiteList]用户{g.username}成功查询白名单信息,搜索IP: {ip}")  # 写入日志文件

    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": item.id, "ip": item.ip, "desc": item.description} for item in result]
        }
    }), 200
    
@system.route("/add_white_list", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="添加白名单IP", is_admin=True, check_ip=True)
def addWhiteList():
    '''添加白名单IP'''
    reqData = request.get_json()  # 获取请求数据

    if not all(key in reqData for key in ["ip", "description"]):  # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    white_ip = reqData["ip"]
    description = reqData["description"]

    if not white_ip:
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    # 使用正则判断是否是IP
    if not re.match(r"^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$", white_ip):
        return jsonify({"code": -1, "message": "请输入正确的IP地址"}), 400

    try:  # 判断是否已存在IP
        if db_session.query(WhiteList).filter(WhiteList.ip == white_ip).first():
            return jsonify({"code": -1, "message": "该IP已存在,请勿重复添加"}), 200 
    finally:
        db_session.close()

    try:  # 不存在则写入whitelist
        white_list = WhiteList(ip=white_ip, description=description, create_user=g.username)
        db_session.add(white_list)
        db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[addWhiteList]写入white_list表发生异常: {traceback.format_exc()}")
        return jsonify({"code": -1, "message": "数据库异常"}), 500
    finally:
        db_session.close()

    try:  # 写入log表
        add_log = Log(ip=g.ip_addr, operate_type="添加白名单", operate_content=f"添加白名单IP({white_ip})", operate_user=g.username)
        db_session.add(add_log)
        db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[addWhiteList]写入log表发生异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    redisClient.setSet("crm:system:white_ip_list", white_ip)  # 将白名单IP写入redis

    crmLogger.info(f"[addWhiteList]用户{g.username}成功添加白名单IP({white_ip})")  # 写入日志文件

    return jsonify({"code": 0, "message": "添加白名单IP成功"}), 200

@system.route("/delete_white_list", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="删除白名单IP", is_admin=True, check_ip=True)
def deleteWhiteList():
    '''删除白名单IP'''
    reqData = request.get_json()  # 获取请求数据

    if not all(key in reqData for key in ["id", "ip"]):  # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    white_id = reqData["id"]
    white_ip = reqData["ip"]

    if not all([white_id, white_ip]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    try:  # 数据库删除白名单IP
        _ip = db_session.query(WhiteList).filter(WhiteList.id == white_id, WhiteList.ip == white_ip).first()
        if _ip:
            db_session.delete(_ip)
            db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[deleteWhiteList]删除white_list表发生异常: {traceback.format_exc()}")
        return jsonify({"code": -1, "message": "数据库异常"}), 500
    finally:
        db_session.close()

    try:  # 写入log表
        delete_log = Log(ip=g.ip_addr, operate_type="删除白名单", operate_content=f"删除白名单IP({white_ip})", operate_user=g.username)
        db_session.add(delete_log)
        db_session.commit()
    except:
        db_session.rollback()  # 发生异常事务回滚
        crmLogger.error(f"[deleteWhiteList]写入log表发生异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    redisClient.delSet("crm:system:white_ip_list", white_ip)  # 从redis中删除白名单IP

    crmLogger.info(f"[deleteWhiteList]用户{g.username}成功删除白名单IP({white_ip})")  # 写入日志文件

    return jsonify({"code": 0, "message": "删除白名单IP成功"}), 200
