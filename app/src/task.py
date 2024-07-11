#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  task.py
@Time    :  2024/06/29 22:20:49
@Version :  1.0
@Desc    :  任务模块
'''
import json
import traceback
import time
from datetime import datetime
from redis.exceptions import LockNotOwnedError
from app.utils import redisClient, crmLogger, createExcel, TEMP_DIR, scan_ip
from app.src.models import db_session, Task, Notice, initManageTable
from sqlalchemy import and_
import threading

def notifyTask(task_id: str, name: str, table_name: str, keyword: str):
    '''
    通知任务
    :param task_id: 任务id
    :param name: 表名
    :param table_name: 表别名
    :param keyword: 日期字段
    '''
    manageTable = initManageTable(table_name)  # 实例化已存在资产表

    try:  # 查询过期数据
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

def extend_lock(lock, timeout):
    while True:
        time.sleep(timeout / 2)  # 每半个超时时间延长一次锁的过期时间
        try:
            lock.extend(timeout)
        except LockNotOwnedError:
            break  # 锁已被释放，退出循环

def exportTableTask():
    '''
    '''
    lock = redisClient.lock("export_lock", timeout=300)  # 300秒锁过期时间

    if lock.acquire(blocking=False):  # 获取锁

        lock_extender = threading.Thread(target=extend_lock, args=(lock, 300))
        lock_extender.start()

        try:
            while redisClient.llen("crm:task:export") > 0:
                task_data = json.loads(redisClient.rpop("crm:task:export").decode("utf-8"))

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
            lock_extender.join()

def ping_ip():
    while redisClient.llen("crm:task:ping") > 0:
        ip = redisClient.rpop()
        if ip:
            scan_ip(ip)

def pingHostTask():
    '''
    '''
    lock = redisClient.lock("ping_lock", timeout=300)  # 300秒锁过期时间

    if lock.acquire(blocking=False):  # 获取锁

        lock_extender = threading.Thread(target=extend_lock, args=(lock, 300))
        lock_extender.start()

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
            lock_extender.join()
