#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  manage.py
@Time    :  2024/04/26 13:53:24
@Version :  1.0
@Desc    :  资产管理模块
'''
from flask import Blueprint, request, jsonify, session, redirect
from app.utils import methods, crmLogger

manage = Blueprint("manage", __name__)

@manage.route("/query", methods=methods.ALL)
def query():
    '''
    查询所有资产表
    '''
    if request.method == "GET":
        try:
            if session.get("username") is None:
                return redirect("/login")
            # 按最新创建的表格排序
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
        except Exception as e:
            crmLogger.error(f"资产查询模块功能异常: {e}")
            return jsonify({
                "code": -1,
                "message": "服务器内部异常"
            }), 500
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405

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
                    {"id": 1}
                ]
            }
        }), 200
    else:
        return jsonify({
            "code": -1,
            "message": "只支持GET方法"
        }), 405


@manage.route("/add", methods=methods.ALL)
def addTable():
    '''
    创建资产表
    '''
    import time
    time.sleep(3)
    return jsonify({
        "code": 0
    }), 200
