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
@verify(allow_methods=["GET"], is_admin=True)
def queryLog():
    '''
    查询操作日志
    '''
    args = request.args
    page = args.get("page", default=1)
    limit = args.get("limit", default=10)
    query_condition = []  # 查询条件
    query_string = []
    operate_user = args.get("user")  # 用户名
    operate_start = args.get("start")  # 开始时间
    operate_end = args.get("end")  # 结束时间
    if operate_user is not None:
        crmLogger.debug(f"query Log params(user={operate_user})")
        query_condition.append(Log.operate_user == operate_user)
        query_string.append(f"user={operate_user}")
    if operate_start is not None:
        crmLogger.debug(f"query Log params(start>={operate_start})")
        query_condition.append(Log.operate_time >= datetime.strptime(operate_start, "%Y-%m-%dT%H:%M:%S"))
        query_string.append(f"start={operate_start}")
        if operate_end is not None:
            crmLogger.debug(f"query Log params(end<={operate_end})")
            query_condition.append(Log.operate_time <= datetime.strptime(operate_end, "%Y-%m-%dT%H:%M:%S"))
            query_string.append(f"end={operate_end}")
        else:
            # 如果结束时间为空,默认为今天23:59:59
            crmLogger.debug("query Log params(end<=today)")
            query_condition.append(Log.operate_time <= datetime.now().replace(hour=23, minute=59, second=59, microsecond=0))
            query_string.append("end=today")
    if len(query_condition) > 0:
        count = count = db_session.query(Log).filter(and_(*query_condition)).count()
        result = db_session.query(Log).filter(and_(*query_condition)).offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
    else:
        count = db_session.query(Log).count()
        result = db_session.query(Log).offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
    crmLogger.info(f"query Log success(total={count})")
    condition_str = ",".join(query_string) if query_string else "无"
    query_log = Log(ip=g.ip_addr, operate_type="日志查询",operate_content=f"用户{g.username},条件({condition_str})查询日志",operate_user=g.username)
    db_session.add(query_log)
    db_session.commit()
    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": data.id, "ip": data.ip, "operate_user": data.operate_user, "operate_time": data.operate_time.strftime("%Y-%m-%d %H:%M:%S"), "type": data.operate_type, "content": data.operate_content} for data in result]
        }
    }), 200
