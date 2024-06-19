#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  user.py
@Time    :  2024/04/21 19:42:14
@Version :  1.0
@Desc    :  用户管理模块
'''
import hashlib
import traceback
from flask import Blueprint, request, jsonify, session, redirect, g
from app.src.models import db_session, User, Log
from app.utils import crmLogger, redisClient, methods, verify, DEFAULT_PASSWORD
from app.utils.config import formatDate
from datetime import date, timedelta, datetime

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
    reqData = request.get_json()  # 获取请求数据
    # 验证码验证
    cache_captcha = redisClient.getData(captcha_id)
    if cache_captcha is None:
        return jsonify({
            "code": -2,
            "message": "验证码错误"
        }), 200
    if reqData["captcha"].lower() != str(cache_captcha):
        return jsonify({
            "code": -2,
            "message": "验证码错误"
        }), 200
    # 用户名密码验证
    result = db_session.query(User).filter(User.username == reqData["username"], User.password == hashlib.md5((reqData["password"].upper() + SALE).encode()).hexdigest().lower()).first()
    # 判断是否开启锁定功能
    if result is None:  # 用户名或密码错误
        if bool(int(redisClient.getData("enable_failed"))):
            if redisClient.getData("crm:{}:failed".format(reqData["username"])) and int(redisClient.getData("crm:{}:failed".format(reqData["username"]))) > int(redisClient.getData("crm:system:failed_count")):  # 判断是否大于设置错误次数
                # 写入数据库
                try:
                    _user = db_session.query(User).filter(User.username == reqData["username"]).first()
                    if _user:
                        _user.status = 0
                        db_session.commit()
                except:
                    db_session.rollback()
                    crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
                    return jsonify({
                        "code": -1,
                        "message": "数据库异常"
                    }), 500
                return jsonify({
                    "code": -1,
                    "message": "用户已被锁定"
                }), 200
            else:
                # 更新redis中记录加1
                redisClient.setIncr("crm:{}:failed".format(reqData["username"]))
        return jsonify({
            "code": -1,
            "message": "用户名或密码错误"
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
    # 判断是否是临时用户且授权是否过期
    if result.type == 2 and result.expire_time < date.today():
        # 数据库更新用户状态
        try:
            _user = db_session.query(User).filter(User.username == reqData["username"]).first()
            _user.status = 2
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
            return jsonify({
                "code": -1,
                "message": "数据库异常"
            }), 500
        return jsonify({
            "code": -1,
            "message": "用户已过期"
        }), 200
    # 判断密码是否过期
    if result.pwd_expire_time < date.today():
        return jsonify({
            "code": -1,
            "message": "用户密码已过期"
        }), 200
    # 登录成功
    redisClient.setData("crm:{}:ip".format(reqData["username"]), g.ip_addr)  # 记录用户登陆的IP
    # 判断是否开启锁定功能
    if bool(int(redisClient.getData("crm:system:enable_failed"))):
        # 清除用户的错误次数记录
        redisClient.setData("crm:{}:failed".format(reqData["username"]), 0)
    # 数据库日志记录登录成功
    try:
        login_log = Log(ip=g.ip_addr, operate_type="登录", operate_content="登录成功", operate_user=reqData["username"])
        db_session.add(login_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info(f"用户{reqData['username']}登录成功")
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
@verify(allow_methods=["GET"], module_name="用户登出", check_ip=True)
def logout():
    '''
    用户登出
    '''
    session.pop('username',None)  # 清除session
    try:
        # 写入log表
        logout_log = Log(ip=g.ip_addr, operate_type="登出", operate_content="登出系统", operate_user=g.username)
        db_session.add(logout_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    # 写入日志文件
    crmLogger.info(f"用户{g.username}登出系统")
    return jsonify({
        "code": 0,
        "message": "success"
    }), 200

@user.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户查询", is_admin=True, check_ip=True)
def query():
    '''
    查询用户
    '''
    args = request.args  # 获取请求参数
    page = int(args.get("page", default=1))
    limit = int(args.get("limit", default=10))
    result = db_session.query(User).filter(User.username != "admin").offset((page - 1) * limit).limit(limit).all()
    try:
        query_log = Log(ip=g.ip_addr, operate_type="查询用户", operate_content="查询用户", operate_user=g.username)
        db_session.add(query_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info(f"用户{g.username}查询所有用户")
    return jsonify({
        "code": 0,
        "message": {
            "total": len(result),
            "data": [{"id": data.uid, "username": data.username, "name": data.name, "type": data.type, "expire": formatDate(data.expire_time), "company": data.company, "status": data.status} for data in result]
        }
    }), 200

@user.route("/add", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建用户", is_admin=True, check_ip=True)
def addUser():
    '''
    创建用户
    '''
    reqData = request.get_json()  # 获取请求数据
    # 判断用户是否已经存在
    is_exist = db_session.query(User).filter(User.username == reqData["username"]).first()
    if is_exist:
        return jsonify({
            "code": -1,
            "message": "{}用户名已存在".format(reqData["username"])
        }), 200
    user_expire_time = ""
    if int(reqData["type"]) == 2:
        user_expire_time = reqData["expire_time"]
        if not user_expire_time:
            user_expire_time = date.today() + timedelta(days=30)  # 如果临时用户没有设置过期时间则默认有效期30天
    try:
        newUser = User(
            name=reqData["name"],
            username=reqData["username"],
            password=hashlib.md5((DEFAULT_PASSWORD.upper() + SALE).encode()).hexdigest().lower(),
            create_user=g.username,
            type=int(reqData["type"]),
            expire_time=user_expire_time,
            pwd_expire_time=(date.today() + timedelta(days=90)),  # 默认90天密码有效期
            company=reqData["company"],
            avator=""
        )
        db_session.add(newUser)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        add_log = Log(ip=g.ip_addr, operate_type="创建用户", operate_content="创建用户{}".format(reqData["username"]), operate_user=g.username)
        db_session.add(add_log)
        db_session.commit()  # 提交事务
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info("用户{}创建了用户{}".format(g.username, reqData["username"]))
    return jsonify({
        "code": 0,
        "message": "用户创建成功"
    }), 200

@user.route("/edit", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="用户编辑", is_admin=True, check_ip=True)
def editUser():
    '''
    编辑用户
    '''
    reqData = request.get_json()  # 获取请求数据
    result = db_session.query(User).filter(User.uid == reqData["uid"], User.username == reqData["username"]).first()
    if not result:  # 判断用户是否存在
        return jsonify({
            "code": -1,
            "message": "用户不存在"
        }), 400
    userStatus = None
    if int(reqData["type"]) == 1:  # 如果用户是永久用户,则将过期状态改为正常
        userStatus = 1 if result.status == 2 else None
    else:
        if reqData["expire_time"] and datetime.strptime(reqData["expire_time"], "%Y-%m-%d").date() > date.today():  # 如果用户是临时用户且授权时间大于今天则将过期状态改为正常
            userStatus = 1 if result.status == 2 else None
        else:
            return jsonify({
                "code": -1,
                "message": "请选择临时用户过期时间"
            }), 400
    try:
        result.name = reqData["name"]
        result.type = int(reqData["type"])
        if reqData["expire_time"]:
            result.expire_time = reqData["expire_time"]
        result.company = reqData["company"]
        if userStatus:
            result.status = userStatus
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        edit_log = Log(ip=g.ip_addr, operate_type="编辑用户", operate_content="编辑用户{}".format(reqData["username"]), operate_user=g.username)
        db_session.add(edit_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info("用户信息更新成功")
    return jsonify({
        "code": 0,
        "message": "用户编辑成功"
    }), 200

@user.route("/del", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="删除用户", is_admin=True, check_ip=True)
def deleteUser():
    '''
    删除用户
    '''
    reqData = request.get_json()
    try:
        _user = db_session.query(User).filter(User.uid == reqData["uid"], User.username == reqData["username"]).first()
        if _user:
            db_session.delete(_user)
            db_session.commit()
    except:
        db_session.rollback()
        crmLogger(f"删除user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        delete_log = Log(ip=g.ip_addr, operate_type="删除用户", operate_content="删除用户{}".format(reqData["username"]), operate_user=g.username)
        db_session.add(delete_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info("删除用户{}成功".format(reqData["username"]))
    return jsonify({
        "code": 0,
        "message": "删除成功"
    }), 200

@user.route("/lock", methods=methods.ALL)
@verify(allow_methods=methods.ALL, module_name="用户锁定", is_admin=True, check_ip=True)
def lockUser():
    '''
    锁定用户
    '''
    reqData = request.get_json()
    try:
        _user = db_session.query(User).filter(User.uid == reqData["uid"], User.username == reqData["username"]).first()
        if _user:
            _user.status = 0
            db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        lock_log = Log(ip=g.ip_addr, operate_type="锁定用户", operate_content="锁定用户{}".format(reqData["username"]), operate_user=g.username)
        db_session.add(lock_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info("用户{}锁定了用户{}状态".format(g.username, reqData["username"]))
    return jsonify({
        "code": 0,
        "message": "用户锁定成功"
    }), 200

@user.route("/unlock", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="用户解锁", is_admin=True, check_ip=True)
def unlockUser():
    '''
    解锁用户
    '''
    reqData = request.get_json()  # 获取请求数据
    try:
        _user = db_session.query(User).filter(User.uid == reqData["uid"], User.username == reqData["username"]).first()
        if _user:
            _user.status = 1
            db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        unlock_log = Log(ip=g.ip_addr, operate_type="解锁用户", operate_content="解锁用户{}".format(reqData["username"]), operate_user=g.username)
        db_session.add(unlock_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info("用户{}解锁了用户{}状态".format(g.username, reqData["username"]))
    return jsonify({
        "code": 0,
        "message": "用户解锁成功"
    }), 200

@user.route("/setpwd", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="密码修改", check_ip=True)
def setPassword():
    '''
    更新用户的密码
    '''
    reqData = request.get_json()  # 获取请求数据
    # 判断旧密码是否正确
    is_right_old_passwd = db_session.query(User).filter(User.username == g.username, User.password == hashlib.md5((reqData["old_password"].upper()+SALE).encode()).hexdigest().lower()).first()
    if is_right_old_passwd is None:
        return jsonify({
            "code": -1,
            "message": "旧密码不正确"
        }), 200
    # 更新数据库中用户的密码和密码过期时间
    try:
        db_session.query(User).filter(User.username == g.username).update({"password": hashlib.md5((reqData["new_password"].upper()+SALE).encode()).hexdigest().lower(), "pwd_expire_time": date.today() + timedelta(days=90)})
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        update_log = Log(ip=g.ip_addr, operate_type="修改密码", operate_content=f"用户{g.username}修改了密码", operate_use=g.username)
        db_session.add(update_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info(f"用户{g.username}修改了密码")
    return jsonify({
        "code": 0,
        "message": "密码更新成功"
    }), 200

@user.route("/reset", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="密码重置", is_admin=True, check_ip=True)
def resetPwd():
    '''
    重置用户的密码为默认密码
    '''
    reqData = request.get_json()  # 获取请求数据
    try:
        db_session.query(User).filter(User.uid == reqData["uid"], User.username == reqData["username"]).update({"password": hashlib.md5((DEFAULT_PASSWORD.upper()+SALE).encode()).hexdigest().lower()})
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"更新user表异常: {traceback.format_exc()}")
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    try:
        reset_log = Log(ip=g.ip_addr, operate_type="密码重置", operate_content="重置用户{}的密码".format(reqData["username"]), operate_user=g.username)
        db_session.add(reset_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info("用户{}重置密码成功".format(reqData["username"]))
    return jsonify({
        "code": 0,
        "message": "密码重置成功"
    }), 200

@user.route("/state", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户状态", check_ip=True)
def state():
    '''
    获取用户状态
    '''
    now = date.today()  # 获取今天日期
    result = db_session.query(User).filter(User.username == g.username).first()
    td = result.pwd_expire_time - now  # 密码有效时间
    return jsonify({
        "code": 0,
        "message": {
            "name": result.name,
            "username": result.username,
            "avator": "/crm/api/v1/images/" + result.avator,
            "is_first": bool(result.is_first),
            "expire": td.days,
            "company": result.company,
            "is_mark": bool(int(redisClient.getData("crm:system:enable_watermark"))),
            "ip": g.ip_addr
        }
    }),200

@user.route("/list", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取用户列表", is_admin=True, check_ip=True)
def listUser():
    '''
    获取用户列表
    '''
    userList = db_session.query(User.username, User.name, User.uid).all()
    crmLogger.info(f"用户{g.username}查询所有用户列表信息")
    return jsonify({
        "code": 0,
        "message": [{"id": v.uid, "name": v.name, "username": v.username} for v in userList]
    }), 200

@user.route("/mail", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户通知信息", check_ip=True)
def getMail():
    '''
    获取通知
    '''
    return jsonify({
        "code": 0,
        "message": {
            "count": 1,
            "data": [
                {
                    "title": "通知1"
                }
            ]
        }
    }), 200
