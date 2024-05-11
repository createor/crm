#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  manage.py
@Time    :  2024/04/26 13:53:24
@Version :  1.0
@Desc    :  资产管理模块
'''
import os
from flask import Blueprint, request, jsonify, g
from app.utils import methods, crmLogger, readExcel, UPLOAD_EXCEL_DIR, getUuid, verify
from app.src.models import db_session, Manage, Header, Log
from sqlalchemy import or_

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
                    "image": "/images/crm.png",
                    "title": "测试1",
                    "remark": "描述信息1",
                    "time": "2023-01-01创建"
                },
                {
                    "id": "2",
                    "image": "/images/crm.png",
                    "title": "测试2",
                    "remark": "描述信息2",
                    "time": "2023-01-01创建"
                },
                {
                    "id": "3",
                    "image": "/images/crm.png",
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
