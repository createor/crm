#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  urls.py
@Time    :  2024/04/18 19:02:22
@Version :  1.0
@Desc    :  url
'''
import os
import traceback
from app.config import app
from app.src import user, system, syslog, manage
from app.src.models import db_session, File, Log
from flask import request, session, g, render_template, redirect, url_for, jsonify, send_from_directory, send_file
from app.utils import UPLOAD_IMAGE_DIR, UPLOAD_EXCEL_DIR, TEMP_DIR, ALLOWED_EXTENSIONS, SCAN_UPLOAD_FILE, methods, crmLogger, redisClient, getUuid, getCaptcha, verify, scan_file
from werkzeug.utils import secure_filename

@app.route("/index", methods=methods.ALL)
@verify(allow_methods=["GET"])
def index():
    '''首页'''
    return render_template("index.html", is_admin=(g.username == "admin"))  # is_admin--判断是否是管理员账号
    
@app.route("/login", methods=methods.ALL)
def login():
    '''登录页'''
    # 获取用户访问IP
    ip_addr = request.headers.get("X-Forwarded-For") or "127.0.0.1"  # 通过nginx转发
    # ip_addr = request.remote_addr or "127.0.0.1"  # 直接访问

    if bool(int(redisClient.getData("crm:system:enable_white"))):  # 判断是否开启白名单机制
        if not redisClient.getSet("crm:system:white_ip_list", ip_addr):
            return jsonify({"code": -1, "message": "无法访问,你不在白名单中"}), 403
        
    if request.method == "GET":
        if session.get("username") is not None:
            return redirect(url_for("index"))  
        errMsg = request.args.get("errMsg", "null")  # 获取错误信息
        return render_template("login.html", errMsg=errMsg)
    else:
        return jsonify({"code": -1, "message": "不支持的请求方法"}), 405

@app.route("/crm/api/v1/crm_manage", methods=methods.ALL)
@verify(allow_methods=["GET"], check_ip=True)
def crm_manage():
    '''资产管理页面'''
    return render_template("crm_manage.html")

@app.route("/crm/api/v1/crm_user", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True, check_ip=True)
def crm_user():
    '''用户管理页面'''
    return render_template("crm_user.html")

@app.route("/crm/api/v1/crm_system", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True, check_ip=True)
def crm_system():
    '''系统设置页面'''
    return render_template("crm_system.html")

@app.route("/crm/api/v1/crm_log", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True, check_ip=True)
def crm_log():
    '''操作日志页面'''
    return render_template("crm_log.html")

@app.route("/", methods=methods.ALL)
@verify(allow_methods=["GET"])
def entrance():
    '''访问入口'''
    return redirect(url_for("index"))
    
@app.route("/crm/api/v1/captcha", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取验证码", auth_login=False)
def captcha():
    '''验证码功能'''
    if session.get("captcha_id"):
        redisClient.delData(session.get("captcha_id"))  # 刷新验证码要先删除redis中的旧验证码

    uuid = getUuid()
    code, imgStr = getCaptcha()

    redisClient.setData(uuid, code, 180)  # 验证码信息写入redis,设置3分钟有效期

    session["captcha_id"] = uuid

    return jsonify({"code": 0, "message": imgStr}), 200

@app.route("/crm/api/v1/upload", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="上传文件")
def upload():
    '''上传文件'''
    if "file" not in request.files:  # 判断请求中是否携带文件
        return jsonify({"code": -1, "message": "错误的请求"}), 400
    
    file = request.files["file"]  # 获取文件

    if "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS:  # 判断文件格式
        filename = secure_filename(file.filename)   # 文件名
        affix = filename.rsplit(".", 1)[1].lower()  # 文件后缀
        file_uuid = getUuid()  # 文件uuid
        path_type = 1          # 默认文件上传路径

        if affix in ["xlsx", "xls"]:
            file.save(os.path.join(UPLOAD_EXCEL_DIR, f"{file_uuid}.{affix}"))  # 表格保存
        else:
            path_type = 2
            file.save(os.path.join(UPLOAD_IMAGE_DIR, f"{file_uuid}.{affix}"))  # 图片保存

        if SCAN_UPLOAD_FILE:  # 使用clamav扫描文件
            # 如果是直接部署在windows或者linux上
            filepath = os.path.join(UPLOAD_EXCEL_DIR, f"{file_uuid}.{affix}") if path_type == 1 else os.path.join(UPLOAD_IMAGE_DIR, f"{file_uuid}.{affix}")
            # 如果是使用容器部署
            # filepath = os.path.join("/data/excels", f"{file_uuid}.{affix}") if path_type == 1 else os.path.join("/data/images", f"{file_uuid}.{affix}")
            
            if not scan_file(filepath):
                os.remove(filepath)  # 移除文件
                crmLogger.error(f"用户{g.username}上传文件{filename}失败: 含有不安全的内容")
                return jsonify({"code": -1, "message": "文件含有不安全的内容" }), 400

        try:  # 写入数据库
            upload_file = File(uuid=file_uuid, filename=filename, affix=affix, filepath=path_type, upload_user=g.username)
            db_session.add(upload_file)
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入file表发生异常: {traceback.format_exc()}")
            return jsonify({"code": -1, "message": "数据库异常"}), 500
        finally:
            db_session.close()

        try:  # 写入log表
            upload_log = Log(ip=g.ip_addr, operate_type="上传文件", operate_content=f"用户上传文件{filename}", operate_user=g.username)
            db_session.add(upload_log)
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")
        finally:
            db_session.close()
        
        crmLogger.info(f"用户{g.username}成功上传文件{filename}")

        return jsonify({"code": 0, "message": file_uuid}), 200
    
    crmLogger.error(f"用户{g.username}上传文件失败: 不支持的文件格式")

    return jsonify({"code": -1, "message": "不支持的文件格式"}), 400

@app.route("/crm/api/v1/images/<string:filename>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="图片访问", check_ip=True)
def download_image(filename):
    '''图片访问地址'''
    try:
        file = db_session.query(File.affix).filter(File.uuid == filename).first()
    finally:
        db_session.close()

    if file is None:
        return jsonify({"code": -1,"message": "文件不存在"}), 400

    return send_from_directory(UPLOAD_IMAGE_DIR, f"{filename}.{file.affix}")

@app.route("/crm/api/v1/file/<string:filename>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="文件下载", check_ip=True)
def download_file(filename):
    '''下载资产表导出的表格文件或者错误详情文件'''
    try:
        file = db_session.query(File.filename, File.affix).filter(File.uuid == filename).first()
    finally:
        db_session.close()

    if file is None:
        crmLogger.error(f"用户{g.username}下载文件(文件id为{filename})失败: 文件不存在")
        return jsonify({"code": -1, "message": "文件不存在"}), 400
    
    try:
        download_log = Log(ip=g.ip_addr, operate_type="下载文件", operate_content=f"用户下载文件{file.filename}", operate_user=g.username)
        db_session.add(download_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    crmLogger.info(f"用户{g.username}成功下载文件{file.filename}")
    
    if file.affix == "txt":  # 下载txt文件
        return send_file(os.path.join(TEMP_DIR, f"{filename}.{file.affix}"), mimetype="text/plain", as_attachment=True, download_name=file.filename)
    else:  # 下载xlsx文件
        return send_file(os.path.join(TEMP_DIR, f"{filename}.{file.affix}"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=file.filename)

@app.route("/crm/api/v1/help", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="帮助手册")
def download_help():
    '''下载帮助手册'''
    filename = "管理员使用手册.docx" if g.username == "admin" else "用户使用手册.docx"  # pdf文件

    try:
        help_log = Log(ip=g.ip, operate_type="下载手册", operate_content=f"用户下载{filename}", operate_user=g.username)
        db_session.add(help_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    crmLogger.info(f"用户{g.username}成功下载使用手册{filename}")

    return send_file(os.path.join(TEMP_DIR, filename), mimetype="application/pdf", as_attachment=True, download_name=filename)

@app.errorhandler(404)
def page_not_found(error):
    '''404页面'''
    return render_template("404.html"), 404

# 注册蓝图
app.register_blueprint(user, url_prefix="/crm/api/v1/user")
app.register_blueprint(system, url_prefix="/crm/api/v1/system")
app.register_blueprint(syslog, url_prefix="/crm/api/v1/log")
app.register_blueprint(manage, url_prefix="/crm/api/v1/manage")
