#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  cronJob.py
@Time    :  2024/05/29 11:21:23
@Version :  1.0
@Desc    :  定时任务模块
'''

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from app.utils.config import cfg
from typing import Any

class Job(object):
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(jobstores={
            "default": RedisJobStore(host=cfg.get("database", "redis_host"), port=int(cfg.get("database", "redis_port")), password=cfg.get("database", "redis_pwd"), db=int(cfg.get("database", "redis_db")))  # 使用Redis存储任务
        }, executor={
            "defalut": {"type": "threadpool", "max_workers": 20},
            "processpool": ProcessPoolExecutor(max_workers=5)
        }, job_defaults={
            "coalesce": False,
            "max_instances": 3
        })

    def setJob(self, id: str = "", job_time: str = "00:00:00", func: Any = None, args: list = [], kwargs: dict = {}) -> None:
        '''
        创建定时任务
        :param id: 任务id
        :param job_time: 任务执行时间,
        :param func: 任务函数
        '''
        # 添加任务,使用cron表达式
        self.scheduler.add_job(func=func, trigger='cron', args=args, kwargs=kwargs, id=id, hour=job_time.split(':')[0], minute=job_time.split(':')[1], second=job_time.split(':')[2])

    def pauseJob(self, id: str = "") -> None:
        '''
        暂停定时任务
        :param id: 任务id
        '''
        self.scheduler.pause_job(id)

    def resumeJob(self, id: str = "") -> None:
        '''
        恢复定时任务
        :param id: 任务id
        '''
        self.scheduler.resume_job(id)

    def delJob(self, id: str = "") -> None:
        '''
        删除定时任务
        :param id: 任务id
        '''
        self.scheduler.remove_job(id)

    def getAllJobs(self) -> list:
        '''
        获取所有定时任务信息
        :return:
        '''
        return self.scheduler.get_jobs()

    def startJob(self) -> None:
        '''
        启动定时任务
        '''
        self.scheduler.start()

    def stopJob(self) -> None:
        '''
        停止定时任务
        '''
        self.scheduler.shutdown()

job = Job()  # 创建实例
job.startJob()
