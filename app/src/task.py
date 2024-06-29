#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  task.py
@Time    :  2024/06/29 22:20:49
@Version :  1.0
@Desc    :  任务模块
'''
import json
import time
from redis.exceptions import LockNotOwnedError
from app.utils import redisClient, crmLogger, createExcel, TEMP_DIR, scan_ip
from app.src.models import db_session, Task, initManageTable
import threading

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
