#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  manage.py
@Time    :  2024/04/26 13:53:24
@Version :  1.0
@Desc    :  资产管理模块
'''
import os
import re
import time
import json
import traceback
from flask import Blueprint, request, jsonify, g, Response, send_file
from app.utils import UPLOAD_EXCEL_DIR, TEMP_DIR, SYSTEM_DEFAULT_TABLE, methods, crmLogger, readExcel, createExcel, getUuid, verify, redisClient, converWords, job, undesense
from app.src.models import engine, db_session, Manage, Header, Log, Options, Echart, Task, File, DetectResult, Notify, initManageTable, generateManageTable, addColumn, alterColumn, MyHeader
from app.src.task import exportTableTask
from sqlalchemy import or_, func, Column, String, Text, Date
from sqlalchemy.sql import insert
from datetime import datetime, date

manage = Blueprint("manage", __name__)

@manage.route("/query", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询资产表", check_ip=True)
def queryTable():
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

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

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
def queryTableTitle():
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
def getTableHeader():
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
    
    result = redisClient.getData(f"crm:header:{table.table_name}")

    if result:

        result = [MyHeader(i) for i in json.loads(result)]

    else:

        try:  # 查询数据,按order升序

            result = db_session.query(Header).filter(Header.table_name == table.table_name).order_by(Header.order.asc()).all()

            if result:
                _h = [
                    {c.name: getattr(u, c.name) for c in u.__table__.columns if c.name not in ["create_user", "create_time", "update_user", "update_time"]} for u in result
                ]
                redisClient.setHashData(f"crm:header:{table.table_name}", json.dumps(_h))  # 写入缓存

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
            obj["templet"] = "<select><option value=''>请选择</option>" + _templ + "</select>"  # layui table的templet模板
        
        data.append(obj)

    return jsonify({"code": 0,"message": data}), 200

@manage.route("/<string:id>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询指定资产表", check_ip=True)
def queryTableByUuid(id):
    '''
    查找指定的资产表
    '''
    try:

        table = db_session.query(Manage.table_name).filter(Manage.uuid == id).first()  # 根据id查找资产表

    finally:

        db_session.close()

    if not table:  # 表不存在
        return jsonify({"code": -1, "message": "资产表不存在"}), 400

    args = request.args                        # 获取请求参数
    page = int(args.get("page", default=1))    # 当前页码,默认第一页
    limit = int(args.get("limit", default=6))  # 每页显示数量,默认6条

    columns = redisClient.getData(f"crm:header:{table.table_name}")

    if columns:
        columns = [MyHeader(i) for i in json.loads(columns)]
    
    else:

        try:

            columns = db_session.query(Header.value, Header.is_desence).filter(Header.table_name == table.table_name).all()  # 获取表头信息,所有列

        finally:

            db_session.close()

    if not columns:  # 如果没有表头信息,则返回空列表
        return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

    # 根据用户搜索关键字返回数据
    key = args.get("key", None)      # 用户查找的字段
    value = args.get("value", None)  # 用户查找的值

    manageTable = initManageTable(table.table_name)  # 实例化已存在资产表

    if key and value:  # 如果存在关键字搜索,模糊搜索

        try:
            count = db_session.query(manageTable).filter((getattr(manageTable.c, key).like(f"%{value}%"))).count()

        finally:

            db_session.close()

        if count == 0:  # 如果没有搜索到结果,直接返回空列表
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

        result = db_session.query(manageTable).filter((getattr(manageTable.c, key).like(f"%{value}%"))).order_by(manageTable.c._id.desc()).offset((page - 1) * limit).limit(limit).all()
    
    else:

        try:

            count = db_session.query(manageTable).count()

        finally:

            db_session.close()

        if count == 0:
            return jsonify({"code": 0, "message": {"total": 0, "data": []}}), 200

        result = db_session.query(manageTable).order_by(manageTable.c._id.desc()).offset((page - 1) * limit).limit(limit).all()

    data = []
    for item in result:
        obj = {}
        obj["_id"] = item._id
        for col in columns:
            if bool(col.is_desence):  # 数据脱敏展示
                obj[col.value] = undesense(getattr(item, col.value))
            else:
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
def addTableData():
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

            crmLogger.error(f"写入header表发生异常: {traceback.format_exc()}")

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

            crmLogger.error(f"写入manage表发生异常: {traceback.format_exc()}")

            return jsonify({"code": -1,"message": "数据库异常"}), 500
        
        finally:

            db_session.close()

        try:  # 批量插入数据

            with engine.begin() as conn:  # 开启事务
                insert_data = temp_table.to_dict(orient="records")  # 转换成[{k1: v1, k2: v2...}]
                for i in insert_data:
                    for c, v in column_header.items():
                        new_data = i.pop(c)  # c-中文字段名
                        if isinstance(new_data, datetime):  # 如果数据格式是时间,格式化为字符串
                            new_data = new_data.strftime("%Y-%m-%d %H:%M:%S")
                        elif isinstance(new_data, date):    # 如果数据格式是日期,格式化为字符串
                            new_data = new_data.strftime("%Y-%m-%d")
                        i.update({v["pinyin"]: new_data})   # 将中文k1更新为拼音
                stmt = insert(manageTable)
                conn.execute(stmt, insert_data)

        except:

            crmLogger.error(f"写入{table_name}表发生异常: {traceback.format_exc()}")

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

            crmLogger.error(f"写入manage表发生异常: {traceback.format_exc()}")

            return jsonify({"code": -1, "message": "数据库异常"}), 500
        
        finally:

            db_session.close()

    try:  # 写入log表

        create_log = Log(ip=g.ip_addr, operate_type="创建资产表", operate_content=f"创建资产表{table_name}", operate_user=g.username)
        db_session.add(create_log)

    except:

        db_session.rollback()

        crmLogger.error(f"写入log表发生异常: {traceback.format_exc()}")

    finally:

        db_session.close()

    redisClient.setSet("crm:manage:table_name", table_name)  # 将标题写入缓存
     
    crmLogger.info(f"用户{g.username}创建资产表{table_name}成功")  # 日志文件记录

    return jsonify({
        "code": 0,
        "message": table_uuid
    }), 200

@manage.route("/template", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="下载资产表模板", check_ip=True)
def downloadTableTemplate():
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

        header = redisClient.getData(f"crm:header:{table.table_name}")

        if header:
            header = [MyHeader[i] for i in header]

        else:

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

            if h.value_type == 2:  # 如果是下拉列表

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

        return jsonify({"code": 0, "message": fileUuid}), 200

@manage.route("/import", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="导入资产表数据", check_ip=True)
def importTableFromExcel():
    '''
    导入资产表
    '''
    reqData = request.get_json()  # 获取请求数据

    if not all(key in reqData for key in ["file_uuid", "table_id"]):  # 校验body参数
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

    if temp_table is None:  # 读取表格失败
        return jsonify({"code": -1, "message": "读取导入表格失败"}), 400

    table_headers = temp_table.columns.tolist()  # 获取表头字段

    if len(table_headers) == 0:  # 表头为空
        return jsonify({"code": -1, "message": "读取导入表格失败"}), 400
    
    templ_header = redisClient.getData(f"crm:header:{table.table_name}")

    if templ_header:
        templ_header = [MyHeader[i] for i in templ_header]

    else:
    
        try:  # 查询数据中表头的记录

            templ_header = db_session.query(Header.name, Header.value, Header.value_type, Header.type, Header.must_input, Header.is_unique).filter(Header.table_name == table.table_name).all()
        
        finally:

            db_session.close()  # 关闭数据库连接

    # 读取文件的header和数据库中比对是否一致,不一致说明不是使用模板导入
    if [h.name for h in templ_header].sort() != list(map(lambda x: x.rsplit("*", 1)[0] if x.endswitch("*") else x, table_headers)).sort():  # 排序后比较
        return jsonify({"code": -1, "message": "导入失败,请使用模板导入"}), 400

    manageTable = initManageTable(table.table_name)  # 实例化已存在的资产表

    # 判断必填值列是否有空值
    must_header = [h.name for h in templ_header if h.must_input == 1]

    for h in must_header:

        if temp_table[f"{h}*"].isnull().any():  # 判断是否有空值,带*表示必填
            return jsonify({"code": -1, "message": f"导入失败,{h}字段在表格中存在空值"}), 400

    # 校验数据是否唯一,有重复导入
    unique_header = [h.name for h in templ_header if h.is_unique == 1]

    for h in unique_header:

        if temp_table["h"].duplicated().any():  # 判断是否有重复数据
            return jsonify({"code": -1, "message": f"导入失败,{h}字段在表格中有重复数据"}), 400
        
        try:

            col_data = db_session.query(getattr(manageTable.c, h.value)).all()

        finally:

            db_session.close()

        if temp_table[h].isin(col_data).any():  # 判断是否有重复数据
            return jsonify({"code": -1, "message": f"导入失败,{h}字段在数据库中有重复数据"}), 400

    # 校验数据是否从下拉列表选项中值
    _temp_opts = {}
    for h in templ_header:

        if h.type == 2:

            try:

                _opt = db_session.query(Options.option_name, Options.option_value).filter(Options.table_name == table.table_name, Options.header_value == h.value).all()
            
            finally:

                db_session.close()

            if not temp_table[h.name].isin([o.option_name for o in _opt]):
                return jsonify({"code": -1, "message": f"导入失败,{h.name}字段在表格中存在非固定选项值"}), 400
            
            for o in _opt:
                _temp_opts[o.option_name] = o.option_value

        if h.value_type == 2:  # 如果要求值是定长字符串

            if len(temp_table[temp_table[h.name].str.len() != h.length]) > 0:
                return jsonify({"code": -1, "message": f"导入失败,{h.name}字段在表格中存在不满足长度的值"}), 400

    insert_data = temp_table.to_dict(orient="records")
    for i in insert_data:
        for c in templ_header:
            new_data = i.pop(c.name)
            # 如果是时间,判断是否是datetime类型,否则进行转换
            i.update({c.value: new_data})
    
    try:

        with engine.begin() as conn:  # 开启事务,批量插入数据        
            stmt = insert(manageTable)
            conn.execute(stmt, insert_data)

    except:

        return jsonify({"code": -1, "message": f"写入{table.name}数据库异常"}), 500

    return jsonify({"code": 0, "message": "导入数据成功"}), 200

@manage.route("/edit", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改资产表数据", check_ip=True)
def editTableData():
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

@manage.route("/alter_column", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="修改列属性", check_ip=True)
def alterTableColumn():
    '''
    修改资产表列信息
    '''
    reqData = request.get_json()

    if not all(key in reqData for key in ["id", "name", "type", "options"]):   # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    try:
        table = db_session.query(Manage.table_name).filter(Manage.uuid == reqData["id"]).first()
    finally:
        db_session.close()

    try:  # 先查询出对应header信息
        curr_header = db_session.query(Header).filter(Header.uuid == reqData["id"]).first()
    finally:
        db_session.close()

    try:  # 如何列名修改则更新header表
        curr_header.name = reqData["name"]
        db_session.commit()
    except:
        db_session.rollback()
        return jsonify({"code": -1, "message": "数据库异常"}), 500
    finally:
        db_session.close()

    manageTable = initManageTable(table.table_name)

    # 如果将列设置为必填,查询此列是否存在空值
    try:
        is_exist_null = db_session.query(manageTable).filter(getattr(manageTable.c, reqData["id"]) == None).all()
    finally:
        db_session.close()

    if len(is_exist_null) > 0:  # 如果存在空值则不允许修改
        return jsonify({"code": -1, "message": "存在空值,不允许修改"}), 400
    
    # 如果将列值设置为唯一,查询此列是否存在重复值
    try:
        is_exist_duplicate = db_session.query(getattr(manageTable.c, "xx"), func.count(getattr(manageTable.c, "xx")).label("count")).group_by(getattr(manageTable.c, "xx")).having(func.count(getattr(manageTable.c, "xx")) > 1).all()
    finally:
        db_session.close()

    if len(is_exist_duplicate) > 0:
        return jsonify({"code": -1, "message": "存在重复值,不允许修改"}), 400

    # 如果设置列值长度为固定长度,查询此列数据长度是否满足要求
    try:
        is_exist_unlength = db_session.query(func.count()).filter(func.length(getattr(manageTable.c, "xx")) != 13).scalar()
    finally:
        db_session.close()

    if is_exist_unlength > 0:  # 如果存在不满足长度的值则不允许修改
        return jsonify({"code": -1, "message": "存在不满足长度的值,不允许修改"}), 400

    # 校验列数据是否可以被转换为时间
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')

    # 首先查询此列中所有不为空的数据
    try:
        query_sql = f"SELECT {} FROM {} WHERE {} IS NOT NULL"
        query_data = db_session.execute(query_sql).fetchall()
    finally:
        db_session.close()

    for row in query_data:
        if not(bool(date_pattern.match(row[0]) or bool(datetime_pattern.match(row[0])))):
            return jsonify({"code": -1, "message": "存在时间格式错误,不允许修改"}), 400

    # 如果列属性修改则更新对应表列属性
    # 固定长度
    # f"VARCHAR({length})"
    if not alterColumn(table.table_name, reqData["id"], reqData["type"]):
        return jsonify({"code": -1, "message": "修改失败"}), 400
    
    # 如果修改列是从下拉列表取值
    # 先判断是否存在列表

    # 不存在则报错

    # 存在则判断数据是否取值与下拉列表中

    try:
        not in [下拉列表]
    finally:
        db_session.close()

    # 校验通过后更新值或者修改列属性

    try:  # 如果type是下拉列表则更新option表
        _opt = db_session.query(Options).filter(Options.header_uuid == curr_header.uuid).all()
        if _opt:  # 如果有option则删除
            db_session.delete(_opt)
            db_session.commit()
    except:
        db_session.rollback()
        return jsonify({"code": -1, "message": "数据库异常"}), 500
    finally:
        db_session.close()
        
    return jsonify({"code": 0, "message": "修改成功"}), 200

@manage.route("/add_clumn", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="添加列", check_ip=True)
def addTableColumn():
    '''
    添加资产表列
    '''
    reqData = request.get_json()

    if not all(key in reqData for key in ["id", "name", "type", "options"]):   # 校验body参数
        return jsonify({"code": -1, "message": "请求参数不完整"}), 400
    
    if not addColumn(reqData["id"], reqData["name"], reqData["type"], reqData["options"]):  # 添加列
        return jsonify({"code": -1, "message": "添加失败"}), 400
    
    # 判断新增的列是否有重复

    # 不存在重复则创建列
    
    return jsonify({"code": 0, "message": "添加成功"}), 200

@manage.route("/ping", methods=methods.ALL)
@verify(allow_methods=["POST"], module_name="ping探测", check_ip=True)
def multDetectHost():
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
    
    return jsonify({"code": 0, "message": "xx"}), 200

@manage.route("/notify", methods=methods.ALL)
@verify(allow_methods=["GET", "POST"], module_name="到期通知", check_ip=True)
def notifyExpireData():
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
                                # expire_data = db_session.query().filter(NotifyMessage.expire_table == "crm_notify", NotifyMessage.expire_id == id).all()
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

    if not id:  # 如果请求参数没有资产表id
        return jsonify({"code": -1, "message": "缺少id参数"}), 400
    
    try:  # 查询是否存在资产表
        table = db_session.query(Manage.name, Manage.table_image).filter(Manage.uuid == id).first()
    finally:
        db_session.close()

    if not table:  # 如果资产表不存在
        return jsonify({"code": -1, "message": "资产表不存在"}), 400

    task_id = getUuid()  # 任务id

    # 将任务条件到队列
    redisClient.lpush("crm:task:export", json.dumps({
        "table_id": id,
        "table_name": table.table_name,
        "task_id": task_id,
        "filter": filter,
        "user": g.username
    }))

    exportTableTask()

    return jsonify({"code": 0, "message": task_id}), 200

@manage.route("/process/<string:task_id>", methods=methods.ALL)
@verify(allow_methods=["GET"], module_name="查询任务进度", check_ip=True)
def progress(task_id):
    '''
    查询任务进度
    '''
    # sse推送进度
    def event_stream():
        while True:
            time.sleep(0.3)
            data = redisClient.getData(f"crm:task:{task_id}")  # done:total
            if not data:
                yield "speed: 0\n\n"
                continue
            done, total = map(int, data.split(":"))
            rate = (done / total) * 100
            if rate >= 100:
                yield "speed: 100\n\n"
                break
            yield f"speed: {rate}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

@manage.route("/rule", methods=methods.ALL)
@verify(allow_methods=["GET", "POST"], module_name="获取或创建图表规则", check_ip=True)
def setEchartRule():
    '''
    或者或创建图表规则
    '''
    if request.method == "GET":    # 查询图表规则

        args = request.args        # 获取请求参数

        id = args.get("id", None)  # 获取表id
        
        if not id:
            return jsonify({"code": -1, "message": "缺少id参数"}), 400
        
        try:  # 查询资产表表是否存在
            table = db_session.query(Manage.table_name).filter(Manage.uuid == id).first()
        finally:
            db_session.close()

        if not table:  # 资产表不存在
            return jsonify({"code": -1, "message": "资产表不存在"}), 400

        try:  # 查询规则,升序
            rules = db_session.query(Echart).filter(Echart.table_name == id).order_by(Echart.id.asc()).all()
        finally:
            db_session.close()

        if not rules:  # 查无规则
            return jsonify({"code": 0, "message": []}), 200

        return jsonify({
            "code": 0,
            "message": [{"id": rule.id, "type": rule.type, "keyword": rule.keyword} for rule in rules]
        }), 200

    elif request.method == "POST":  # 创建图表规则

        reqData = request.get_json()  # 获取请求数据

        if not all(key in reqData for key in ["id", "task_id", "name", "operate"]):  # 校验body参数
            return jsonify({"code": -1, "message": "请求参数不完整"}), 400

        name = reqData["name"]  # 名称
        table_name = reqData["table_name"]  # 表名
        keyword = reqData["keyword"]  # 关键字
        type = reqData["type"]  # 图表类型
        config = reqData["config"]  # 图表配置
        
        try:  # 先删除规则
            db_session.query(Echart).filter(Echart.table_name == reqData["id"]).delete()
            db_session.commit()
        except:
            db_session.rollback()
            return jsonify({"code": -1, "message": "数据库异常"}), 500
        finally:
            db_session.close()

        try:  # 再创建规则
            db_session.add_all()
            db_session.commit()
        except:
            db_session.rollback()
            return jsonify({"code": -1, "message": "数据库异常"}), 500
        finally:
            db_session.close()

        return jsonify({"code": 0, "message": "创建成功"}), 200

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
    
    # 从缓存中查询

    # 缓存不存在
    
    try:  # 查询规则
        rules = db_session.query(Echart).filter(Echart.table_name == id).order_by(Echart.id.asc()).all()
    finally:
        db_session.close()

    if not rules:
        return jsonify({"code": 0, "message": [] }), 200

    result = []

    manageTable = initManageTable(table.table_name)  # 实例化已存在资产表

    for rule in rules:
        if rule.type == 1:  # 饼图

            try:
                pie_result = db_session.query(getattr(manageTable.c, rule.keyword), func.count(1)).group_by(getattr(manageTable.c, rule.keyword)).all()
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
                bar_result = db_session.query(getattr(manageTable.c, rule.keyword), func.count(1)).group_by(getattr(manageTable.c, rule.keyword)).all()
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

            try:  # # 根据日期排序
                line_result = db_session.query(getattr(manageTable.c, rule.keyword), func.count(1)).group_by(getattr(manageTable.c, rule.keyword)).all()
            finally:
                db_session.close()

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

    # 将结果写入缓存

    return jsonify({"code": 0, "message": result}), 200
