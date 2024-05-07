#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  user.py
@Time    :  2024/04/21 19:42:14
@Version :  1.0
@Desc    :  用户管理模块
'''
import hashlib
from flask import Blueprint, request, jsonify, session, redirect
from app.src.models import db_session, User, Log
from app.utils import crmLogger, redisClient, methods
from datetime import date

user = Blueprint("user", __name__)

# 变量
SALE = "1We4Zx0Mn" # md5的加盐值

@user.route("/login", methods=methods.ALL)
def login():
    '''
    用户登录
    '''
    if request.method == "POST":
        ip_addr = request.remote_addr or "127.0.0.1" # 用户IP地址
        try:
            # 判断是否开启IP白名单以及用户是否在白名单中
            if redisClient.getData("enable_white") is not None and bool(int(redisClient.getData("enable_white"))):
                if not redisClient.getSet(ip_addr):  # 如果不在白名单中无需响应
                    return
            # 获取session中验证码的id
            captcha_id = session.get("captcha_id")
            # 如果获取为空则返回登录页
            if captcha_id is None:
                return redirect("/login", code=302)
            userData = request.get_json()
            # 验证码验证
            cache_captcha = redisClient.getData(captcha_id)
            if cache_captcha is None:
                return jsonify({
                    "code": -2,
                    "message": "验证码错误"
                }), 200
            if userData["captcha"].lower() != str(cache_captcha):
                return jsonify({
                    "code": -2,
                    "message": "验证码错误"
                }), 200
            # 用户名密码验证
            result = db_session.query(User).filter(User.username == userData["username"], User.password == hashlib.md5((userData["password"].upper() + SALE).encode()).hexdigest().lower()).first()
            if result is None:
                # 判断是否开启锁定功能
                # 更新redis中记录

                # 判断是否大于设置
                return jsonify({
                    "code": -1,
                    "message": "用户名密码错误"
                }), 200
            if result.status == 0:
                return jsonify({
                    "code": -1,
                    "message": "用户已被锁定"
                }), 200
            if result.status == 2:
                return jsonify({
                    "code": -1,
                    "message": "用户已过期"
                }), 200
            # 登录成功
            # 判断是否开启锁定功能
            # 清除用户的错误次数记录
                
            # 数据库日志记录登录成功
            login_log = Log(ip=ip_addr, operate_type="登录", operate_content=f"用户{userData['username']}登录成功", operate_user=userData['username'])
            db_session.add(login_log)
            db_session.commit()
            # redis删除验证码
            redisClient.delData(captcha_id)    
            # 设置session
            session["username"] = result.username
            session.permanent = True
            return jsonify({
                "code": 0,
                "message": "登录成功"
            }), 200
        except (KeyError, TypeError):
            return jsonify({
                "code": -1,
                "message": "错误的请求"
            }), 400
        except Exception as e:
            # 日志文件记录异常
            crmLogger.error(f"登录模块功能异常: {e}")
            return jsonify({
                "code": -1,
                "message": "服务器异常"
            }), 500
    else:
        return jsonify({
            "code": -1,
            "message": "只支持POST方法"
        }), 405

@user.route("/logout", methods=methods.ALL)
def logout():
    '''
    用户登出
    '''
    if request.method == "GET":
        ip_addr = request.remote_addr
        try:   
            username = session.get("username")
            # 清除session
            session.pop('username',None)
            # 写入日志
            logout_log = Log(ip=ip_addr,operate_type="登出",operate_content=f"用户{username}登出系统", operate_user=username)
            db_session.add(logout_log)
            db_session.commit()
            return jsonify({
                "code": 0,
                "message": "success"
            }), 200
        except Exception as e:
            crmLogger.error(f"登出模块功能异常: {e}")
        finally:
            return jsonify({
                "code": 0
            }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405

@user.route("/query", methods=methods.ALL)
def query():
    '''
    查询用户
    '''
    if request.method == "GET":
        try:
            username = session.get("username")
            if username is None:
                return redirect("/login")
            if username != "admin":
                return jsonify({
                    "code": -1,
                    "message": "无权限访问"
                }), 403
            args = request.args
            page = args.get("page", default=1)
            limit = args.get("limit", default=10)
            result = db_session.query(User).filter(User.username != "admin").offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
            return jsonify({
                "code": 0,
                "message": {
                    "total": len(result),
                    "data": [{"id": data.uid, "username": data.username, "name": data.name, "type": data.type, "expire": data.expire_time, "company": data.company, "status": data.status} for data in result]
                }
            }), 200
        except Exception as e:
            crmLogger.error(f"查询用户模块功能异常: {e}")
            return jsonify({
                "code": -1,
                "message": "服务器内部异常"
            }), 500
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405

@user.route("/add")
def addUser():
    '''
    创建用户
    '''
    if request.method == "POST":
        try:
            if session.get("username") != "admin":
                return jsonify({
                    "code": -1,
                    "message": "需要管理员权限"
                }), 200
            userData = request.get_json()
            is_exist = db_session.query(User).filter(User.username == userData["username"]).first()
            if is_exist:
                return jsonify({
                    "code": -1,
                    "message": f"{userData['username']}用户名已存在"
                }), 200
            newUser = User(
                name=userData.get("name", ""),
                username=userData["username"]
            )
            db_session.add(newUser)
            db_session.commit()  # 提交事务
        except Exception as e:
            pass
    else:
        return jsonify({
            "code": -1,
            "message": "只支持POST方法"
        }), 405

@user.route("/edit")
def editUser():
    '''
    编辑用户
    '''
    if request.method == "POST":
        try:
            if session.get("username") != "admin":
                return jsonify({
                    "code": -1,
                    "message": "需要管理员权限"
                }), 200
            return jsonify({
                "code": 0,
                "message": "用户创建成功"
            }), 200
        except Exception as e:
            pass
    else:
        return jsonify({
            "code": -1,
            "message": "只支持POST方法"
        }), 405

@user.route("/unlock")
def unlockUser():
    '''
    解锁用户
    '''
    if request.method == "POST":
        # 判断是否是admin用户
        if session.get("username") != "admin":
            return jsonify({
                "code": -1,
                "message": "需要管理员权限"
            }), 200
        return jsonify({
            "code": 0,
            "message": "用户解锁成功"
        }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持POST方法"
        }), 405

@user.route("/setpwd")
def setPassword():
    '''
    更新用户的密码
    '''
    if request.method == "POST":
        username = session.get("username")
        userData = request.get_json()
        # 更新数据库中用户的密码
        db_session.query(User).filter(User.username == username).update({"password": hashlib.md5((userData["new_password"].upper()+SALE).encode()).hexdigest().lower()})
        db_session.commit()
        return jsonify({
            "code": 0,
            "message": "密码更新成功"
        }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持POST方法"
        }), 405


@user.route("/state")
def state():
    '''
    获取用户状态
    '''
    if request.method == "GET":
        username = session.get("username")
        now = date.today()
        result = db_session.query(User).filter(User.username == username).first()
        td = result.pwd_expire_time - now
        return jsonify({
            "code": 0,
            "message": {
                "name": result.name,
                "avator": result.avator,
                "is_first": bool(result.is_first),
                "expire": td.days
            }
        }),200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }),405
    
@user.route("/first", methods=methods.ALL)
def unFirst():
    '''
    更新用户是否第一次登录
    '''
    if request.method == "GET":
        username = session.get("username")
        db_session.query(User).filter(User.username == username).update({"is_first": 0})
        db_session.commit()
        return jsonify({
            "code": 0,
            "message": "success"
        }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405

@user.route("/list", methods=methods.ALL)
def listUser():
    '''
    获取用户列表
    '''
    return jsonify({
        "code": 0,
        "message": ["admin", "test"]
    }), 200
