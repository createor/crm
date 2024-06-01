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
    # 按最新创建的表格排序
    # count = db_session.query(Manage).count()
    # result = db_session.query(Manage).limit()
    return jsonify({
        "code": 0,
        "message": {
            "total": 3,
            "data": [
                {
                    "id": "1",
                    "image": "crm.png",
                    "title": "测试1",
                    "remark": "描述信息1",
                    "time": "2023-01-01创建"
                },
                {
                    "id": "2",
                    "image": "crm.png",
                    "title": "测试2",
                    "remark": "描述信息2",
                    "time": "2023-01-01创建"
                },
                {
                    "id": "3",
                    "image": "crm.png",
                    "title": "测试1",
                    "remark": "描述信息1",
                    "time": "2023-01-01创建"
                }
            ]
        }
    })

@manage.route("/<string:id>", methods=methods.ALL)
def queryTable(id):
    '''
    查找指定的资产表
    '''
    if request.method == "GET":
        return jsonify({
            "code": 0,
            "message": {
                "total": 1,
                "data": [
                    {
                        "id": 1,
                        "ip": "1.1.1.1",
                        "name": "主机1"
                    },
                    {
                        "id": 2,
                        "ip": "1.1.1.2",
                        "name": "主机2"
                    },
                    {
                        "id": 3,
                        "ip": "3.1.1.1",
                        "name": "主机3"
                    },
                    {
                        "id": 4,
                        "ip": "1.4.1.2",
                        "name": "主机4"
                    },
                    {
                        "id": 5,
                        "ip": "1.1.1.5",
                        "name": "主机5"
                    },
                    {
                        "id": 6,
                        "ip": "1.1.6.2",
                        "name": "主机6"
                    }
                ]
            }
        }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405


@manage.route("/add", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建资产表")
def addTable():
    '''
    创建资产表
    '''
    userData = request.get_json()
    filename = userData["filename"]
    table_name = userData["name"]
    table_keyword = userData["keyword"]
    table_desc = userData["desc"]
    is_exist_table = db_session.query(Manage).filter(or_(Manage.name == table_name, Manage == table_keyword)).first()
    if is_exist_table:
        return jsonify({
            "code": -1,
            "message": "表或关键字已存在"
        }), 200
    temp_table = readExcel(os.path.join(UPLOAD_EXCEL_DIR, filename))
    # 表头字段
    table_headers = temp_table.columns.tolist()
    if len(table_headers) == 0:
        crmLogger.error(f"")
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

@manage.route("/export", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="导出资产表")
def export():
    '''
    '''
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
