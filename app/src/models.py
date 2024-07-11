#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  models.py
@Time    :  2024/04/21 21:07:10
@Version :  1.0
@Desc    :  数据库模型模块
'''
import re
import json
import traceback
from typing import Union
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Date, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta, date
from app.utils import redisClient, crmLogger
from app.utils.config import cfg

# 数据库引擎
engine = create_engine(
    "mysql+pymysql://{}:{}@{}:{}/{}".format(cfg.get("database", "mysql_user"), cfg.get("database", "mysql_pwd"), cfg.get("database", "mysql_host"), cfg.get("database", "mysql_port"), cfg.get("database", "mysql_db")),
    echo=False,  # 是否打印sql
    pool_size=100,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_timeout=30
)

# 数据库会话
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# 数据库基类
Base = declarative_base()
Base.query = db_session.query_property()

def init_cache():
    '''
    初始化redis缓存
    '''
    crmLogger.info("正在初始化缓存")

    # 初始化系统配置
    redisClient.setData("crm:system:enable_white", db_session.query(Setting.value).filter(Setting.type == "enable_white").first().value)
    redisClient.setData("crm:system:enable_failed", db_session.query(Setting.value).filter(Setting.type == "enable_failed").first().value)
    redisClient.setData("crm:system:enable_single", db_session.query(Setting.value).filter(Setting.type == "enable_single").first().value)
    redisClient.setData("crm:system:enable_watermark", db_session.query(Setting.value).filter(Setting.type == "enable_watermark").first().value)
    redisClient.setData("crm:system:failed_count", db_session.query(Setting.value).filter(Setting.type == "failed_count").first().value)
    
    # 初始化白名单ip
    white_ip = db_session.query(WhiteList.ip).all()

    if len(white_ip) > 0:
        for item in white_ip:
            redisClient.setSet("crm:system:white_ip_list", item.ip)

    # 缓存资产表信息用于搜索
    try:
        manage_list = db_session.query(Manage.uuid, Manage.name, Manage.table_name).all()
    finally:

        db_session.close()
    
    if len(manage_list) > 0:
        for item in manage_list:
            redisClient.setSet("crm:manage:table_uuid", item.uuid)  # 缓存资产表uuid
            redisClient.setSet("crm:manage:table_name", item.name)  # 缓存资产表标题

            try:
                _h = db_session.query(Header).filter(Header.table_name == item.table_name).order_by(Header.order.asc()).all()
            finally:
                db_session.close()

            if _h:
                _h_dicts = [
                    {c.name: getattr(u, c.name) for c in u.__table__.columns if c.name not in ["create_user", "create_time", "update_user", "update_time"]} for u in _h
                ]  # 转换为字典dict
                redisClient.setData(f"crm:header:{item.table_name}", json.dumps(_h_dicts))  # 缓存资产表的header

            try:
                _r = db_session.query(Echart).filter(Echart.table_name == item.table_name).order_by(Echart.id.asc()).all()
            finally:
                db_session.close()

            if _r:
                _r_dicts = [
                    {c.name: getattr(u, c.name) for c in u.__table__.columns} for u in _r
                ]
                redisClient.setData(f"crm:echart:{item.table_name}", json.dumps(_r_dicts))  # 缓存资产表图表规则

    crmLogger.info("缓存初始化完成")

def init_db():
    '''
    初始化数据库
    '''
    crmLogger.info("正在初始化数据库")
    Base.metadata.create_all(bind=engine)  # 手册启动创建所有表
    crmLogger.info("数据库初始化完成")
    init_cache()

class User(Base):
    '''用户表'''
    __tablename__ = "crm_user"
    uid = Column(Integer, primary_key=True, autoincrement=True)                   # 用户id
    name = Column(String(100))                                                    # 用户昵称
    username = Column(String(100), index=True, nullable=False, unique=True)       # 用户名
    password = Column(String(40), nullable=False)                                 # 用户密码
    create_time = Column(DateTime, default=datetime.now)                          # 用户创建时间
    create_user = Column(String(100))                                             # 用户创建者
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)   # 用户更新时间
    update_user = Column(String(100))                                             # 用户更新者
    type = Column(Integer, default=1)                                             # 用户类型: 1-永久用户,2-临时用户
    expire_time = Column(Date, default=date.today() + timedelta(days=30))         # 临时用户到期时间,默认30天有效期
    pwd_expire_time = Column(Date, default=date.today() + timedelta(days=90))     # 密码过期时间,默认90天有效期
    status = Column(Integer, default=1)                                           # 状态: 1-正常,2-到期用户,0-锁定用户
    company = Column(String(100))                                                 # 用户所属组织或者公司
    avator = Column(String(100), default="default")                               # 用户头像地址
    is_first = Column(Integer, default=1)                                         # 用户是否第一次登录: 1-是,0-否,用于判断是否启动引导界面

class Log(Base):
    '''日志表'''
    __tablename__ = "crm_log"
    id = Column(Integer, primary_key=True, autoincrement=True)  # 日志id
    ip = Column(String(20), nullable=False)                     # 操作用户的IP
    operate_type = Column(String(40), nullable=False)           # 操作类型
    operate_content = Column(String(255), nullable=False)       # 操作内容
    operate_user = Column(String(100), nullable=False)          # 操作用户
    operate_time = Column(DateTime, default=datetime.now)       # 操作时间

class Setting(Base):
    '''系统配置表'''
    __tablename__ = "crm_setting"
    type = Column(String(40), primary_key=True, unique=True, nullable=False)  # 配置类型
    value = Column(Integer, default=0)                                        # 配置的值
    desc = Column(String(40))                                                 # 配置的描述信息

class WhiteList(Base):
    '''白名单'''
    __tablename__ = "crm_white_list"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    ip = Column(String(20), unique=True, nullable=False)        # 白名单ip
    description = Column(String(255))                           # 描述信息
    create_user = Column(String(100))                           # 白名单创建者
    create_time = Column(DateTime, default=datetime.now)        # 创建时间

class Manage(Base):
    '''资产表'''
    __tablename__ = "crm_manage"
    uuid = Column(String(40), primary_key=True, unique=True, nullable=False)  # 资产表id
    name = Column(String(255), unique=True, nullable=False)                   # 自定义资产表名称
    table_name = Column(String(20), unique=True, nullable=False)              # 资产表对应的数据库表名
    table_image = Column(String(20), default="crm")                           # 资产表背景图片
    description = Column(String(255))                                         # 资产表描述信息
    create_user = Column(String(100))                                         # 资产表创建者
    create_time = Column(DateTime, default=datetime.now)                      # 资产表创建时间
    update_user = Column(String(100))                                         # 资产表更新者
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 资产表更新时间

class Echart(Base):
    '''图表配置表'''
    __tablename__ = "crm_echart"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    name = Column(String(255), nullable=False)                  # 图表名称
    type = Column(Integer, default=1)                           # 图表类型: 1-饼图,2-柱形图,3-折线图
    keyword = Column(String(100), nullable=False)               # 图表数据来源的字段
    date_keyword = Column(String(100))                          # 图表数据的时间字段
    table_name = Column(String(20), nullable=False)             # 图表数据来源的资产表

class File(Base):
    '''文件上传信息表'''
    __tablename__ = "crm_file"
    uuid = Column(String(40), primary_key=True, unique=True, nullable=False)  # 文件的唯一标识
    filename = Column(String(255), nullable=False)                            # 文件名
    filepath = Column(Integer, default=1)                                     # 文件路径: 1-excel_path,2-image_path,0-temp_path
    affix = Column(String(10), nullable=False)                                # 文件后缀
    password = Column(String(20))                                             # 文件密码,如果存在的话
    upload_user = Column(String(100))                                         # 文件上传者
    upload_time = Column(DateTime, default=datetime.now)                      # 文件上传时间

class Header(Base):
    '''资产表表头表'''
    __tablename__ = "crm_header"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Integer, default=1)                     # 表头类型: 1-字符串, 2-下拉列表
    name = Column(String(255), nullable=False)            # 中文名称
    value = Column(String(255), nullable=False)           # 英文字段
    value_type = Column(Integer, default=1)               # 值类型: 1-字符串(默认255字符),2-定长字符串,3-大文本(超过255个字符),4-日期(yyyy-mm-dd),5-时间(yyyy-mm-dd hh:mm:ss)
    table_name = Column(String(20), nullable=False)       # 归属哪个资产表
    is_unique = Column(Integer, default=0)                # 是否唯一: 1-是,0-否
    is_desence = Column(Integer, default=0)               # 是否脱敏: 1-是,0-否
    must_input = Column(Integer, default=0)               # 是否必填: 1-是,0-否
    length = Column(Integer, default=0)                   # 长度,如果value_type为2时,该字段才有意义
    order = Column(Integer, default=0)                    # 排序
    create_user = Column(String(100))                     # 创建者
    create_time = Column(DateTime, default=datetime.now)  # 创建时间
    update_user = Column(String(100))                     # 更新者
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间

class Options(Base):
    '''下拉选项表'''
    __tablename__ = "crm_options"
    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增id
    option_name = Column(String(255), nullable=False)  # 选项名称
    option_value = Column(String(255), nullable=False) # 选项值
    header_value = Column(String(255), nullable=False) # 归属字段
    table_name =Column(String(20), nullable=False)     # 归属资产表

class Task(Base):
    '''批量探测任务表'''
    __tablename__ = "crm_task"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)  # 任务id
    name = Column(String(255), nullable=False)                              # 任务名称
    keyword = Column(String(255), nullable=False)                           # 任务对应的资产表的IP字段
    table_name = Column(String(20), nullable=False)                         # 任务对应的资产表
    status = Column(Integer, default=0)                                     # 任务状态: 0-未开始, 1-进行中, 2-已完成, 3-失败
    create_user = Column(String(100))                                       # 任务创建者
    create_time = Column(DateTime, default=datetime.now)                    # 任务创建时间

class DetectResult(Base):
    '''批量探测任务结果表'''
    __tablename__ = "crm_detect_result"
    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增id
    task_id = Column(String(40), nullable=False)                # 任务id,来源于task的id字段
    ip = Column(String(20), nullable=False)                     # 探测的ip
    status = Column(Integer, nullable=False)                    # 状态: 0-不在线, 1-在线, 2-未探测
    reason = Column(String(255))                                # 未探测原因
    create_time = Column(DateTime, default=datetime.now)        # 创建时间

class Notify(Base):
    '''到期提醒表'''
    __tablename__ = "crm_notify"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)       # 任务id
    name = Column(String(255), nullable=False)                                   # 任务名
    keyword = Column(String(20), nullable=False)                                 # 日期列名
    table_name = Column(String(20), nullable=False)                              # 资产表表名
    status = Column(Integer, default=1)                                          # 状态: 1-启动, 0-停止
    create_user = Column(String(100))                                            # 任务创建者
    create_time = Column(DateTime, default=datetime.now)                         # 任务创建时间
    update_user = Column(String(100))                                            # 更新者
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间

class Notice(Base):
    '''用户通知表'''
    __tablename__ = "crm_notice"
    id = Column(Integer, primary_key=True, autoincrement=True)                   # 消息的自增id
    message = Column(String(40), nullable=False)                                 # 消息内容
    notify_id = Column(String(40), nullable=False)                               # 字段来源:crm_notify的id
    is_read = Column(Integer, default=0)                                         # 0-未读,1-已读
    create_time = Column(DateTime, default=datetime.now)                         # 创建时间
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间

class History(Base):
    '''导入导出历史记录表'''
    __tablename__ = "crm_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_uuid = Column(String(40))                        # 导入或导出的文件uuid
    err_file = Column(String(40))                         # 导入文件错误说明文件uuid
    mode = Column(Integer, nullable=False)                # 1-导出, 2-导入
    status = Column(Integer, default=0)                   # 0-排队中, 1-在执行, 2-执行成功, 3-执行失败
    table_name = Column(String(20), nullable=False)       # 导入导出的资产表别名
    create_user = Column(String(100))                     # 创建者
    create_time = Column(DateTime, default=datetime.now)  # 创建时间

class MyHeader:
    '''
    将dict类型的header转换为类便于使用.访问
    '''
    def __init__(self, data):
        self.__data = data
    
    def __getattr__(self, name):
        return self.__data.get(name)

def generateManageTable(table_name: str="", cols=[]) -> Union[Table, None]:
    '''
    生成新资产表
    :param table_name: 资产表名称
    :param cols: 表字段列表
    :return:
    '''
    cols.append(Column('_id', Integer, primary_key=True, autoincrement=True))
    cols.append(Column('_create_user', String(100)))
    cols.append(Column('_create_time', DateTime, default=datetime.now))
    cols.append(Column('_update_user', String(100)))
    cols.append(Column('_update_time', DateTime, default=datetime.now, onupdate=datetime.now))

    dynamic_table = Table(table_name, Base.metadata, *cols, extend_existing=True)

    try:
        with engine.connect() as conn:
            dynamic_table.create(conn)  # 创建动态表格
    except:
        crmLogger.error(f"生成新资产表{table_name}失败,原因: {traceback.format_exc()}")
        return None
    
    return dynamic_table

def initManageTable(table_name: str="") -> Table:
    '''
    实例化已有的资产表
    :pararm table_name: 资产表名称
    :return:
    '''
    return Table(table_name, 
                 Base.metadata, 
                 Column("_id", Integer, primary_key=True, autoincrement=True), 
                 Column('_create_user', String(100)), 
                 Column('_create_time', DateTime, default=datetime.now), 
                 Column('_update_time', DateTime, default=datetime.now, onupdate=datetime.now),
                 extend_existing=True, 
                 autoload=True, 
                 autoload_with=engine)

def addColumn(table_name: str, col_name: str, col_type: str) -> bool:
    '''
    资产表添加新字段
    :param table_name: 资产表名称
    :param col_name: 数据列名
    :param col_type: 数据类型
    :return:
    '''
    try:
        add_col_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
        db_session.execute(text(add_col_sql))
        db_session.commit()
        return True    
    except:
        db_session.rollback()
        crmLogger.error(f"资产表{table_name}添加字段失败,原因: {traceback.format_exc()}")
        return False  
    finally:
        db_session.close()
    
def alterColumn(table_name: str, col_name: str, dist_type: str) -> bool:
    '''
    资产表修改已有字段属性
    :param table_name: 资产表名称
    :param col_name: 数据列名称
    :param dist_type: 目标数据类型 VARCHAR(255), TEXT, DATE, DATETIME
    :return:
    '''
    varchar_pattern = re.compile(r'^VARCHAR\(\d+\)$', re.IGNORECASE)
    text_pattern = re.compile(r'^TEXT$', re.IGNORECASE)
    date_pattern = re.compile(r'^DATE$', re.IGNORECASE)
    datetime_pattern = re.compile(r'^DATETIME$', re.IGNORECASE)

    create_index = None

    if not (varchar_pattern.match(dist_type) or text_pattern.match(dist_type) or date_pattern.match(dist_type) or datetime_pattern.match(dist_type)):
        return False

    try:
        alter_column_sql = f"ALTER TABLE {table_name} MODIFY COLUMN {col_name} {dist_type}"
        db_session.execute(text(alter_column_sql))
        
        if create_index:
            db_session.execute(text(create_index))

        db_session.commit()
        return True   
    except:
        db_session.rollback()
        crmLogger.error(f"资产表{table_name}修改字段{col_name}属性失败,原因: {traceback.format_exc()}")
        return False
    
    finally:

        db_session.close()

init_db()
