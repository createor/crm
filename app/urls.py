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
from app.src.models import db_session, File
from flask import request, session, render_template, redirect, url_for, jsonify, send_from_directory, send_file, g
from app.utils import UPLOAD_IMAGE_DIR, UPLOAD_EXCEL_DIR, TEMP_DIR, ALLOWED_EXTENSIONS, methods, getUuid, getCaptcha, verify, redisClient, scan_file, crmLogger
from werkzeug.utils import secure_filename

@app.route("/index", methods=methods.ALL)
@verify(allow_methods=["GET"])
def index():
    '''
    首页
    '''
    return render_template("index.html", is_admin=(g.username == "admin"))  # is_admin--是否是admin账号
    
@app.route("/login", methods=methods.ALL)
def login():
    '''
    登录页
    '''
    ip_addr = request.remote_addr or "127.0.0.1"

    if bool(int(redisClient.getData("crm:system:enable_white"))):

        if not redisClient.getSet("crm:system:white_ip_list", ip_addr):
            return jsonify({"code": -1, "message": "IP地址不在白名单中"}), 403
        
    if request.method == "GET":

        if session.get("username") is not None:
            return redirect(url_for("index"))
        
        errMsg = request.args.get("errMsg", "null")  # 获取错误信息

        return render_template("login.html", errMsg=errMsg)
    
    else:
        return jsonify({"code": -1, "message": "不支持的请求方法"}), 405

@app.route("/crm/api/v1/crm_manage", methods=methods.ALL)
@verify(allow_methods=["GET"])
def crm_manage():
    '''
    资产管理页面
    '''
    return render_template("crm_manage.html")

@app.route("/crm/api/v1/crm_user", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True)
def crm_user():
    '''
    用户管理页面
    '''
    return render_template("crm_user.html")

@app.route("/crm/api/v1/crm_system", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True)
def crm_system():
    '''
    系统设置页面
    '''
    return render_template("crm_system.html")

@app.route("/crm/api/v1/crm_log", methods=methods.ALL)
@verify(allow_methods=["GET"], is_admin=True)
def crm_log():
    '''
    操作日志页面
    '''
    return render_template("crm_log.html")

@app.route("/", methods=methods.ALL)
@verify(allow_methods=["GET"])
def entrance():
    '''
    访问入口
    '''
    return redirect(url_for("index"))
    
@app.route("/crm/api/v1/captcha", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取验证码", auth_login=False)
def captcha():
    '''
    验证码功能
    '''
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
    '''
    上传文件
    '''
    if "file" not in request.files:  # 判断请求中是否携带文件
        return jsonify({"code": -1, "message": "错误的请求"}), 400
    
    file = request.files["file"]  # 获取文件

    if "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS:  # 判断文件格式

        filename = secure_filename(file.filename)  # 文件名

        affix = filename.rsplit(".", 1)[1].lower()  # 文件后缀

        file_uuid = getUuid()  # 文件uuid

        path_type = 1  # 默认文件上传路径

        if affix in ["xlsx", "xls"]:

            file.save(os.path.join(UPLOAD_EXCEL_DIR, f"{file_uuid}.{affix}"))  # 表格保存

        else:

            path_type = 2

            file.save(os.path.join(UPLOAD_IMAGE_DIR, f"{file_uuid}.{affix}"))  # 图片保存

        # TODO
        # 使用clamav扫描文件
        # filepath = os.path.join(UPLOAD_EXCEL_DIR, file_uuid + "." + affix) if path_type == 1 else os.path.join(UPLOAD_IMAGE_DIR, file_uuid + "." + affix)
        # if not scan_file(filepath):
        #     os.remove(filepath)  # 移除文件
        #     return jsonify({"code": -1, "message": "文件含有不安全的内容" }), 400

        try:  # 写入数据库

            upload_file = File(uuid=file_uuid, filename=filename, affix=affix, filepath=path_type, upload_user=g.username)
            db_session.add(upload_file)
            db_session.commit()

        except:

            db_session.rollback()

            crmLogger.error(f"写入file表发生异常: {traceback.format_exc()}")
        
        return jsonify({"code": 0, "message": file_uuid}), 200
    
    return jsonify({"code": -1, "message": "不支持的文件格式"}), 400

@app.route("/crm/api/v1/images/<string:filename>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="图片访问")
def download_image(filename):
    '''
    图片访问地址
    '''
    try:

        file = db_session.query(File.affix).filter(File.uuid == filename).first()

    finally:

        db_session.close()

    if file is None:
        return jsonify({"code": -1,"message": "文件不存在"}), 400

    return send_from_directory(UPLOAD_IMAGE_DIR, f"{filename}.{file.affix}")

@app.route("/crm/api/v1/file/<string:filename>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="表格下载")
def download_file(filename):
    '''
    下载资产表导出的表格文件
    '''
    try:

        file = db_session.query(File.filename, File.affix).filter(File.uuid == filename).first()

    finally:

        db_session.close()

    if file is None:
        return jsonify({"code": -1, "message": "文件不存在"}), 400

    return send_file(os.path.join(TEMP_DIR, f"{filename}.{file.affix}"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=file.filename)

@app.route("/crm/api/v1/help", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="帮助手册")
def download_help():
    '''
    下载帮助手册
    '''
    filename = "管理员使用手册.docx" if g.username == "admin" else "用户使用手册.docx"

    return send_file(os.path.join(TEMP_DIR, filename), as_attachment=True, download_name=filename)

@app.errorhandler(404)
def page_not_found(error):
    '''
    404页面
    '''
    return render_template("404.html"), 404

# 注册蓝图
app.register_blueprint(user, url_prefix="/crm/api/v1/user")
app.register_blueprint(system, url_prefix="/crm/api/v1/system")
app.register_blueprint(syslog, url_prefix="/crm/api/v1/log")
app.register_blueprint(manage, url_prefix="/crm/api/v1/manage")
