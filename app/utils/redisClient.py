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
from app.utils.config import cfg

class redisConnPool:
    '''redis连接池'''
    def __init__(self, passwd: str, host: str="127.0.0.1", port: int=6379, db: int=0) -> None:
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
            self.pubsub = None
        except Exception as e:
            crmLogger.error(f"redis连接错误: {e}")
    
    def setData(self, key:str, value:Union[int, str], expire: int=0) -> None:
        '''
        写入数据
        :param key: 键
        :param value: 值
        :param expire: 过期时间,单位:秒
        '''
        try:
            if expire == 0:
                self.conn.set(key, value)
            else:
                # 设置过期时间
                self.conn.set(key, value, ex=expire)
        finally:
            self.conn.close()

    def getData(self, key: str) -> Union[str, None]:
        '''
        读取数据
        :param key: 键
        :return:
        '''
        try:
            result = self.conn.get(key)
        finally:
            self.conn.close()
        if result is None:
            return None
        return result.decode("utf-8")
    
    def delData(self, key) -> None:
        '''
        删除数据
        :param key: 键
        '''
        try:
            self.conn.delete(key)
        finally:
            self.conn.close()

    def setIncr(self, key: str, amount: int=1) -> None:
        '''
        设置自增
        :param amount: 自增数
        '''
        try:
            self.conn.incr(key, amount)
        finally:
            self.conn.close()

    def setDecr(self, key: str, amount: int=1) -> None:
        '''
        设置自减
        :param amount: 自减数
        '''
        try:
            self.conn.decr(key, amount)
        finally:
            self.conn.close()

    def setHash(self, hashName: str, key: str, value: str) -> None:
        '''
        写入dict
        :param hashName: hash名称
        :param key: hash中的键
        :parm value: hash中键对应的值
        '''
        try:
            self.conn.hset(hashName, key, value)
        finally:
            self.conn.close()
    
    def setHashData(self, hashName: str, data: dict) -> None:
        '''
        写入dict
        :param hashName: hash名称
        :param data: dict
        '''
        try:
            self.conn.hmset(hashName, data)
        finally:
            self.conn.close()

    def getHash(self, hashName: str, key: str) -> str:
        '''
        读取dict
        :param hashName: hash名称
        :param key: hash中的键
        :return:
        '''
        try:
            return self.conn.hget(hashName, key)
        finally:
            self.conn.close()
    
    def getHashData(self, hashName: str) -> dict:
        '''
        获取dict中的所有键值对
        :param hashName: hash名称
        :return:
        '''
        try:
            return self.conn.hgetall(hashName)
        finally:
            self.conn.close()
    
    def delHash(self, hashName: str, key: str) -> None:
        '''
        删除dict中的键值对
        '''
        try:
            self.conn.hdel(hashName, key)
        finally:
            self.conn.close()

    def setSet(self, setName: str, *value: str) -> None:
        '''
        写入set
        :param setName: set名称
        :param *value: 值
        '''
        try:
            self.conn.sadd(setName, *value)
        finally:
            self.conn.close()

    def getSet(self, setName: str, value: str) -> bool:
        '''
        查询成员是否存在set中
        :param setName: set名称
        :param value: 值
        :return:
        '''
        try:
            return self.conn.sismember(setName, value)
        finally:
            self.conn.close()
    
    def getSetData(self, setName: str) -> list:
        '''
        获取set中的所有成员
        :param setName: set名称
        :return:
        '''
        try:
            return list(self.conn.smembers(setName))
        finally:
            self.conn.close()
    
    def delSet(self, setName: str, value: str) -> bool:
        '''
        删除set中指定成员
        :param setName: set名称
        :param value: 值
        '''
        try:
            self.conn.srem(setName, value)
        finally:
            self.conn.close()

    def lpush(self, listName: str, value: str) -> None:
        '''
        从左往右增加列表数据
        :param listName: 列表名称
        :param value: 值
        '''
        try:
            self.conn.lpush(listName, value)
        finally:
            self.conn.close()

    def llen(self, listName: str) -> int:
        '''
        获取指定列表的长度
        :param listName: 列表名称
        :return:
        '''
        try:
            return self.conn.llen(listName)
        finally:
            self.conn.close()
    
    def rpop(self, listName: str) -> str:
        '''
        取列表中最右边的值
        :param listName: 列表名称
        :return:
        '''
        try:
            return self.conn.rpop(listName)
        finally:
            self.conn.close()

    def subscribe(self, channel: str, fun: callable):
        '''
        获取订阅对象
        :param channel: 频道
        :param fun: 回调函数
        '''
        if self.pubsub is None:
            self.pubsub = self.conn.pubsub()
        self.pubsub.subscribe(**{channel: fun})
        self.pubsub.run_in_thread(sleep_time=0.001)
    
    def publish(self, channel: str, message: str):
        '''
        发布消息
        '''
        try:
            self.conn.publish(channel, message)
        finally:
            self.conn.close()

    def unSubscribe(self):
        '''
        取消订阅
        '''
        if self.pubsub is not None:
            self.pubsub.unsubscribe()
            self.pubsub.close()
            self.pubsub = None

redisClient = redisConnPool(passwd=cfg.get("database", "redis_pwd"), host=cfg.get("database", "redis_host"), port=int(cfg.get("database", "redis_port")), db=int(cfg.get("database", "redis_db")))
def export(message):
    ''''''
    print(message["data"])
redisClient.subscribe("export", export)
