#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  auth.py
@Time    :  2024/05/04 20:02:42
@Author  :  createor@github.com
@Version :  1.0
@Desc    :  鉴权模块
'''
from functools import wraps
import traceback
from flask import jsonify, redirect, request, url_for, session, g
from app.utils import crmLogger, redisClient


def verify(allow_methods: list = ["GET"], module_name: str = "", auth_login: bool = True, is_admin: bool = False, allow_admin: list = ["admin"]):
    '''
    装饰函数,用于识别用户是否登录以及是否是admin用户
    :param allow_methods: 允许的方法
    :param module_name: 模块名称
    :param auth_login: 是否校验用户登录情况
    :param is_admin: 是否只允许管理员访问
    :param allow_admin: 管理员列表
    :return:
    '''
    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            ip_addr = request.remote_addr or "127.0.0.1" # 用户IP地址
            g.ip_addr = ip_addr
            # 判断是否开启IP白名单以及用户是否在白名单中
            enable_white = redisClient.getData("enable_white")
            if enable_white is not None and bool(int(enable_white)):
                if not redisClient.getSet(ip_addr):  # 如果不在白名单中无需响应
                    return
            if request.method in allow_methods:
                try:
                    if auth_login:
                        username = session.get("username")  # 从session获取用户名
                        if username is None:
                            return redirect(url_for("login"))  # 未登录或者登录过期返回登录界面
                        g.username = username
                        if is_admin:
                            if username not in allow_admin:
                                return jsonify({
                                    "code": -1,
                                    "message": "无权限访问"
                                }), 403
                    return func(*args, **kwargs)
                except (KeyError, TypeError):
                    return jsonify({
                        "code": -1,
                        "message": "错误的请求"
                    }), 400
                except Exception:
                    crmLogger.error(f"{module_name}模块功能异常: {traceback.format_exc()}")  # 日志记录错误信息
                    return jsonify({
                        "code": -1,
                        "message": "服务器异常"
                    }), 500
            else:
                return jsonify({
                    "code": -1,
                    "message": "不支持的请求方法"
                }), 405
        return inner_wrapper
    return wrapper
