#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  task.py
@Time    :  2024/06/29 22:20:49
@Version :  1.0
@Desc    :  任务模块
'''
import os
import json
import traceback
from datetime import datetime, date
from app.utils import TEMP_DIR, UPLOAD_EXCEL_DIR, redisClient, crmLogger, createExcel, readExcel, scan_ip, getUuid
from app.src.models import engine, db_session, Task, Notice, History, Header, Options, File, initManageTable, MyHeader
from sqlalchemy import and_, insert
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial

def notifyTask(task_id: str, name: str, table_name: str, keyword: str):
    '''
    通知任务
    :param task_id: 任务id
    :param name: 表名
    :param table_name: 表别名
    :param keyword: 日期字段
    '''
    manageTable = initManageTable(table_name)  # 实例化已存在资产表

    try:  # 查询过期数据数量
        today = datetime.now().strftime("%Y-%m-%d")  # 获取今天日期
        expire_data = db_session.query(manageTable).filter(and_(f"{today} 00:00:00" <= getattr(manageTable.c, keyword), getattr(manageTable.c, keyword) <= f"{today} 23:59:59")).count()
    finally:
        db_session.close
        
    if expire_data > 0:
        try:  # 写入数据库
            notice_data = Notice(message="{}资产表有{}条数据已过期".format(name, expire_data), notify_id=task_id)
            db_session.add(notice_data)
            db_session.commit()
        except:
            db_session.rollback()
            crmLogger.error(f"写入notice表发生异常: {traceback.format_exc()}")
        finally:
            db_session.close()

def writeError(task_id: str, error: str) -> bool:
    '''
    写入错误信息
    :param task_id: 任务id
    :param error: 错误信息
    :return:
    '''
    filename = getUuid()
    filepath = os.path.join(TEMP_DIR, f"{filename}.txt")

    with open(filepath, "w", encoding="utf-8") as f:  # 创建错误文件
        f.write(error)

    try:  # 插入file表
        err_file = File(uuid=filename, filename="错误信息.txt", filepath=0, affix="txt")
        db_session.add(err_file)
        db_session.commit()
    except:
        db_session.rollback()
        crmLogger.error(f"写入file表发生异常: {traceback.format_exc()}")
        redisClient.setData(f"crm:task:{task_id}", "100:100")
        return False
    finally:
        db_session.close()

    try:
        db_session.query(History).filter(History.id == task_id).update({"status": 3, "err_file": filename})
        db_session.commit()
    except:     
        db_session.rollback()
        crmLogger.error(f"更新history表发生异常: {traceback.format_exc()}")
        redisClient.setData(f"crm:task:{task_id}", "100:100")
        return False
    finally:
        db_session.close()

    return True

def importTableTask(table_name: str):
    '''
    表格导入任务
    :param table_name: 表别名
    '''
    lock = redisClient.lock(f"import_{table_name}_lock", timeout=300)  # 300秒锁过期时间

    if lock.acquire(blocking=False):  # 获取锁

        try:
            while redisClient.llen(f"crm:import:{table_name}") > 0:  # 导入队列不为空时

                import time
                time.sleep(20)

                task_data = json.loads(redisClient.rpop(f"crm:import:{table_name}"))  # 读取任务数据

                crmLogger.info(f"正在执行导入任务: {task_data}")

                try:               # 更新状态为执行中
                    db_session.query(History).filter(History.id == task_data["task_id"]).update({History.status: 1})
                    db_session.commit()
                except:
                    db_session.rollback()
                    crmLogger.error(f"更新history表发生异常: {traceback.format_exc()}")
                    continue
                finally:
                    db_session.close()
                
                temp_table = readExcel(os.path.join(UPLOAD_EXCEL_DIR, task_data["file"]))  # 读取表格

                if temp_table is None:  # 读取表格失败
                    crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: 读取导入表格失败")
                    if not writeError(task_data["task_id"], "读取导入表格失败"):
                        continue

                table_headers = temp_table.columns.tolist()  # 获取表头字段

                if len(table_headers) == 0:                  # 如果表头为空
                    crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: 读取表格表头为空")
                    if not writeError(task_data["task_id"], "读取表格表头为空"):
                        continue

                templ_header = redisClient.getData(f"crm:header:{task_data['table']}")  # 从redis中读取缓存

                if templ_header:
                    templ_header = [MyHeader(i) for i in json.loads(templ_header)]
                else:
                    try:  # 查询数据中表头的记录
                        templ_header = db_session.query(Header.name, Header.value, Header.value_type, Header.type, Header.must_input, Header.is_unique).filter(Header.table_name == task_data["table"]).all()
                    finally:
                        db_session.close()

                # 读取文件的header和数据库中比对是否一致,不一致说明不是使用模板导入
                if [h.name for h in templ_header].sort() != list(map(lambda x: x.rsplit("*", 1)[0] if x.endswith("*") else x, table_headers)).sort():  # 去除*号后排序后比较
                    crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: 未使用模板导入")
                    if not writeError(task_data["task_id"], "未使用模板导入"):
                        continue

                manageTable = initManageTable(task_data["table"])  # 实例化已存在的资产表

                # 判断必填值列是否有空值
                must_header = [h.name for h in templ_header if h.must_input == 1]
                for h in must_header:
                    if temp_table[f"{h}*"].isnull().any():         # 判断是否有空值,带*表示必填
                        crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: {h}字段为必填项,存在空值")
                        if not writeError(task_data["task_id"], f"{h}字段为必填项,存在空值"):
                            continue

                # 校验数据是否唯一,有重复导入
                unique_header = []
                for h in templ_header:
                    if h.is_unique == 1:
                        if h.must_input == 1:
                            unique_header.append({"name": f"{h.name}*", "value": h.value})
                        else:
                            unique_header.append({"name": f"{h.name}", "value": h.value})
                        
                for h in unique_header:
                    if temp_table[f"{h['name']}"].duplicated().any():  # 判断是否有重复数据
                        crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: {h['name'].rsplit('*', 1)[0]}字段为唯一项,有重复数据")
                        if not writeError(task_data["task_id"], f"{h['name'].rsplit('*', 1)[0]}字段为唯一项,有重复数据"):
                            continue

                    try:  # 比对导入的表格数据与数据库中是否有重复
                        col_data = db_session.query(getattr(manageTable.c, h["value"])).all()
                    finally:
                        db_session.close()

                    col_data = [getattr(c, h["value"]) for c in col_data if getattr(c, h["value"])]

                    if temp_table[f"{h['name']}"].isin(col_data).any():  # 判断是否有重复数据
                        crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: {h['name'].rsplit('*', 1)[0]}字段在数据库中有重复数据")
                        if not writeError(task_data["task_id"], f"{h['name'].rsplit('*', 1)[0]}字段在数据库中有重复数据"):
                            continue

                for h in templ_header:
                
                    if h.type == 2:  # 校验数据是否从下拉列表选项中值
                        try:
                            _opt = db_session.query(Options.option_name).filter(Options.table_name == task_data["table"], Options.header_value == h.value).all()
                        finally:
                            db_session.close()

                        if not temp_table[h.name].isin([o.option_name for o in _opt]):
                            crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: {h.name}字段存在非固定选项值")
                            if not writeError(task_data["task_id"], f"{h.name}字段存在非固定选项值"):
                                continue

                    if h.value_type == 2:   # 校验数据中长度是否合法       
                        # is_all_length = temp_table[h.name].str.len == h.length
                        # if not is_all_length.all():
                        if len(temp_table[temp_table[h.name].str.len() != h.length]) > 0:
                            crmLogger.error(f"用户{task_data['user']}导入资产表{task_data['table']}失败: {h.name}字段存在不满足长度的值")
                            if not writeError(task_data["task_id"], f"{h.name}字段存在不满足长度的值"):
                                continue

                insert_data = temp_table.to_dict(orient="records")

                date_header = [h.name for h in templ_header if h.value_type == 4]
                datetime_header = [h.name for h in templ_header if h.value_type == 5]

                for i in insert_data:
                    for c in templ_header:
                        if c.must_input == 1:
                            new_data = i.pop(f"{c.name}*")
                        else:
                            new_data = i.pop(c.name)
                        if new_data:
                            if date_header or datetime_header:
                                if c.name in date_header:       # 如果是时间,判断是否是date类型,否则进行转换
                                    if isinstance(new_data, datetime):
                                        new_data = date.fromordinal(new_data.toordinal())
                                    elif not isinstance(new_data, date):
                                        try:
                                            new_data = datetime.strptime(new_data, "%Y-%m-%d")
                                        except (ValueError, TypeError):
                                            pass
                                elif c.name in datetime_header:  # 如果是时间,判断是否是datetime类型,否则进行转换
                                    if isinstance(new_data, date):
                                        new_data = datetime.fromordinal(new_data.toordinal())
                                    elif not isinstance(new_data, datetime):
                                        try:
                                            new_data = datetime.strptime(new_data, "%Y-%m-%d %H:%M:%S")
                                        except (ValueError, TypeError):
                                            pass
                                else:
                                    if isinstance(new_data, datetime):
                                        new_data = new_data.strftime("%Y-%m-%d %H:%M:%S")
                                    elif isinstance(new_data, date):
                                        new_data = new_data.strftime("%Y-%m-%d")
                            i.update({c.value: new_data})

                try:
                    with engine.begin() as conn:  # 开启事务,批量插入数据        
                        stmt = insert(manageTable)
                        conn.execute(stmt, insert_data)
                except:
                    crmLogger.error(f"{table_name}表插入数据失败: {traceback.format_exc()}")
                    continue

                try:
                    db_session.query(History).filter(History.id == task_data["task_id"]).update({"status": 2})
                    db_session.commit()
                except:
                    db_session.rollback()
                finally:
                    db_session.close()

                crmLogger.info("导入成功")
                
                redisClient.setData(f"crm:task:{task_data['task_id']}", "100:100")   # 设置进度为100%

        finally:
            lock.release()  # 释放锁
            # lock_extender.join()

    else:
        crmLogger.info("任务已存在")

def startImportTableTask(task_name):
    '''启动表格导入任务'''
    with ThreadPoolExecutor(max_workers=3) as executor:
        future = executor.submit(partial(importTableTask, task_name))
        return future

def exportTableTask():
    '''表格导出任务'''
    lock = redisClient.lock("export_lock", timeout=300)  # 300秒锁过期时间

    if lock.acquire(blocking=False):  # 获取锁

        try:
            while redisClient.llen("crm:task:export") > 0:
                
                task_data = json.loads(redisClient.rpop("crm:task:export"))

                # 数据库中设置次任务状态

                manageTable = initManageTable(task_data["table_name"])  # 实例化已存在的资产表

                if task_data["filter"]:  # 如果存在筛选条件
                
                    try:
                        export_data = db_session.query(manageTable).filter(eval(filter)).all()
                    finally:
                        db_session.close()

                else:

                    try:
                        export_data = db_session.query(manageTable).all()
                    finally:
                        db_session.close()

                redisClient.setData("crm:task:{}".format(task_data["task_id"]), "0:{}".format(len(export_data)))  # 将任务进度写入redis

                createExcel(TEMP_DIR, task_data["task_id"], task_data["table_name"], export_data)

        finally:
            lock.release()

def ping_ip():
    ''''''
    while redisClient.llen("crm:task:ping") > 0:
        ip = redisClient.rpop()
        if ip:
            scan_ip(ip)

def pingHostTask():
    '''批量探测主机任务'''
    lock = redisClient.lock("ping_lock", timeout=300)  # 300秒锁过期时间

    if lock.acquire(blocking=False):  # 获取锁

        try:
            while redisClient.llen("crm:task:ping") > 0:
                task_data = json.loads(redisClient.rpop("crm:task:ping").decode("utf-8"))

                threads = []
                for _ in range(5):
                    thread = threading.Thread(target=ping_ip)
                    thread.start()
                    threads.append(thread)

                for t in threads:
                    t.join()          

        finally:
            lock.release()
