#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  redisClient.py
@Time    :  2024/04/21 21:02:13
@Version :  1.0
@Desc    :  redis客户端
'''
from typing import Union
import redis
from app.utils import crmLogger

class redisConnPool:
    '''redis连接池'''
    def __init__(self, passwd: str, host: str="117.72.32.46", port: int=6379, db: int=0) -> None:
        '''
        :param passwd: redis密码
        :param host: redis地址
        :param port: redis端口
        :param db: redis数据库
        '''
        try:
            self.pool = redis.ConnectionPool(
                                host=host,
                                port=port,
                                db=db,
                                password=passwd
                            )
            self.conn = redis.Redis(connection_pool=self.pool)
        except Exception as e:
            crmLogger.error(f"redis连接错误: {e}")
    
    def setData(self, key:str, value:Union[int, str], expire: int=0) -> None:
        '''
        写入数据
        :param key: 键
        :param value: 值
        :param expire: 过期时间,单位:秒
        '''
        if expire == 0:
            self.conn.set(key, value)
        else:
            # 设置过期时间
            self.conn.set(key, value, ex=expire)

    def getData(self, key: str) -> Union[bytes, None]:
        '''
        读取数据
        :param key: 键
        :return:
        '''
        result = self.conn.get(key)
        if result is None:
            return None
        return result.decode()
    
    def delData(self, key) -> None:
        '''
        删除数据
        :param key: 键
        '''
        self.conn.delete(key)

    def setIncr(self, key: str, amount: int=1) -> None:
        '''
        设置自增
        :param amount: 自增数
        '''
        self.conn.incr(key, amount)

    def setDecr(self, key: str, amount: int=1) -> None:
        '''
        设置自减
        :param amount: 自减数
        '''
        self.conn.decr(key, amount)

    def setHash(self, hashName: str, key: str, value: str) -> None:
        '''
        写入dict
        :param hashName: hash名称
        :param key: hash中的键
        :parm value: hash中键对应的值
        '''
        self.conn.hset(hashName, key, value)

    def getHash(self, hashName: str, key: str) -> str:
        '''
        读取dict
        :param hashName: hash名称
        :param key: hash中的键
        :return:
        '''
        return self.conn.hget(hashName, key)
    
    def delHash(self, hashName: str, key: str) -> None:
        '''
        删除dict中的键值对
        '''
        self.conn.hdel(hashName, key)

    def setSet(self, setName: str, *value: str) -> None:
        '''
        写入set
        :param setName: set名称
        :param *value: 值
        '''
        self.conn.sadd(setName, *value)

    def getSet(self, setName: str, value: str) -> bool:
        '''
        查询成员是否存在set中
        :param setName: set名称
        :param value: 值
        :return:
        '''
        return self.conn.sismember(setName, value)
    
    def delSet(self, setName: str, value: str) -> bool:
        '''
        删除set中指定成员
        :param setName: set名称
        :param value: 值
        '''
        self.conn.srem(setName, value)

    def lpush(self, listName: str, value: str) -> None:
        '''
        从左往右增加列表数据
        :param listName: 列表名称
        :param value: 值
        '''
        self.conn.lpush(listName, value)

    def llen(self, listName: str) -> int:
        '''
        获取指定列表的长度
        :param listName: 列表名称
        :return:
        '''
        return self.conn.llen(listName)
    
    def rpop(self, listName: str) -> str:
        '''
        取列表中最右边的值
        :param listName: 列表名称
        :return:
        '''
        return self.conn.rpop(listName)

redisClient = redisConnPool(passwd="123456")
