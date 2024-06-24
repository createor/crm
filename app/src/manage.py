#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  manage.py
@Time    :  2024/04/26 13:53:24
@Version :  1.0
@Desc    :  资产管理模块
'''
import os
import traceback
from flask import Blueprint, request, jsonify, g, Response
from app.utils import methods, crmLogger, readExcel, UPLOAD_EXCEL_DIR, SYSTEM_DEFAULT_TABLE, getUuid, verify, redisClient, converWords
from app.src.models import db_session, Manage, Header, Log, Options, Echart, Task, DetectResult, generateManageTable, initManageTable
from sqlalchemy import or_, func
import threading

manage = Blueprint("manage", __name__)

@manage.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询资产表", check_ip=True)
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
        try:
            count = db_session.query(Manage).filter(Manage.name.like("%{}%".format(title))).count()
        finally:
            db_session.close()
        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
        try:
            # 搜索结果
            result = db_session.query(Manage).filter(Manage.name.like("%{}%".format(title))).order_by(Manage.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()
    else:
        try:
            count = db_session.query(Manage).count()
        finally:
            db_session.close()
        if count == 0:
            return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
        try:
            result = db_session.query(Manage).order_by(Manage.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()
    try:
        # 写入log表
        query_log = Log(ip=g.ip_addr, operate_type="查询资产表", operate_content=f"查询资产表,title={title}", operate_user=g.username)
        db_session.add(query_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    finally:
        db_session.close()
    crmLogger.info(f"用户{g.username}查询了资产表,title={title},page={page},limit={limit}")
    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": [{"id": item.uuid, "title": item.name, "remark": item.description, "image": f"/crm/api/v1/images/{item.table_image}", "time": f"{item.create_time}创建"} for item in result]
        }
    }), 200

@manage.route("/title", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询资产表标题", check_ip=True)
def queryTitle():
    '''
    查询所有资产表标题
    '''
    args = request.args  # 获取请求参数
    title = args.get("k", None)  # 搜索关键字
    if title:
        return jsonify({
            "code": 0,
            "message": [item.decode("utf-8") for item in redisClient.getSetData("crm:manage:table_name") if title in item.decode("utf-8")]  # 从redis中查询
        }), 200
    else:
        return jsonify({
            "code": 0,
            "message": []
        }), 200

@manage.route("/header", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询资产表字段", check_ip=True)
def getHeader():
    '''
    获取表格的头部字段
    '''
    args = request.args  # 获取请求参数
    id = args.get("id", None)  # 表格的uuid
    if not id:
        return jsonify({
            "code": -1,
            "message": "缺少id参数"
        }), 400
    # 查看表是否存在
    try:
        table = db_session.query(Manage).filter(Manage.uuid == id).first()
    finally:
        db_session.close()
    if not table:
        return jsonify({
            "code": -1,
            "message": "资产表不存在"
        }), 400
    try:
        result = db_session.query(Header).filter(Header.table_name == table.table_name).order_by(Header.order.asc()).all()
    finally:
        db_session.close()
    if not result:
        return jsonify({
            "code": 0,
            "message": []
        }), 200
    data = []
    for item in result:
        obj = {
            "field": item.value,
            "title": item.name,
            "fieldTitle": item.name,
            "type": item.type,
            "is_mark": bool(item.is_desence),
            "must_input": bool(item.must_input)
        }
        if item.type == 2:  # 如果是下拉框
            try:
                options = db_session.query(Options).filter(Options.table_name == id, Options.header_value == item.value).all()
            finally:
                db_session.close()
            _obj = {}
            _templ = ""
            for opt in options:
                _obj[opt.option_value] = opt.option_name
                _templ += f"<option value='{opt.option_value}'>{opt.option_name}</option>"
            obj["option"] = _obj
            obj["templet"] = "<select><option value=''>请选择</option>" + _templ + "</select>"
        data.append(obj)
    return jsonify({
        "code": 0,
        "message": data
    }), 200

@manage.route("/<string:id>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询指定资产表", check_ip=True)
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
    columns = db_session.query(Header.value).filter(Header.table_name == table.table_name).all()  # 获取表头信息,所有列
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
    queryTable = initManageTable(table.table_name)
    if key and value:  # 如果存在关键字搜索
        count = db_session.query(queryTable).filter((getattr(queryTable.c, key).like(f"%{value}%"))).count()
        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({
                "code": 0,
                "message": {
                    "total": 0,
                    "data": []
                }
            }), 200
        result = db_session.query(queryTable).filter((getattr(queryTable.c, key).like(f"%{value}%"))).order_by(queryTable.c._id.desc()).offset((page - 1) * limit).limit(limit).all()
    else:
        count = db_session.query(queryTable).count()
        if count == 0:
            return jsonify({
                    "code": 0,
                    "message": {
                        "total": 0,
                        "data": []
                    }
                }), 200
    result = db_session.query(queryTable).order_by(queryTable.c._id.desc()).offset((page - 1) * limit).limit(limit).all()
    data = []
    for item in result:
        obj = {}
        obj["_id"] = item._id
        for col in columns:
            obj[col.value] = getattr(item, col.value)
        data.append(obj)
    return jsonify({
        "code": 0,
        "message": {
            "total": count,
            "data": data
        }
    }), 200

@manage.route("/add", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建资产表", check_ip=True)
def addTable():
    '''
    创建资产表
    '''
    userData = request.get_json()              # 获取请求参数
    filename = userData.get("filename", None)  # excel文件名
    table_name = userData.get("name", None)    # 资产表标题
    table_keyword = userData.get("keyword")    # 资产表关键字
    table_desc = userData.get("desc")          # 资产表描述
    if table_name in SYSTEM_DEFAULT_TABLE:
        return jsonify({
            "code": -1,
            "message": "不能使用系统表"
        }), 200
    # 判断表名是否已存在
    try:
        is_exist_table = db_session.query(Manage).filter(or_(Manage.name == table_name, Manage == table_keyword)).first()
    finally:
        db_session.close()
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
        header_data = [Header(name=k, value=v["pinyin"], table_name=table_name, order=v["index"], create_user=g.username) for k, v in converWords(table_headers).items()]
        db_session.add_all(header_data)
        db_session.add(Manage(uuid=getUuid(), name=table_name, description=table_desc, create_user=g.username))
        db_session.add(Log(ip=g.ip_addr, operate_type="创建资产表", operate_content=f"创建资产表{table_name}", operate_user=g.username))
        db_session.commit()
        manageTable = generateManageTable(table_name)  # 创建表
        # 批量插入数据
        db_session.add_all([manageTable(**v) for v in temp_table.to_dict(orient="records")])
        db_session.commit()
        crmLogger.info(f"创建资产表{table_name}成功")
        return jsonify({
            "code": 0,
            "message": "success"
        }), 200
    else:
        # 直接创建资产表,后面创建列方式
        pass

@manage.route("/template", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="下载资产表模板", check_ip=True)
def downloadTemplate():
    '''
    下载资产表模板
    '''
    # return send_from_directory(UPLOAD_EXCEL_DIR, "资产表模板.xlsx", as_attachment=True)

@manage.route("/import", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="导入资产表数据", check_ip=True)
def importTable():
    '''
    导入资产表
    '''
    pass

@manage.route("/edit", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改资产表数据", check_ip=True)
def editData():
    '''
    修改资产表数据
    '''
    reqData = request.get_json()
    try:
        db_session.query()
        db_session.commit()
    except:
        db_session.rollback()
    return jsonify({
        "code": 0,
        "message": "修改成功"
    }), 200

@manage.route("/alter", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改列属性", check_ip=True)
def alterColumn():
    '''
    修改资产表标题信息
    '''
    reqData = request.get_json()
    try:
        table = db_session.query(Manage).filter()
        db_session.commit()
    except:
        db_session.rollback()
        return jsonify({
            "code": -1,
            "message": "数据库异常"
        }), 500
    return jsonify({
        "code": 0,
        "message": "修改成功"
    }), 200

@manage.route("/ping", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="ping探测", check_ip=True)
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
@verify(allow_methods=["POST"], module_name="到期通知", check_ip=True)
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
@verify(allow_methods=["GET"], module_name="导出资产表", check_ip=True)
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

@manage.route("/setrule", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="创建图表规则", check_ip=True)
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
@verify(allow_methods=["GET"], module_name="获取图表规则", check_ip=True)
def getEchartRules():
    '''
    获取图表规则
    '''
    args = request.args  # 获取请求参数
    id = args.get("id", None)  # 获取表id
    if not id:
        return jsonify({
            "code": -1,
            "message": "缺少id参数"
        }), 400
    # 查询表是否存在
    table = db_session.query(Manage).filter(Manage.uuid == id).first()
    if not table:
        return jsonify({
            "code": -1,
            "message": "资产表不存在"
        }), 400
    # 查询规则
    rules = db_session.query(Echart).filter(Echart.table_name == id).order_by(Echart.id.asc()).all()
    if not rules:
        return jsonify({
            "code": 0,
            "message": []
        }), 200
    return jsonify({
        "code": 0,
        "message": [{"id": rule.id, "type": rule.type, "keyword": rule.keyword} for rule in rules]
    }), 200

@manage.route("/echart", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取图表信息", check_ip=True)
def getEchart():
    '''
    获取echart数据
    '''
    args = request.args  # 获取请求参数
    id = args.get("id", None)  # 获取表id
    if not id:
        return jsonify({
            "code": -1,
            "message": "缺少id参数"
        }), 400
    # 查询表是否存在
    table = db_session.query(Manage).filter(Manage.uuid == id).first()
    if not table:
        return jsonify({
            "code": -1,
            "message": "资产表不存在"
        }), 400
    # 查询规则
    rules = db_session.query(Echart).filter(Echart.table_name == id).order_by(Echart.id.asc()).all()
    if not rules:
        return jsonify({
            "code": -1,
            "message": "没有图表规则"
        }), 400
    result = []
    queryTable = initManageTable(table.table_name)
    for rule in rules:
        if rule.type == 1:  # 饼图
            pie_result = db_session.query(getattr(queryTable.c, rule.keyword), func.count(1)).group_by(getattr(queryTable.c, rule.keyword)).all()
            if pie_result:
                data = []
                for i in pie_result:
                    data.append({"value": i[1], "name": i[0]})
                result.append({
                    "title": {
                        "text": rule.name,
                        "left": "center"
                    },
                    "tooltip": {
                        "trigger": "item"
                    },
                    "legend": {
                        "orient": "vertical",
                        "left": "left"
                    },
                    "toolbox": {
                        "feature": {
                            "saveAsImage": {}
                        }
                    },
                    "series": [
                        {
                            "name": rule.name,
                            "type": "pie",
                            "radius": "50%",
                            "data": data,
                            "emphasis": {
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                                }
                            }
                        }
                    ]
                })
        if rule.type == 2:  # 柱形图
            bar_result = db_session.query(getattr(queryTable.c, rule.keyword), func.count(1)).group_by(getattr(queryTable.c, rule.keyword)).all()
            if bar_result:
                data_1 = []
                data_2 = []
                for i in pie_result:
                    data_1.append(i[0])
                    data_2.append(i[1])
                result.append({
                    "title": {
                        "text": rule.name
                    },
                    "xAxis": {
                        "type": "category",
                        "data": data_1
                    },
                    "yAxis": {
                        "type": "value"
                    },
                    "toolbox": {
                        "feature": {
                            "saveAsImage": {}
                        }
                    },
                    "series": [
                        {
                            "data": data_2,
                            "type": "bar"
                        }
                    ]
                })
        if rule.type == 3:  # 折线图
            # 根据日期排序
            data = []
            data.append({"name": "", "type": "line", "stack": "total", "data":[]})
            result.append({
                "title": {
                    "text": rule.name
                },
                "tooltip": {
                    "trigger": "axis"
                },
                "legend": {
                    "data": []
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "category",
                    "boundaryGap": False,
                    "data": []
                },
                "yAxis": {
                    "type": "value"
                },
                "toolbox": {
                    "feature": {
                        "saveAsImage": {}
                    }
                },
                "series": []
            })
    return jsonify({
        "code": 0,
        "message": result
    }), 200
