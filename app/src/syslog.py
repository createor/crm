#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  syslog.py
@Time    :  2024/04/21 20:50:01
@Version :  1.0
@Desc    :  操作日志模块
'''
from flask import Blueprint, request, jsonify, g
from app.src.models import db_session, Log
from app.utils import methods, crmLogger, verify
from sqlalchemy import and_
from datetime import datetime

syslog = Blueprint("syslog", __name__)

@syslog.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询操作日志", is_admin=True, check_ip=True)
def queryLog():
    '''
    查询操作日志
    '''
    args = request.args  # 获取查询参数
    page = args.get("page", default=1)       # 页码,默认1
    limit = args.get("limit", default=10)    # 每页数量,默认10
    query_condition = []                     # 查询条件
    operate_user = args.get("user", None)    # 用户名
    operate_start = args.get("start", None)  # 开始时间
    operate_end = args.get("end", datetime.now().replace(hour=23, minute=59, second=59, microsecond=0))      # 结束时间
    if operate_user is not None:  # 筛选用户为空
        query_condition.append(Log.operate_user.in_(operate_user.split(",")))
    if operate_start is not None: # 筛选时间为空
        query_condition.append(Log.operate_time >= datetime.strptime(operate_start, "%Y-%m-%dT%H:%M:%S"))
        query_condition.append(Log.operate_time <= datetime.strptime(operate_end, "%Y-%m-%dT%H:%M:%S"))
    if len(query_condition) > 0:  # 存在筛选条件
        try:
            count = count = db_session.query(Log).filter(and_(*query_condition)).count()
            if count == 0:
                return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200
            # 按操作时间倒序排序
            result = db_session.query(Log).filter(and_(*query_condition)).order_by(Log.operate_time.desc()).offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        finally:
            db_session.close()
    else:
        try:
            count = db_session.query(Log).count()
            if count == 0:
                return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200
            result = db_session.query(Log).order_by(Log.operate_time.desc()).offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        finally:
            db_session.close()
    crmLogger.info(f"用户{g.username}查询日志: 结果total={count}")
    crmLogger.debug(f"查询条件: operate_user={operate_user}, operate_start={operate_start}, operate_end={operate_end}, page={page}, limit={limit}")
    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": data.id, "ip": data.ip, "operate_user": data.operate_user, "operate_time": data.operate_time.strftime("%Y-%m-%d %H:%M:%S"), "type": data.operate_type, "content": data.operate_content} for data in result]
        }
    }), 200
