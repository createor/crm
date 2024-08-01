#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  notify.py
@Time    :  2024/08/01 12:22:57
@Version :  1.0
@Desc    :  到期通知模块
'''

import traceback
from flask import Blueprint, g, jsonify
from app.utils import methods, verify
from app.src.models import db_session, NotifyTask

notify = Blueprint("notify", __name__)

@notify.route("/all", methods=methods.ALL)
@verify(allow_methods=["GET"])
def getAllNotifyTask():
    '''获取所有到期通知任务'''
    try:
        notify_tasks = db_session.query(NotifyTask).all()
    finally:
        db_session.close()
        return jsonify({
            "code": 0,
            "msg": "success",
            "data": [{
                "id": notify_task.id,
                "name": notify_task.name,
                "contact": notify_task.contact,
            }]
        })

@notify.route("", methods=methods.ALL)
@verify(allow_methods=["POST"])
def modifyTaskName():
    '''修改任务名称'''
    pass

@notify.route("", methods=methods.ALL)
@verify(allow_methods=["POST"])
def addNotifyTask():
    '''添加到期通知任务'''
    try:
        name = g.data.get("name")
        contact = g.data.get("contact")
        notify_task = NotifyTask(name=name, contact=contact)
        db_session.add(notify_task)
        db_session.commit()
    finally:
        db_session.close()
        return jsonify({
           "code": 0,
        })
    

