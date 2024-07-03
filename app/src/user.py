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
from flask import Blueprint, request, g, session, jsonify, redirect
from app.src.models import db_session, User, Log
from app.utils import DEFAULT_PASSWORD, crmLogger, redisClient, methods, verify
from app.utils.config import formatDate
from datetime import date, timedelta, datetime

user = Blueprint("user", __name__)

SALE = "1We4Zx0Mn" # md5的加盐值

@user.route("/login", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="用户登录", auth_login=False)
def userLogin():
    '''用户登录'''
    captcha_id = session.get("captcha_id")  # 获取session中验证码的id
    
    if captcha_id is None:  # 如果获取为空则返回登录页
        return redirect("/login", code=302)

    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["username", "password", "captcha"]):  # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    username = reqData["username"]
    password = reqData["password"]
    captcha = reqData["captcha"]

    if not all([username, password, captcha]):  # 校验参数是否有值
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    cache_captcha = redisClient.getData(captcha_id)

    if cache_captcha is None or reqData["captcha"].lower() != cache_captcha:  # 验证码验证
        return jsonify({"code": -2, "message": "验证码错误"}), 200
    
    try:  # 用户名密码验证

        result = db_session.query(User).filter(User.username == username).first()

    finally:

        db_session.close()

    if result is None:  # 用户名不存在

        crmLogger.error(f"用户{username}登陆失败: 用户名不存在")

        return jsonify({"code": -1, "message": "用户名或密码错误"}), 200
    
    if result.password != hashlib.md5((password.upper() + SALE).encode()).hexdigest().lower():  # 密码错误

        if bool(int(redisClient.getData("crm:system:enable_failed"))):  # 判断是否开启锁定功能

            if redisClient.getData("crm:{}:failed".format(username)) and int(redisClient.getData("crm:{}:failed".format(username))) > int(redisClient.getData("crm:system:failed_count")):  # 判断是否大于设置错误次数

                try:  # 更新user表

                    _user = db_session.query(User).filter(User.username == username).first()

                    if _user:

                        _user.status = 0   # 超出次数则更新用户状态为锁定

                        db_session.commit()

                except:

                    db_session.rollback()  # 发生异常则回滚数据

                    crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")  # 日志记录

                    return jsonify({"code": -1, "message": "数据库异常"}), 500
                
                finally:

                    db_session.close()

                return jsonify({"code": -1, "message": "用户已被锁定"}), 200
            
            else:
                
                redisClient.setIncr("crm:{}:failed".format(username))  # 没有超过次数则在redis中记录加1

        crmLogger.error(f"用户{username}登陆失败: 密码错误")

        return jsonify({"code": -1, "message": "用户名或密码错误"}), 200

    # 判断用户状态
    if result.status == 0:

        crmLogger.error(f"用户{username}登陆失败: 用户失败次数过多,已被锁定")

        return jsonify({"code": -1, "message": "用户已被锁定"}), 200
    
    elif result.status == 2:

        crmLogger.error(f"用户{username}登陆失败: 用户已过期")

        return jsonify({"code": -1, "message": "用户已过期"}), 200
    
    if result.type == 2 and result.expire_time < date.today():  # 判断用户是否是临时用户且授权是否过期

        try:

            result.status = 2    # 更新用户状态为过期

            db_session.commit()

        except:

            db_session.rollback()

            crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

            return jsonify({"code": -1, "message": "数据库异常"}), 500
        
        finally:

            db_session.close()

        crmLogger.error(f"用户{username}登陆失败: 用户已过期")

        return jsonify({"code": -1, "message": "用户已过期"}), 200
    
    if result.pwd_expire_time < date.today():  # 判断密码是否过期

        crmLogger.error(f"用户{username}登陆失败: 密码已过期")

        return jsonify({"code": -1, "message": "用户密码已过期"}), 200

    # 登录成功
    redisClient.setData(f"crm:{username}:ip", g.ip_addr)  # 记录用户登陆的IP

    if bool(int(redisClient.getData("crm:system:enable_failed"))):  # 判断是否开启锁定功能
        redisClient.setData(f"crm:{username}:failed", 0)  # 清除用户的错误次数记录

    try:  # 数据库日志记录登录成功

        login_log = Log(ip=g.ip_addr, operate_type="登录", operate_content="登录成功", operate_user=username)
        db_session.add(login_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{username}登录成功")

    redisClient.delData(captcha_id)  # redis删除已使用的验证码

    # 设置session
    session["username"] = username
    session.permanent = True

    return jsonify({"code": 0, "message": "登录成功"}), 200

@user.route("/logout", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户登出", check_ip=True)
def UserLogout():
    '''用户登出'''
    session.pop("username", None)  # 清除session

    try:  # 写入log表
        
        logout_log = Log(ip=g.ip_addr, operate_type="登出", operate_content="登出系统", operate_user=g.username)
        db_session.add(logout_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")
        
    finally:

        db_session.close()


    crmLogger.info(f"用户{g.username}成功登出系统")  # 写入日志文件

    return jsonify({"code": 0, "message": "登出成功"}), 200

@user.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户查询", is_admin=True, check_ip=True)
def queryUser():
    '''查询用户'''
    args = request.args  # 获取请求参数

    page = int(args.get("page", default=1))
    limit = int(args.get("limit", default=10))

    try:

        count = db_session.query(User).filter(User.username != "admin").count()
    finally:

        db_session.close()

    if count == 0:

        return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200
        
    try:

        result = db_session.query(User).filter(User.username != "admin").offset((page - 1) * limit).limit(limit).all()

    finally:

        db_session.close()

    try:  # 写入log表

        query_log = Log(ip=g.ip_addr, operate_type="查询用户", operate_content="查询所有用户", operate_user=g.username)
        db_session.add(query_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功查询所有用户")

    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": data.uid, "username": data.username, "name": data.name, "type": data.type, "expire": formatDate(data.expire_time), "company": data.company, "status": data.status} for data in result]
        }
    }), 200

@user.route("/add", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建用户", is_admin=True, check_ip=True)
def addUser():
    '''创建用户'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["username", "type", "expire_time", "name", "company"]):  # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    name = reqData["name"]
    username = reqData["username"]
    user_type = reqData["type"]
    expire_time = reqData["expire_time"]
    company = reqData["company"]

    if not all([username, user_type]):  # 校验参数的值
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:  # 判断用户是否已经存在

        is_exist_user = db_session.query(User).filter(User.username == username).first()

    finally:

        db_session.close()

    if is_exist_user:
        return jsonify({"code": -1, "message": f"{username}用户已存在"}), 200
    
    if int(user_type) == 2:

        if not expire_time:
            expire_time = date.today() + timedelta(days=30)  # 如果临时用户没有设置过期时间则默认有效期30天

    try:

        newUser = User(
            name=name,
            username=username,
            password=hashlib.md5((DEFAULT_PASSWORD.upper() + SALE).encode()).hexdigest().lower(),  # 设置密码为默认密码
            create_user=g.username,
            type=int(user_type),
            expire_time=expire_time,
            pwd_expire_time=(date.today() + timedelta(days=90)),  # 默认90天密码有效期
            company=company
        )
        db_session.add(newUser)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入user表发生异常: {traceback.format_exc()}")

        return jsonify({"code": -1, "message": "数据库异常"}), 500
    
    finally:

        db_session.close()

    try:  # 写入log表

        add_log = Log(ip=g.ip_addr, operate_type="创建用户", operate_content=f"创建用户({username})", operate_user=g.username)
        db_session.add(add_log)
        db_session.commit()  # 提交事务

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功创建了用户{username}")

    return jsonify({"code": 0, "message": "用户创建成功"}), 200

@user.route("/edit", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="用户编辑", is_admin=True, check_ip=True)
def editUser():
    '''编辑用户'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["uid", "username", "name", "expire_time", "type", "company"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    user_id = reqData["uid"]
    nickname = reqData["name"]
    username = reqData["username"]
    expire_time = reqData["expire_time"]
    user_type = reqData["type"]
    company = reqData["company"]

    if not all([user_id, username, user_type]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:

        result = db_session.query(User).filter(User.uid == user_id, User.username == username).first()

    finally:

        db_session.close()

    if not result:  # 判断用户是否存在

        crmLogger.error(f"编辑用户{username}失败: 该用户不存在")

        return jsonify({"code": -1, "message": "用户不存在"}), 400

    userStatus = None

    if int(user_type) == 1:  # 如果设置用户是永久用户,则将过期状态改为正常

        userStatus = 1 if result.status == 2 else result.status

    else:

        if expire_time and datetime.strptime(expire_time, "%Y-%m-%d").date() > date.today():  # 如果用户是临时用户且授权时间大于今天则将过期状态改为正常
            
            userStatus = 1 if result.status == 2 else result.status

        else:

            crmLogger.error(f"编辑用户{username}失败: 临时用户未选择过期时间")

            return jsonify({"code": -1, "message": "请选择临时用户过期时间"}), 400
        
    try:  # 更新用户信息

        result.name = nickname
        result.type = int(user_type)
        if expire_time:
            result.expire_time = expire_time
        result.company = company
        if userStatus:
            result.status = userStatus
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

        return jsonify({"code": -1, "message": "数据库异常"}), 500
    
    finally:

        db_session.close()

    try:  # 写入log表

        edit_log = Log(ip=g.ip_addr, operate_type="编辑用户", operate_content=f"编辑用户({username})", operate_user=g.username)
        db_session.add(edit_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功编辑了用户{username}的信息")

    crmLogger.debug(f"用户{username}更新信息: name={nickname}, type={user_type}, expire_time={expire_time}, status={userStatus}, company={company}")

    return jsonify({"code": 0, "message": "用户编辑成功"}), 200

@user.route("/del", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="删除用户", is_admin=True, check_ip=True)
def deleteUser():
    '''删除用户'''
    reqData = request.get_json()  # 获取请求数据

    if not all(key in reqData for key in ["uid", "username"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    user_id = reqData["uid"]
    username = reqData["username"]

    if not all([user_id, username]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:

        _user = db_session.query(User).filter(User.uid == user_id, User.username == username).first()

        if _user:  # 判断用户是否存在

            db_session.delete(_user)  # 删除用户数据

            db_session.commit()

    except:

        db_session.rollback()  # 回滚数据

        crmLogger(f"删除user表发生异常: {traceback.format_exc()}")  # 日志记录

        return jsonify({"code": -1, "message": "数据库异常"}), 500
    
    finally:

        db_session.close()

    try:  # 写入log表

        delete_log = Log(ip=g.ip_addr, operate_type="删除用户", operate_content=f"删除用户({username})", operate_user=g.username)
        db_session.add(delete_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功删除了用户{username}")

    return jsonify({"code": 0, "message": "删除用户成功"}), 200

@user.route("/lock", methods=methods.ALL)
@verify(allow_methods=methods.ALL, module_name="用户锁定", is_admin=True, check_ip=True)
def lockUser():
    '''锁定用户'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["uid", "username"]):  # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    user_id = reqData["uid"]
    username = reqData["username"]

    if not all([user_id, username]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:

        _user = db_session.query(User).filter(User.uid == user_id, User.username == username).first()

        if _user:

            if _user.status == 2:

                crmLogger.error(f"锁定用户{username}失败: 用户已过期")

                return jsonify({"code": -1, "message": "无法锁定已过期用户"}), 400
            
            elif _user.status == 1:

                _user.status = 0

                db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

        return jsonify({"code": -1, "message": "数据库异常"}), 500

    finally:

        db_session.close()

    try:  # 写入log表

        lock_log = Log(ip=g.ip_addr, operate_type="锁定用户", operate_content=f"锁定用户({username})", operate_user=g.username)
        db_session.add(lock_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功锁定了用户{username}")

    return jsonify({"code": 0, "message": "用户锁定成功"}), 200

@user.route("/unlock", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="用户解锁", is_admin=True, check_ip=True)
def unlockUser():
    '''解锁用户'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["uid", "username"]):  # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    user_id = reqData["uid"]
    username = reqData["username"]

    if not all([user_id, username]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:

        _user = db_session.query(User).filter(User.uid == user_id, User.username == username).first()

        if _user:

            if _user.status == 2:

                crmLogger.error(f"用户{username}解锁失败: 用户已过期")

                return jsonify({"code": -1, "message": "无法解锁已过期用户"}), 400
            
            elif _user.status == 0:

                _user.status = 1

                db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

        return jsonify({"code": -1, "message": "数据库异常"}), 500
    
    finally:

        db_session.close()

    try:  # 写入log表

        unlock_log = Log(ip=g.ip_addr, operate_type="解锁用户", operate_content=f"解锁用户({username})", operate_user=g.username)
        db_session.add(unlock_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功解锁了用户{username}")

    return jsonify({"code": 0, "message": "用户解锁成功"}), 200

@user.route("/setpwd", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="密码修改", check_ip=True)
def setPassword():
    '''更新用户的密码'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["old_password", "new_password"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    old_password = reqData["old_password"]
    new_password = reqData["new_password"]

    if not all([old_password, new_password]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:  # 判断旧密码是否正确

        is_right_old_passwd = db_session.query(User).filter(User.username == g.username, User.password == hashlib.md5((old_password.upper()+SALE).encode()).hexdigest().lower()).first()

    finally:

        db_session.close()

    if is_right_old_passwd is None:

        crmLogger.error(f"用户{g.username}更新密码失败: 旧密码不正确")

        return jsonify({ "code": -1, "message": "旧密码不正确"}), 200
    
    try:  # 更新数据库中用户的密码和密码过期时间

        db_session.query(User).filter(User.username == g.username).update({"password": hashlib.md5((new_password.upper()+SALE).encode()).hexdigest().lower(), "pwd_expire_time": date.today() + timedelta(days=90)})
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

        return jsonify({"code": -1, "message": "数据库异常"}), 500
    
    finally:

        db_session.close()

    try:  # 写入log表

        update_log = Log(ip=g.ip_addr, operate_type="修改密码", operate_content="修改密码", operate_use=g.username)
        db_session.add(update_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功修改了密码")

    return jsonify({"code": 0, "message": "密码更新成功"}), 200

@user.route("/reset", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="密码重置", is_admin=True, check_ip=True)
def resetPwd():
    '''重置用户的密码为默认密码'''
    reqData = request.get_json()  # 获取请求数据
    
    if not all(key in reqData for key in ["uid", "username"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    user_id = reqData["uid"]
    username = reqData["username"]

    if not all([user_id, username]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:

        db_session.query(User).filter(User.uid == user_id, User.username == username).update({"password": hashlib.md5((DEFAULT_PASSWORD.upper()+SALE).encode()).hexdigest().lower(), "pwd_expire_time": date.today() + timedelta(days=90)})
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

        return jsonify({"code": -1, "message": "数据库异常"}), 500
    
    finally:

        db_session.close()

    try:

        reset_log = Log(ip=g.ip_addr, operate_type="密码重置", operate_content=f"重置用户{username}的密码", operate_user=g.username)
        db_session.add(reset_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}成功重置了用户{username}的密码")

    return jsonify({"code": 0, "message": "密码重置成功"}), 200

@user.route("/state", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户状态", check_ip=True)
def state():
    '''获取用户状态'''
    try:  # 查询用户

        result = db_session.query(User).filter(User.username == g.username).first()

    finally:

        db_session.close()
    
    if not result:
        return jsonify({"code": -1, "message": "用户不存在"}), 400

    now = date.today()  # 获取今天日期
    td = result.pwd_expire_time - now  # 密码有效时间

    return jsonify({
        "code": 0,
        "message": {
            "name": result.name,  # 用户昵称
            "username": result.username,  # 用户名
            "avator": "/crm/api/v1/images/" + result.avator,  # 头像地址
            "is_first": bool(result.is_first),  # 是否首次登陆
            "expire": td.days,    # 密码有效天数
            "type": result.type,  # 用户类型
            "expire_time": result.expire_time if result.expire_time else "",  # 临时用户过期时间
            "company": result.company,  # 公司、组织名称
            "is_mark": bool(int(redisClient.getData("crm:system:enable_watermark"))),  # 是否显示水印
            "ip": g.ip_addr  # 用户IP地址
        }
    }), 200

@user.route("/list", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取用户列表", is_admin=True, check_ip=True)
def listUser():
    '''获取用户列表'''
    try:

        userList = db_session.query(User.username, User.name, User.uid).all()
    
    finally:

        db_session.close()

    crmLogger.info(f"用户{g.username}查询所有用户列表信息")

    return jsonify({
        "code": 0,
        "message": [{"id": v.uid, "name": v.name, "username": v.username} for v in userList]
    }), 200

@user.route("/modify", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="用户修改资料", check_ip=True)
def modifyUser():
    '''修改用户资料'''
    reqData = request.get_json()  # 获取请求数据

    if not all(key in reqData for key in ["nickname", "company", "avatar"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    try:

        _user = db_session.query(User).filter(User.username == g.username).first()

        if _user:
            if reqData["nickname"]:
                _user.name = reqData["nickname"]
            if reqData["company"]:
                _user.company = reqData["company"]
            if reqData["avatar"]:
                _user.avator = reqData["avatar"]
            db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新user表发生异常: {traceback.format_exc()}")

    try:  # 写入log表

        update_log = Log(ip=g.ip_addr, operate_type="更新资料", operate_content="更新个人资料", operate_user=g.username)
        db_session.add(update_log)
        db_session.commit()

    except:

        db_session.rollback()

        crmLogger.error(f"更新log表发生异常: {traceback.format_exc()}")

    crmLogger.info("用户{}更新了资料".format(g.username))

    return jsonify({"code": 0, "message": {"ip": g.ip_addr, "name": _user.name, "username": g.username}}), 200

@user.route("/mail", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="用户通知信息", check_ip=True)
def getMail():
    '''获取通知'''
    # try:

    #     email = db_session.query().filter().all()

    # finally:

    #     db_session.close()

    return jsonify({
        "code": 0,
        "message": {
            "total": 2,
            "data": {
                "today": {
                    "title": "通知",
                    "detail": "测试"
                },
                "history": [
                    {
                        "title": "通知1",
                        "detail": "测试1"
                    }
                ]
            }
        }
    }), 200
