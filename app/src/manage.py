#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  manage.py
@Time    :  2024/04/26 13:53:24
@Version :  1.0
@Desc    :  资产管理模块
'''
import os
from flask import Blueprint, request, jsonify, g, Response
from app.utils import methods, crmLogger, readExcel, UPLOAD_EXCEL_DIR, getUuid, verify, redisClient
from app.src.models import db_session, Manage, Header, Log, Task, DetectResult
from sqlalchemy import or_
import threading

manage = Blueprint("manage", __name__)

@manage.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询资产表")
def query():
    '''
    查询所有资产表
    '''
    args = request.args                        # 获取请求参数
    title = args.get("title", None)            # 资产表标题
    page = int(args.get("page", default=1))    # 当前页码,默认第一页
    limit = int(args.get("limit", default=3))  # 每页显示数量,默认3条
    # 按最新创建的表格降序
    if title:  # 如果存在标题搜索
        count = db_session.query(Manage).filter(Manage.name.like("%{}%".format(title))).count()
        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
        result = db_session.query(Manage).filter(Manage.name.like("%{}%".format(title))).order_by(Manage.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
    else:
        count = db_session.query(Manage).count()
        if count == 0:
            return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
        result = db_session.query(Manage).order_by(Manage.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": item.uuid, "title": item.name, "remark": item.description, "image": f"/crm/api/v1/images/{item.table_image}", "time": f"{item.create_time}创建"} for item in result]
        }
    }), 200

@manage.route("/<string:id>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询指定资产表")
def queryTable(id):
    '''
    查找指定的资产表
    '''
    table = db_session.query(Manage).filter(Manage.uuid == id).first()  # 根据id查找
    if not table:
        return jsonify({
            "code": -1,
            "message": "资产表不存在"
        }), 200
    args = request.args                        # 获取请求参数
    page = int(args.get("page", default=1))    # 当前页码,默认第一页
    limit = int(args.get("limit", default=6))  # 每页显示数量,默认6条
    columns = db_session.query(Header).filter(Header.table_name == table.table_name).all()  # 获取表头信息,所有列
    if not columns:  # 如果没有表头信息,则返回空列表
        return jsonify({
            "code": 0,
            "message": {
                "total": 0,
                "data": []
            }
        }), 200
    # 根据用户搜索关键字返回数据
    key = args.get("key", None)      # 用户查找的字段
    value = args.get("value", None)  # 用户查找的值
    if key and value:  # 如果存在关键字搜索
        count = db_session.query(table.table_name).filter((getattr(table.table_name, key).like(f"%{value}%"))).count()
        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
        result = db_session.query(table.table_name).filter(or_(getattr(table.table_name, key).like("%{}%".format(value)), getattr(table.table_name, "ip").like("%{}%".format(value)))).order_by(table.table_name._id.desc()).offset((page - 1) * limit).limit(limit).all()
    count = db_session.query(table.table_name).count()
    if count == 0:
        return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
    result = db_session.query(table.table_name).order_by(table.table_name._id.desc()).offset((page - 1) * limit).limit(limit).all()
    for item in result:
        for col in columns:
            if col.name not in item.__dict__:
                item.__dict__[col.name] = None  
    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": item._id, col: item[col]} for item in result for col in columns]
        }
    }), 200

@manage.route("/add", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建资产表")
def addTable():
    '''
    创建资产表
    '''
    userData = request.get_json()              # 获取请求参数
    filename = userData.get("filename", None)  # excel文件名
    table_name = userData.get("name", None)    # 资产表标题
    table_keyword = userData.get("keyword")    # 资产表关键字
    table_desc = userData.get("desc")          # 资产表描述
    # 判断表名是否已存在
    is_exist_table = db_session.query(Manage).filter(or_(Manage.name == table_name, Manage == table_keyword)).first()
    if is_exist_table:
        return jsonify({
            "code": -1,
            "message": "表或关键字已存在"
        }), 200
    if filename:
        # 表格导入资产表方式
        temp_table = readExcel(os.path.join(UPLOAD_EXCEL_DIR, filename))  # 读取表格
        if temp_table is None:
            return jsonify({
                "code": -1,
                "message": "读取表格失败"
            }), 200
        # 表头字段
        table_headers = temp_table.columns.tolist()
        if len(table_headers) == 0:
            crmLogger.error(f"读取表格{filename}失败: 表头读取为空")
            return jsonify({
                "code": -1,
                "message": "读取表格失败"
            }), 200
        header_data = [Header() for v in table_headers]
        db_session.add_all(header_data)
        db_session.add(Manage(uuid=getUuid(), name=table_name, description=table_desc, create_user=g.username))
        db_session.add(Log(ip=g.ip_addr, operate_type="创建资产表", operate_content=f"创建资产表{table_name}", operate_user=g.username))
        db_session.commit()
        crmLogger.info()
        return jsonify({
            "code": 0,
            "message": "success"
        }), 200
    else:
        # 直接创建资产表,后面创建列方式
        pass

@manage.route("/template", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="下载资产表模板")
def downloadTemplate():
    '''
    下载资产表模板
    '''
    # return send_from_directory(UPLOAD_EXCEL_DIR, "资产表模板.xlsx", as_attachment=True)

@manage.route("/import", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="导入资产表")
def importTable():
    '''
    导入资产表
    '''
    pass

@manage.route("/edit", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改资产表数据")
def editData():
    '''
    修改资产表数据
    '''
    userData = request.get_json()

@manage.route("/alter", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改列属性")
def alterColumn():
    '''
    修改资产表标题信息
    '''
    userData = request.get_json()

@manage.route("/ping", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="ping探测")
def multDetect():
    '''
    多线程ping探测    
    '''
    userData = request.get_json()  # 用户的请求body数据
    column = userData["column"]  # 用户选择的IP列名
    # 生成任务uuid
    task_id = getUuid()
    # 创建任务,存入redis
    redisClient.lpush("ping_task_queue", task_id)
    # 插入数据库
    task_data = Task(uuid=task_id, status=0, create_user=g.username)
    db_session.add(task_data)
    db_session.commit()
    # 查询任务队列最右边是不是此任务,如果是则执行,执行完成后删除最右边
    # sse推送进度
    def event_stream():
        while True:
            yield ''
    return Response(event_stream(), mimetype="text/event-stream")

@manage.route("/notify", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="到期通知")
def notifyExpire():
    '''
    到期通知
    '''
    args = request.args  # 获取请求参数
    id = args.get("id")  # 资产表id
    # 设置通知消息样式

    # 设置单元格下拉样式

    # sse推送进度
    def event_stream():
        while True:
            yield ''
    return Response(event_stream(), mimetype="text/event-stream")

@manage.route("/export", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="导出资产表")
def export():
    '''
    导出资产表
    '''
    args = request.args  # 获取请求参数
    id = args.get("id")  # 资产表id
    # 设置导出表样式

    # 设置单元格下拉样式

    # sse推送进度
    def event_stream():
        while True:
            yield ''
    return Response(event_stream(), mimetype="text/event-stream")

@manage.route("/header", methods=methods.ALL)
@verify(allow_methods=["GET"])
def getHeader():
    '''
    获取表格的头部字段
    '''
    args = request.args  #
    table_name = args.get("table_name")
    result = db_session.query(Header).filter().all()
    return jsonify({
        "code": 0,
        "message": {
            "id": {
                "title": "ID",
                "order": 1,  # 顺序
                "type": 1,  # 1-文本,2-下拉框,3-时间
                "decode": 0  # 是否脱敏,1-是,0-不是
            },
            "name": {
                "title": "名称",
                "order": 2,
                "type": 1,
                "decode": 0
            },
            "type": {
                "title": "类型",
                "order": 3,
                "type": 3,
                "option": {  # 如果是下拉框,下拉选项
                    "switch": "交换机",
                    "route": "路由器"
                },
                "decode": 0
            },
            "password": {
                "title": "密码",
                "order": 4,
                "type": 1,
                "decode": 1
            },
            "create_time": {
                "title": "创建时间",
                "order": 5,
                "type": 3,
                "decode": 0
            }
        }
    }), 200

@manage.route("/setrule", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建图表规则")
def setEchartRule():
    '''
    创建图表规则
    '''
    userData = request.get_json()  # 用户的请求body数据
    table_name = userData["table_name"]  # 表名
    keyword = userData["keyword"]  # 关键字
    type = userData["type"]  # 图表类型
    config = userData["config"]  # 图表配置
    #创建图表规则

@manage.route("/getrule", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取图表规则")
def getEchartRules():
    '''
    获取图表规则
    '''

@manage.route("/echart", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取图表信息")
def getEchart():
    '''
    获取echart数据
    '''
    args = request.args  # 获取请求参数
    table_name = args.get("table_name")
    result = db_session.query(Header).filter().all()
    return jsonify({
        "code": 0,
        "message": {
            "id": {
                "title": "ID",
                "order": 1,  # 顺序
            }
        }
    }), 200
