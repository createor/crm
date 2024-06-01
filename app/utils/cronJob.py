#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  cronJob.py
@Time    :  2024/05/29 11:21:23
@Version :  1.0
@Desc    :  定时任务模块
'''

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.redis import RedisJobStore

scheduler = BlockingScheduler(jobstores={
    'default': RedisJobStore(host='localhost', port=6379, db=0)
})

def setJob(id: str = "", job_time: str = "00:00:00", func: function = None):
    '''
    创建定时任务
    :param id: 任务id
    :param job_time: 任务执行时间,
    :param func: 任务函数
    '''
    scheduler.add_job(func, 'cron', id=id, hour=job_time.split(':')[0], minute=job_time.split(':')[1], second=job_time.split(':')[2])

def delJob(id: str = ""):
    '''
    删除定时任务
    :param id: 任务id
    '''
    scheduler.remove_job(id)
