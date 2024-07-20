#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  auth.py
@Time    :  2024/05/04 20:02:42
@Version :  1.0
@Desc    :  鉴权模块
'''
from functools import wraps
import traceback
from flask import jsonify, redirect, url_for, request, session, g
from app.utils import crmLogger, redisClient

def verify(allow_methods: list = ["GET"], module_name: str = "", auth_login: bool = True, is_admin: bool = False, allow_admin: list = ["admin"], check_ip: bool = False):
    '''
    装饰函数,用于识别用户是否登录以及是否是admin用户
    :param allow_methods: 允许的方法,默认GET方法
    :param module_name: 模块名称
    :param auth_login: 是否校验用户登录情况,默认true
    :param is_admin: 是否只允许管理员访问,默认false
    :param allow_admin: 管理员列表,默认admin
    :param check_ip: 是否校验用户IP,默认false
    :return:
    '''
    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):

            # 通过nginx转换则获取header的"X-Forwarded-For"字段
            ip_addr = request.headers.get("X-Forwarded-For") or "127.0.0.1"

            # 直接访问
            # ip_addr = request.remote_addr or "127.0.0.1" # 用户访问的IP地址

            g.ip_addr = ip_addr

            if bool(int(redisClient.getData("crm:system:enable_white"))):        # 判断是否开启IP白名单以及用户是否在白名单中

                if not redisClient.getSet("crm:system:white_ip_list", ip_addr):  # IP不在白名单中
                    return jsonify({"code": -1, "message": "无法访问,你不在白名单中"}), 403

            if request.method in allow_methods:  # 校验请求方法

                try:
                    if auth_login:  # 校验是否要求用户登陆

                        username = session.get("username")  # 从session获取用户名

                        if username is None:
                            return redirect(url_for("login", errMsg="null"))  # 未登录或者登录过期返回登录界面
                        
                        g.username = username

                        if is_admin:  # 校验是否要求是管理员

                            if username not in allow_admin:
                                return jsonify({"code": -1, "message": "无权限访问,你不是管理员"}), 403
                            
                        if check_ip and bool(int(redisClient.getData("crm:system:enable_single"))):  # 判断是否需要校验IP以及是否开启单点登陆

                            if ip_addr != redisClient.getData(f"crm:{username}:ip"):  # 访问IP和redis中记录不一致
                                session.pop("username", None)
                                return jsonify({"code": 302, "message": "/login?errMsg=账号已在其他地方登陆"}), 200
                            
                    return func(*args, **kwargs)
                
                except (KeyError, TypeError):

                    crmLogger.error(f"错误的请求: {traceback.format_exc()}")

                    return jsonify({"code": -1, "message": "错误的请求"}), 400
                
                except Exception:

                    crmLogger.error(f"{module_name}模块功能异常: {traceback.format_exc()}")  # 日志记录错误信息

                    return jsonify({"code": -1, "message": "服务器异常"}), 500
                
            else:
                return jsonify({"code": -1, "message": "不支持的请求方法"}), 405
            
        return inner_wrapper
    
    return wrapper
