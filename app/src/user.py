#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  user.py
@Time    :  2024/04/21 19:42:14
@Version :  1.0
@Desc    :  用户管理模块
'''
import hashlib
from flask import Blueprint, request, jsonify, session, redirect, g
from app.src.system import readConfig
from app.src.models import db_session, User, Log
from app.utils import crmLogger, redisClient, methods, verify, DEFAULT_PASSWORD
from datetime import date, timedelta

user = Blueprint("user", __name__)

SALE = "1We4Zx0Mn" # md5的加盐值

@user.route("/login", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="登录", auth_login=False)
def login():
    '''
    用户登录
    '''
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
    # 判断是否开启锁定功能
    enable_failed = readConfig(all=False, filter="enable_failed")
    if result is None:
        if bool(enable_failed):
            if int(redisClient.getData(userData["username"])) > int(readConfig(all=False, filter="failed_count")):  # 判断是否大于设置
                return jsonify({
                    "code": -1,
                    "message": "用户已被锁定"
                }), 200
            else:
                # 更新redis中记录加1
                redisClient.setIncr(userData["username"])
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
    if bool(enable_failed):
        # 清除用户的错误次数记录
        redisClient.setData(userData["username"], 0)
    # 数据库日志记录登录成功
    login_log = Log(ip=g.ip_addr, operate_type="登录", operate_content="登录成功", operate_user=userData["username"])
    db_session.add(login_log)
    db_session.commit()
    crmLogger.info(f"用户{userData['username']}登录成功")
    # redis删除验证码
    redisClient.delData(captcha_id)    
    # 设置session
    session["username"] = result.username
    session.permanent = True
    return jsonify({
        "code": 0,
        "message": "登录成功"
    }), 200

@user.route("/logout", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户登出")
def logout():
    '''
    用户登出
    '''
    session.pop('username',None)  # 清除session
    # 写入日志
    logout_log = Log(ip=g.ip_addr, operate_type="登出", operate_content="登出系统", operate_user=g.username)
    db_session.add(logout_log)
    db_session.commit()
    crmLogger.info(f"用户{g.username}登出系统")
    return jsonify({
        "code": 0,
        "message": "success"
    }), 200

@user.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户查询", is_admin=True)
def query():
    '''
    查询用户
    '''
    # 获取参数
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

@user.route("/add")
@verify(allow_methods=["POST"], module_name="创建用户", is_admin=True)
def addUser():
    '''
    创建用户
    '''
    userData = request.get_json()
    is_exist = db_session.query(User).filter(User.username == userData["username"]).first()
    if is_exist:
        return jsonify({
            "code": -1,
            "message": f"{userData['username']}用户名已存在"
        }), 200
    newUser = User(
        name=userData.get("name", ""),
        username=userData["username"],
        password=hashlib.md5((DEFAULT_PASSWORD.upper() + SALE).encode()).hexdigest().lower(),
        create_user=g.username,
        type=userData.get("type", 1),
        expire_time=(userData.get("expire_time", "") if userData.get("type", 1) else ""),  # 如果临时用户没有设置则默认有效期30天
        pwd_expire_time=(date.today()+timedelta(days=90)),  # 默认90天密码有效期
        company=userData.get("company", ""),
        avator=""
    )
    db_session.add(newUser)
    add_log = Log(ip=g.ip_addr, operate_type="创建用户", operate_content=f"创建用户{userData['username']}", operate_user=g.username)
    db_session.add(add_log)
    db_session.commit()  # 提交事务

@user.route("/edit")
@verify(allow_methods=["POST"], module_name="用户编辑", is_admin=True)
def editUser():
    '''
    编辑用户
    '''
    return jsonify({
        "code": 0,
        "message": "用户编辑成功"
    }), 200

@user.route("/unlock")
@verify(allow_methods=["POST"], module_name="用户解锁", is_admin=True)
def unlockUser():
    '''
    解锁用户
    '''
    userData = request.get_json()
    db_session.query(User).filter(User.uid == userData["uid"]).update({"status": 1})
    unlock_log = Log(ip=g.ip_addr, operate_type="解锁用户", operate_content=f"解锁用户{userData['username']}", operate_user=g.username)
    db_session.add(unlock_log)
    db_session.commit()
    return jsonify({
        "code": 0,
        "message": "用户解锁成功"
    }), 200

@user.route("/setpwd")
@verify(allow_methods=["POST"], module_name="密码修改")
def setPassword():
    '''
    更新用户的密码
    '''
    userData = request.get_json()
    # 判断旧密码是否正确
    is_right_old_passwd = db_session.query(User).filter(User.username == g.username, User.password == hashlib.md5((userData["old_password"].upper()+SALE).encode()).hexdigest().lower()).first()
    if is_right_old_passwd is None:
        return jsonify({
            "code": -1,
            "message": "旧密码不正确"
        }), 200
    # 更新数据库中用户的密码
    db_session.query(User).filter(User.username == g.username).update({"password": hashlib.md5((userData["new_password"].upper()+SALE).encode()).hexdigest().lower()})
    update_log = Log(ip=g.ip_addr, operate_type="修改密码", operate_content=f"用户{g.username}修改了密码", operate_use=g.username)
    db_session.add(update_log)
    db_session.commit()
    return jsonify({
        "code": 0,
        "message": "密码更新成功"
    }), 200

@user.route("/reset")
@verify(allow_methods=["POST"], module_name="密码重置", is_admin=True)
def resetPwd():
    '''
    重置用户的密码为默认密码
    '''
    userData = request.get_json()
    db_session.query(User).filter(User.uid == userData["uid"]).update({"password": hashlib.md5((DEFAULT_PASSWORD.upper()+SALE).encode()).hexdigest().lower()})
    reset_log = Log(ip=g.ip_addr, operate_type="密码重置", operate_content=f"重置用户{userData['username']}的密码", operate_user=g.username)
    db_session.add(reset_log)
    db_session.commit()
    return jsonify({
        "code": 0,
        "message": "success"
    }), 200

@user.route("/state")
@verify(allow_methods=["GET"], module_name="用户状态")
def state():
    '''
    获取用户状态
    '''
    now = date.today()
    result = db_session.query(User).filter(User.username == g.username).first()
    td = result.pwd_expire_time - now
    return jsonify({
        "code": 0,
        "message": {
            "name": result.name,
            "username": result.username,
            "avator": "/crm/api/v1/images/" + result.avator,
            "is_first": bool(result.is_first),
            "expire": td.days,
            "company": result.company
        }
    }),200
    
@user.route("/first", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="首次登录")
def unFirst():
    '''
    更新用户是否第一次登录
    '''
    db_session.query(User).filter(User.username == g.username).update({"is_first": 0})
    db_session.commit()
    return jsonify({
        "code": 0,
        "message": "success"
    }), 200

@user.route("/list", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True)
def listUser():
    '''
    获取用户列表
    '''
    userList = db_session.query(User.username).all()
    return jsonify({
        "code": 0,
        "message": [v.username for v in userList]
    }), 200
