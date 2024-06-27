#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  manage.py
@Time    :  2024/04/26 13:53:24
@Version :  1.0
@Desc    :  资产管理模块
'''
import os
import io
import traceback
from flask import Blueprint, request, jsonify, g, Response, send_file, make_response
from app.utils import methods, crmLogger, readExcel, createExcel, UPLOAD_EXCEL_DIR, TEMP_DIR, SYSTEM_DEFAULT_TABLE, getUuid, verify, redisClient, converWords, job
from app.src.models import engine, db_session, Manage, Header, Log, Options, Echart, Task, File, DetectResult, Notify, initManageTable, generateManageTable
from sqlalchemy import or_, func, Column, String, Text, Date
from sqlalchemy.sql import insert
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
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
    reqData = request.get_json()                # 获取请求参数
    # 校验参数
    if not all(key in reqData for key in ["filename", "name", "keyword", "desc"]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    filename = reqData["filename"]              # excel文件名
    table_name = reqData["name"]                # 资产表标题
    table_keyword = reqData["keyword"].lower()  # 资产表别名
    table_desc = reqData["desc"]                # 资产表描述
    if not table_name or not table_keyword:
        return jsonify({"code": -1, "message": "表名或表别名不能为空"}), 400
    if table_keyword in SYSTEM_DEFAULT_TABLE:
        return jsonify({"code": -1, "message": "不能使用系统表表名"}), 400
    # 判断表是否已存在
    try:
        # 使用or查询
        is_exist_table = db_session.query(Manage).filter(or_(Manage.name == table_name, Manage.table_name == table_keyword)).first()
    finally:
        db_session.close()
    if is_exist_table:
        return jsonify({"code": -1, "message": "表名或表别名已存在"}), 400
    if filename:
        # 表格导入资产表方式
        try:
            file = db_session.query(File.affix).filter(File.uuid == filename).first()
        finally:
            db_session.close()
        if not file:
            return jsonify({
                "code": -1,
                "message": "导入的表格文件不存在"
            }), 400
        temp_table = readExcel(os.path.join(UPLOAD_EXCEL_DIR, f"{filename}.{file.affix}"))  # 读取表格
        if temp_table is None:
            return jsonify({
                "code": -1,
                "message": "读取表格失败"
            }), 200
        # 表头字段
        table_headers = temp_table.columns.tolist()
        if len(table_headers) == 0:
            crmLogger.error(f"读取表格文件{filename}失败: 原因: 表头读取为空")
            return jsonify({
                "code": -1,
                "message": "读取表格失败"
            }), 200
        column_header = converWords(table_headers)
        try:
            header_data = [Header(name=k, value=v["pinyin"], table_name=table_keyword, order=v["index"], create_user=g.username) for k, v in column_header.items()]
            db_session.add_all(header_data)
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入header表异常: {traceback.format_exc()}")
            return jsonify({
                "code": -1,
                "message": "数据库异常"
            }), 500
        finally:
            db_session.close()
        manageTable = generateManageTable(table_keyword, [Column(h["pinyin"], String(255)) for _, h in column_header.items()])  # 创建表
        try:
            table_uuid = getUuid()
            db_session.add(Manage(uuid=table_uuid, name=table_name, table_name=table_keyword, description=table_desc, create_user=g.username))
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入manage表异常: {traceback.format_exc()}")
            return jsonify({
                "code": -1,
                "message": "数据库异常"
            }), 500
        finally:
            db_session.close()
        try:
            # 批量插入数据
            with engine.connect() as conn:
                # 记录错误
                insert_data = temp_table.to_dict(orient="records")
                new_insert_data = []
                for i in insert_data:
                    for c, v in column_header.items():
                        new_data = i.pop(c)
                        if isinstance(new_data, datetime):
                            # 修改列属性为date
                            new_data = new_data.strftime("%Y-%m-%d %H:%M:%S")
                        i.update({v["pinyin"]: new_data})
                    new_insert_data.append(i)
                stmt = insert(manageTable)
                conn.execute(stmt, insert_data)
        except:
            crmLogger.error(f"写入{table_name}表异常: {traceback.format_exc()}")
            return jsonify({
                "code": -1,
                "message": "数据库异常"
            }), 500
    else:
        # 直接创建资产表,后面创建列方式
        initManageTable(table_keyword)
        try:
            table_uuid = getUuid()
            db_session.add(Manage(uuid=table_uuid, name=table_name, table_name=table_keyword, description=table_desc, create_user=g.username))
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入manage表异常: {traceback.format_exc()}")
            return jsonify({
                "code": -1,
                "message": "数据库异常"
            }), 500
        finally:
            db_session.close()
    try:
        create_log = Log(ip=g.ip_addr, operate_type="创建资产表", operate_content=f"创建资产表{table_name}", operate_user=g.username)
        db_session.add(create_log)
    except:
        db_session.rollback()
    finally:
        db_session.close()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    crmLogger.info(f"用户{g.username}创建资产表{table_name}成功")
    return jsonify({
        "code": 0,
        "message": table_uuid
    }), 200

@manage.route("/template", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="下载资产表模板", check_ip=True)
def downloadTemplate():
    '''
    下载资产表模板
    '''
    args = request.args        # 获取请求参数
    id = args.get("id", None)  # 获取表uuid
    try:
        table = db_session.query(Manage.name, Manage.table_name).filter(Manage.uuid == id).first()
    finally:
        db_session.close()
    # 查询的表不存在
    if not table:
        return jsonify({
            "code": -1,
            "message": "资产表不存在"
        }), 400
    # 如果redis有缓存,直接返回
    templ_file = redisClient.getData(f"crm:{id}:template")
    if templ_file:
        try:
            file = db_session.query(File.filename, File.affix).filter(File.uuid == templ_file).first()
        finally:
            db_session.close()
        with open(os.path.join(TEMP_DIR, f"{templ_file}.{file.affix}"), "rb") as f:
            file_binary = f.read()
        return send_file(io.BytesIO(file_binary), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, attachment_filename=f"{file.filename}")
    else:
        # 查询header
        try:
            header = db_session.query(Header.name, Header.type, Header.value, Header.value_type, Header.must_input, Header.order).filter(Header.table_name == table.table_name).order_by(Header.order.asc()).all()
        finally:
            db_session.close()
        if not header:
            return jsonify({
                "code": -1,
                "message": "资产表暂无字段"
            }), 400
        table_header = {}
        table_styles = {}
        for h in header:
            if h.must_input == 1:
                table_header[f"{h.name}*"] = chr(h.order + 65)
            else:
                table_header[f"{h.name}"] = chr(h.order + 65)
            if h.value_type == 2:
                try:
                    opt = db_session.query(Options.option_name, Options.option_value).filter(Options.table_name == table.table_name, Options.header_value == h.value).all()
                finally:
                    db_session.close()
                table_styles[f"{h.name}"] = {
                    "type": 2,
                    "options": ",".join([o.option_name for o in opt])
                }
        fileUuid = getUuid()
        if not createExcel(TEMP_DIR, fileUuid, "导入模板", table_header, {}, table_styles, True):
            return jsonify({
                "code": -1,
                "message": "创建模板文件失败"
            }), 500
        # 写入redis
        redisClient.setData(f"crm:{id}:template", fileUuid)
        # 写入file表
        try:
            db_session.add(File(uuid=fileUuid, filename=f"{table.name}导入模板.xlsx", affix="xlsx", filepath=0, upload_user="system"))
            db_session.commit()
        except:
            db_session.rollback()
        finally:
            db_session.close()
        crmLogger.info(f"生成资产表<{table.name}>导入模板文件完成")
        return send_file(os.path.join(TEMP_DIR, f"{fileUuid}.xlsx"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, attachment_filename=f"{table.name}导入模板.xlsx")  # 下载文件

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
@verify(allow_methods=["GET", "POST"], module_name="到期通知", check_ip=True)
def notifyExpire():
    '''
    到期通知
    '''
    if request.method == "GET":    # 获取所有通知
        args = request.args        # 获取请求参数
        id = args.get("id", None)  # 资产表id
        page = int(args.get("page", 1))    # 页码
        limit = int(args.get("limit", 5))  # 每页数量
        try:
            table = db_session.query(Manage).filter(Manage.uuid == id).first()
        finally:
            db_session.close()
        if not table:
            return jsonify({"code": -1, "message": "资产表不存在"}), 400
        try:
            count = db_session.query(Notify).filter(Notify.table == table.table_name, Notify.create_user == g.username).count()
            if count == 0:
                return jsonify({
                    "code": 0,
                    "message": []
                }), 200
            data = db_session.query(Notify).filter(Notify.table == table.table_name, Notify.create_user == g.username).order_by(Notify.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()
        return jsonify({
            "code": 0,
            "message": {
                "count": count,
                "data": [{"id": i.id, "name": i.name, "status": i.status, "create_time": i.create_time} for i in data]
            }
        }), 200
    elif request.method == "POST":
        reqData = request.get_json()   # 获取请求数据
        # 校验参数
        if not all(key in reqData for key in ["id", "task_id", "name", "operate"]):
            return jsonify({"code": -1, "message": "请求参数不完整"}), 400
        id = reqData["id"]              # 资产表id
        task_id = reqData["task_id"]    # 任务id
        name = reqData["name"]          # 任务名
        operate = reqData["operate"]    # 任务操作
        try:
            table = db_session.query(Manage).filter(Manage.uuid == id).first()
        finally:
            db_session.close()
        if not table:
            return jsonify({"code": -1, "message": "资产表不存在"}), 400
        try:
            # 查询是否已经存在通知
            if task_id:
                is_exist_notify = db_session.query(Notify).filter(Notify.id == task_id, Notify.status == 1,).first()
            else:
                is_exist_notify = db_session.query(Notify).filter(Notify.table == table.table_name, Notify.status == 1, Notify.create_user == g.username).first()
            if operate == "add":  # 新建通知
                if is_exist_notify:
                    return jsonify({"code": -1, "message": "该资产表已经存在通知"}), 400
                else:
                    # 创建定时任务
                    task_id = getUuid()
                    def getTaskFun(timeWord):
                        def fun():
                            # 查询过期数据
                            try:
                                today = datetime.now().strftime("%Y-%m-%d")  # 获取今天日期
                                expire_data = db_session.query().filter(NotifyMessage.expire_table == "crm_notify", NotifyMessage.expire_id == id).all()
                            finally:
                                db_session.close()
                            # 写入数据库
                            try:
                                db_session.commit()
                            except:
                                db_session.rollback()
                                crmLogger.error()
                            finally:
                                db_session.close()
                        return fun
                    try:
                        job.setJob(task_id, "00:00:00", getTaskFun())
                        
                    except:
                        pass
                    # 写入数据库
                    try:
                        add_log = Log()
                        db_session.add(add_log)
                        db_session.commit()
                    except:
                        db_session.rollback()
                    finally:
                        db_session.close()
                    crmLogger.info(f"{task_id}任务添加成功")
                    return jsonify({
                        "code": 0,
                        "message": "创建成功"
                    }), 200
            if operate == "stop":  # 停止通知
                if is_exist_notify:
                    pass
                else:
                    return jsonify({"code": 0, "message": "已停止通知"}), 200
        finally:
            db_session.close()  

@manage.route("/export", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="导出资产表", check_ip=True)
def export():
    '''
    导出资产表
    '''
    args = request.args  # 获取请求参数
    id = args.get("id")  # 资产表id
    # 
    redisClient.publish("export", {
        "id": id,
        "filter": "",
        "user": g.username
    })
    # sse推送进度
    # def event_stream():
    #     while True:
    #         yield ''
    # return Response(event_stream(), mimetype="text/event-stream")
    return jsonify({"code": 0}), 200

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
    args = request.args        # 获取请求参数
    id = args.get("id", None)  # 获取表id
    # 参数不存在
    if not id:
        return jsonify({
            "code": -1,
            "message": "缺少id参数"
        }), 400
    # 查询表是否存在
    table = db_session.query(Manage.table_name).filter(Manage.uuid == id).first()
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
