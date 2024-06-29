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
from flask import Blueprint, request, jsonify, g, Response, send_file, make_response
from app.utils import methods, crmLogger, readExcel, createExcel, UPLOAD_EXCEL_DIR, TEMP_DIR, SYSTEM_DEFAULT_TABLE, getUuid, verify, redisClient, converWords, job
from app.src.models import engine, db_session, Manage, Header, Log, Options, Echart, Task, File, DetectResult, Notify, initManageTable, generateManageTable
from sqlalchemy import or_, func, Column, String, Text, Date
from sqlalchemy.sql import insert
from datetime import datetime

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

    if title:  # 如果存在标题搜索

        try:
            count = db_session.query(Manage).filter(Manage.name.like("%{}%".format(title))).count()
        finally:
            db_session.close()

        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

        try:  # 模糊搜索结果,按最新创建的表格降序
            result = db_session.query(Manage).filter(Manage.name.like("%{}%".format(title))).order_by(Manage.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()

    else:  # 不存在标题搜索

        try:
            count = db_session.query(Manage).count()
        finally:
            db_session.close()

        if count == 0:
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

        try:
            result = db_session.query(Manage).order_by(Manage.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
        finally:
            db_session.close()

    try:  # 写入log表
        query_log = Log(ip=g.ip_addr, operate_type="查询资产表", operate_content=f"查询资产表,title={title}", operate_user=g.username)
        db_session.add(query_log)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    finally:
        db_session.close()

    crmLogger.info(f"用户{g.username}查询了资产表,title={title},page={page},limit={limit}")  # 写入日志文件

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
    args = request.args          # 获取请求参数

    title = args.get("k", None)  # 搜索关键字

    if title:  # 存在关键字搜索
        return jsonify({
            "code": 0,
            "message": [item.decode("utf-8") for item in redisClient.getSetData("crm:manage:table_name") if title in item.decode("utf-8")]  # 从redis中查询
        }), 200
    else:
        return jsonify({"code": 0, "message": []}), 200

@manage.route("/header", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询资产表字段", check_ip=True)
def getHeader():
    '''
    获取表格的头部字段
    '''
    args = request.args        # 获取请求参数

    id = args.get("id", None)  # 表格的uuid

    if not id:
        return jsonify({"code": -1, "message": "缺少id参数"}), 400

    try:  # 查看表是否存在
        table = db_session.query(Manage).filter(Manage.uuid == id).first()
    finally:
        db_session.close()

    if not table:
        return jsonify({"code": -1, "message": "资产表不存在"}), 400

    try:  # 查询数据,按order升序
        result = db_session.query(Header).filter(Header.table_name == table.table_name).order_by(Header.order.asc()).all()
    finally:
        db_session.close()

    if not result:  # 结果为空
        return jsonify({"code": 0, "message": []}), 200

    data = []
    for item in result:
        obj = {
            "field": item.value,                 # 值
            "title": item.name,                  # 标题
            "fieldTitle": item.name,             # 标题
            "type": item.type,                   # 类型
            "is_mark": bool(item.is_desence),    # 是否加密
            "must_input": bool(item.must_input)  # 是否必填
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

    return jsonify({"code": 0,"message": data}), 200

@manage.route("/<string:id>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询指定资产表", check_ip=True)
def queryTable(id):
    '''
    查找指定的资产表
    '''
    try:
        table = db_session.query(Manage).filter(Manage.uuid == id).first()  # 根据id查找资产表
    finally:
        db_session.close()

    if not table:  # 表不存在
        return jsonify({"code": -1, "message": "资产表不存在"}), 400

    args = request.args                        # 获取请求参数
    page = int(args.get("page", default=1))    # 当前页码,默认第一页
    limit = int(args.get("limit", default=6))  # 每页显示数量,默认6条

    try:
        columns = db_session.query(Header.value).filter(Header.table_name == table.table_name).all()  # 获取表头信息,所有列
    finally:
        db_session.close()

    if not columns:  # 如果没有表头信息,则返回空列表
        return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

    # 根据用户搜索关键字返回数据
    key = args.get("key", None)      # 用户查找的字段
    value = args.get("value", None)  # 用户查找的值

    queryTable = initManageTable(table.table_name)  # 实例化已存在资产表

    if key and value:  # 如果存在关键字搜索,模糊搜索

        try:
            count = db_session.query(queryTable).filter((getattr(queryTable.c, key).like(f"%{value}%"))).count()
        finally:
            db_session.close()

        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

        result = db_session.query(queryTable).filter((getattr(queryTable.c, key).like(f"%{value}%"))).order_by(queryTable.c._id.desc()).offset((page - 1) * limit).limit(limit).all()
    
    else:

        try:
            count = db_session.query(queryTable).count()
        finally:
            db_session.close()

        if count == 0:
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

        result = db_session.query(queryTable).order_by(queryTable.c._id.desc()).offset((page - 1) * limit).limit(limit).all()

    data = []
    for item in result:
        obj = {}
        obj["_id"] = item._id
        for col in columns:
            obj[col.value] = getattr(item, col.value)  # 获取对应属性值
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

    if not all(key in reqData for key in ["filename", "name", "keyword", "desc"]):  # 校验参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    filename = reqData["filename"]              # excel文件名
    table_name = reqData["name"]                # 资产表标题
    table_keyword = reqData["keyword"].lower()  # 资产表别名
    table_desc = reqData["desc"]                # 资产表描述

    if not table_name or not table_keyword:
        return jsonify({"code": -1, "message": "表名或表别名不能为空"}), 400

    if table_keyword in SYSTEM_DEFAULT_TABLE:
        return jsonify({"code": -1, "message": "不能使用系统表表名"}), 400

    try:  # 判断表是否已存在,使用or查询
        is_exist_table = db_session.query(Manage).filter(or_(Manage.name == table_name, Manage.table_name == table_keyword)).first()
    finally:
        db_session.close()

    if is_exist_table:  # 如果已经存在资产表
        return jsonify({"code": -1, "message": "表名或表别名已存在"}), 400

    if filename:  # 表格导入资产表方式

        try:
            file = db_session.query(File.affix).filter(File.uuid == filename).first()  # 根据文件id查询文件
        finally:
            db_session.close()

        if not file:
            return jsonify({"code": -1, "message": "导入的表格文件不存在"}), 400

        temp_table = readExcel(os.path.join(UPLOAD_EXCEL_DIR, f"{filename}.{file.affix}"))  # 读取表格

        if temp_table is None:
            return jsonify({"code": -1, "message": "读取表格失败"}), 400

        table_headers = temp_table.columns.tolist()  # 表头字段

        if len(table_headers) == 0:
            crmLogger.error(f"读取表格文件{filename}失败: 原因: 表头读取为空")
            return jsonify({"code": -1, "message": "读取表格失败"}), 400

        column_header = converWords(table_headers)  # 中文拼音转换

        try:  # 批量插入表头数据
            header_data = [Header(name=k, value=v["pinyin"], table_name=table_keyword, order=v["index"], create_user=g.username) for k, v in column_header.items()]
            db_session.add_all(header_data)
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入header表异常: {traceback.format_exc()}")
            return jsonify({"code": -1, "message": "数据库异常"}), 500
        finally:
            db_session.close()

        manageTable = generateManageTable(table_keyword, [Column(h["pinyin"], String(255)) for _, h in column_header.items()])  # 创建资产表
        
        if manageTable is None:
            return jsonify({"code": -1, "message": "创建资产表失败"}), 400

        table_uuid = getUuid()
        try:  # 写入manage表
            db_session.add(Manage(uuid=table_uuid, name=table_name, table_name=table_keyword, description=table_desc, create_user=g.username))
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入manage表异常: {traceback.format_exc()}")
            return jsonify({"code": -1,"message": "数据库异常"}), 500
        finally:
            db_session.close()

        try:  # 批量插入数据
            with engine.begin() as conn:  # 开启事务
                insert_data = temp_table.to_dict(orient="records")  # 转换成[{k1: v1, k2: v2...}]
                for i in insert_data:
                    for c, v in column_header.items():
                        new_data = i.pop(c)
                        if isinstance(new_data, datetime):  # 如果数据格式是时间,格式化为字符串
                            new_data = new_data.strftime("%Y-%m-%d %H:%M:%S")
                        i.update({v["pinyin"]: new_data})  # 将中文k1更新为拼音
                stmt = insert(manageTable)
                conn.execute(stmt, insert_data)
        except:
            crmLogger.error(f"写入{table_name}表异常: {traceback.format_exc()}")
            return jsonify({"code": -1,"message": "数据库异常"}), 500
    else:  # 直接创建资产表,后面创建列方式
        manageTable = generateManageTable(table_keyword)

        if manageTable is None:
            return jsonify({"code": -1, "message": "创建资产表失败"}), 400

        table_uuid = getUuid()
        try:  # 写入manage表
            db_session.add(Manage(uuid=table_uuid, name=table_name, table_name=table_keyword, description=table_desc, create_user=g.username))
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入manage表异常: {traceback.format_exc()}")
            return jsonify({"code": -1, "message": "数据库异常"}), 500
        finally:
            db_session.close()

    try:  # 写入log表
        create_log = Log(ip=g.ip_addr, operate_type="创建资产表", operate_content=f"创建资产表{table_name}", operate_user=g.username)
        db_session.add(create_log)
    except:
        db_session.rollback()
        crmLogger.error(f"写入log表异常: {traceback.format_exc()}")
    finally:
        db_session.close()
     
    crmLogger.info(f"用户{g.username}创建资产表{table_name}成功")  # 日志文件记录

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

    if not id:
        return jsonify({"code": -1, "message": "缺少id参数"}), 400

    try:
        table = db_session.query(Manage.name, Manage.table_name).filter(Manage.uuid == id).first()
    finally:
        db_session.close()

    if not table:  # 查询的表不存在
        return jsonify({"code": -1, "message": "资产表不存在"}), 400

    templ_file = redisClient.getData(f"crm:{id}:template")  # 如果redis有缓存,直接返回

    if templ_file:

        try:
            file = db_session.query(File.filename, File.affix).filter(File.uuid == templ_file).first()
        finally:
            db_session.close()

        return send_file(os.path.join(TEMP_DIR, f"{templ_file}.{file.affix}"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, attachment_filename=f"{file.filename}")
   
    else:  # 缓存不存在则创建模板文件

        try:  # 查询header
            header = db_session.query(Header.name, Header.type, Header.value, Header.value_type, Header.must_input, Header.order).filter(Header.table_name == table.table_name).order_by(Header.order.asc()).all()
        finally:
            db_session.close()

        if not header:
            return jsonify({"code": -1, "message": "资产表暂无字段"}), 400

        table_header = {}
        table_styles = {}
        for h in header:
            if h.must_input == 1:
                table_header[f"{h.name}*"] = chr(h.order + 65)  # 转换成大写字母
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
            return jsonify({"code": -1, "message": "创建模板文件失败"}), 500

        redisClient.setData(f"crm:{id}:template", fileUuid)   # 写入redis

        try:  # 写入file表
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
    reqData = request.get_json()  # 获取请求数据

    # 校验body参数
    if not all(key in reqData for key in ["file_uuid", "table_id"]):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400

    file_uuid = reqData["file_uuid"]    # 获取上传的文件uuid
    table_id = reqData["table_id"]      # 获取导入的资产表id

    try:  # 查询资产表是否存在
        table = db_session.query(Manage.table_name).filter(Manage.uuid == table_id).first()
    finally:
        db_session.close()  # 关闭数据库连接

    if not table:  # 资产表不存在
        return jsonify({"code": -1, "message": "资产表不存在"}), 400
    
    try:  # 查询文件是否存在
        file = db_session.query(File.affix).filter(File.uuid == file_uuid).first()
    finally:
        db_session.close()  # 关闭数据库连接
    
    if not file:  # 文件不存在
        return jsonify({"code": -1, "message": "导入的文件不存在"}), 400
    
    temp_table = readExcel(os.path.join(UPLOAD_EXCEL_DIR, f"{file_uuid}.{file.affix}"))  # 读取表格

    if temp_table is None:  # 读取失败
        return jsonify({"code": -1, "message": "读取导入表格失败"}), 400

    table_headers = temp_table.columns.tolist()  # 获取表头字段

    if len(table_headers) == 0:  # 表头为空
        return jsonify({"code": -1, "message": "读取导入表格失败"}), 400
    
    try:  # 查询数据中表头的记录
        templ_header = db_session.query(Header.name, Header.value, Header.type, Header.must_input).filter(Header.table_name == table.table_name).all()
    finally:
        db_session.close()  # 关闭数据库连接

    # 读取文件的header和数据库中比对是否一致,不一致说明不是使用模板导入
    if [h.name for h in templ_header].sort() != table_headers.sort():  # 排序后比较
        return jsonify({"code": -1, "message": "导入失败,请使用模板导入"}), 400

    manageTable = initManageTable(table.table_name)  # 实例化已存在的资产表

    # 校验数据是否唯一,有重复导入

    # 校验数据是否从下拉列表选项中值

    # 如果是时间,判断是否是datetime类型,否则进行转换
    
    try:
        with engine.begin() as conn:  # 开启事务,批量插入数据
            insert_data = temp_table.to_dict(orient="records")
            stmt = insert(manageTable)
            conn.execute(stmt, insert_data)
    except:
        return jsonify({"code": -1, "message": f"写入{table.name}数据库异常"}), 500

    return jsonify({"code": 0, "message": "导入数据成功"}), 200


@manage.route("/edit", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改资产表数据", check_ip=True)
def editData():
    '''
    修改资产表数据
    '''
    reqData = request.get_json()  # 获取请求数据

    if "table_id" not in reqData or "id" not in reqData:  # 获取id失败
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    id = reqData["table_id"]

    try:
        table = db_session.query(Manage.table_name).filter(Manage.uuid == id).first()
    finally:
        db_session.close()
    
    if not table:  # 资产表不存在
        return jsonify({"code": -1, "message": "资产表不存在"}), 400

    try:  # 从数据库中查询对应表的header信息
        header = db_session.query(Header).filter(Header.table_name == table.table_name).all()
    finally:
        db_session.close()

    must_exist_header = [h.value for h in header if h.must_input == 1]  # 必填字段

    # 校验参数
    if not all(key in reqData for key in must_exist_header):
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    manageTable = initManageTable(table.table_name)  # 实例化已存在资产表

    # 校验是否唯一的数值

    # 校验是否从下拉列表中的值

    try:
        data = db_session.query(manageTable).filter(getattr(manageTable.c, id) == reqData["id"]).first()  # 根据行id筛选数据
        if data:

            # 更新信息
            setattr(data, id, reqData["id"])
            db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"修改资产表数据失败")
    finally:
        db_session.close()

    return jsonify({"code": 0, "message": "修改成功"}), 200

@manage.route("/alter", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改列属性", check_ip=True)
def alterColumn():
    '''
    修改资产表列信息
    '''
    reqData = request.get_json()

    # 如何列名修改则更新header表

    # 如果列属性修改则更新对应表列属性

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

    id = args.get("id", None)          # 资产表id
    filter = args.get("filter", None)  # 筛选条件

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

@manage.route("/rule", methods=methods.ALL)
@verify(allow_methods=["GET", "POST"], module_name="创建图表规则", check_ip=True)
def setEchartRule():
    '''
    创建图表规则
    '''
    if request.method == "GET":  # 查询图表规则
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
    elif request.method == "POST":  # 创建图表规则
        userData = request.get_json()  # 用户的请求body数据
        table_name = userData["table_name"]  # 表名
        keyword = userData["keyword"]  # 关键字
        type = userData["type"]  # 图表类型
        config = userData["config"]  # 图表配置
        #创建图表规则

@manage.route("/echart", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="获取图表信息", check_ip=True)
def getEchart():
    '''
    获取echart数据
    '''
    args = request.args        # 获取请求参数

    id = args.get("id", None)  # 获取表id

    if not id:  # 参数不存在
        return jsonify({"code": -1, "message": "缺少id参数"}), 400
    
    try:  # 查询表是否存在
        table = db_session.query(Manage.table_name).filter(Manage.uuid == id).first()
    finally:
        db_session.close()

    if not table:
        return jsonify({"code": -1, "message": "资产表不存在"}), 400
    
    try:  # 查询规则
        rules = db_session.query(Echart).filter(Echart.table_name == id).order_by(Echart.id.asc()).all()
    finally:
        db_session.close()

    if not rules:
        return jsonify({"code": 0, "message": [] }), 200

    result = []

    queryTable = initManageTable(table.table_name)  # 实例化已存在资产表

    for rule in rules:
        if rule.type == 1:  # 饼图

            try:
                pie_result = db_session.query(getattr(queryTable.c, rule.keyword), func.count(1)).group_by(getattr(queryTable.c, rule.keyword)).all()
            finally:
                db_session.close()
            
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

        elif rule.type == 2:  # 柱形图

            try:
                bar_result = db_session.query(getattr(queryTable.c, rule.keyword), func.count(1)).group_by(getattr(queryTable.c, rule.keyword)).all()
            finally:
                db_session.close()

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

        elif rule.type == 3:  # 折线图
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

    return jsonify({"code": 0, "message": result}), 200
