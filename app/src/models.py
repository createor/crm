#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  models.py
@Time    :  2024/04/21 21:07:10
@Version :  1.0
@Desc    :  数据库模型模块
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Date
from datetime import datetime
from app.utils import redisClient, crmLogger, getUuid

# 数据库引擎
engine = create_engine(
    "mysql+pymysql://root:YH56qw#M@117.72.32.46:3306/crm",
    echo=False,  # 是否打印sql
    pool_size=100,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_timeout=30
)

# 数据库会话
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_cache():
    '''
    初始化redis缓存
    '''
    crmLogger.info("正在初始化缓存")
    # 初始化配置
    enable_failed = db_session.query(Setting.value).filter(Setting.type == "enable_failed").first()[0]
    redisClient.setData("enable_failed", enable_failed)
    enable_white = db_session.query(Setting.value).filter(Setting.type == "enable_white").first()[0]
    redisClient.setData("enable_white", enable_white)
    enable_single = db_session.query(Setting.value).filter(Setting.type == "enable_single").first()[0]
    redisClient.setData("enable_single", enable_single)
    failed_count = db_session.query(Setting.value).filter(Setting.type == "failed_count").first()[0]
    redisClient.setData("failed_count", failed_count)
    # 初始化白名单ip
    white_ip = db_session.query(WhiteList.ip).all()
    if len(white_ip) > 0:
        redisClient.setSet("white_ip_list", [v.ip for v in white_ip])
    crmLogger.info("缓存初始化完成")

def init_db():
    '''
    初始化数据库
    '''
    crmLogger.info("正在初始化数据库")
    Base.metadata.create_all(bind=engine)  # 创建所有表
    # 初始化数据
    # 初始化用户
    init_user = db_session.query(User).filter(User.username == "admin").first()
    if init_user is None:
        db_session.add(User(
            name="系统管理员",
            username="admin",
            password="",
            create_user="admin",
            type=1,
            pwd_expire_time="2099-12-31",
            avator="",
            status=1
        ))
    # 初始化图片文件
    init_bg_img = db_session.query(File).filter().first()  # 背景图片
    if init_bg_img is None:
        db_session.add(File(
            uuid=getUuid(),
            filename="crm.png",
            filepath=2
        ))
    init_avator_img = db_session.query(File).filter().first()  # 头像图片
    if init_avator_img is None:
        db_session.add(File(
            uuid=getUuid(),
            filename="default.png",
            filepath=2
        ))
    # 初始化配置
    init_config = db_session.query(Setting).all()
    if len(init_config) == 0:
        db_session.add(Setting(type="enable_failed", value=0, desc="是否开启失败锁定,1-开启,0-关闭"))
        db_session.add(Setting(type="enable_white", value=0, desc="是否开启白名单模式,1-开启,0-关闭"))
        db_session.add(Setting(type="enable_single", value=0, desc="是否开启单点登录功能,1-开启,0-关闭"))
        db_session.add(Setting(type="failed_count", value=3, desc="失败次数"))
    else:
        exist_types = [item.type for item in init_config]
        for v in list(set(["enable_failed", "enable_white", "enable_single", "failed_count"]) - set(exist_types)):
            if v == "enable_failed":
                db_session.add(Setting(type="enable_failed", value=0, desc="是否开启失败锁定,1-开启,0-关闭"))
            if v == "enable_white":
                db_session.add(Setting(type="enable_white", value=0, desc="是否开启白名单模式,1-开启,0-关闭"))
            if v == "enable_single":
                db_session.add(Setting(type="enable_single", value=0, desc="是否开启单点登录功能,1-开启,0-关闭"))
            if v == "failed_count":
                db_session.add(Setting(type="failed_count", value=3, desc="失败次数"))         
    db_session.commit()
    crmLogger.info("数据库初始化完成")
    init_cache()

class User(Base):
    '''用户表'''
    __tablename__ = "user"
    uid = Column(Integer, primary_key=True, autoincrement=True)  # 用户id
    name = Column(String(100))  # 用户昵称
    username = Column(String(100), index=True, nullable=False, unique=True)  # 用户名
    password = Column(String(40), nullable=False)  # 用户密码
    create_time = Column(DateTime, default=datetime.now)  # 创建时间
    create_user = Column(String(100))  # 创建者
    update_time = Column(DateTime)  # 更新时间
    update_user = Column(String(100))  # 更新者
    type = Column(Integer)  # 用户类型: 1-永久用户,2-临时用户
    expire_time = Column(Date)  # 临时用户到期时间
    pwd_expire_time = Column(Date)  # 密码过期时间
    status = Column(Integer, default=1)  # 状态: 1-正常,2-到期用户,0-锁定用户
    company = Column(String(100))  # 所属组织\公司
    avator = Column(String(100))  # 图像地址
    is_first = Column(Integer, default=1)  # 是否第一次登录: 1-是,0-否

class Log(Base):
    '''日志表'''
    __tablename__ = "log"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    ip = Column(String(20))  # 用户IP
    operate_type = Column(String(40))  # 操作类型
    operate_content = Column(Text)  # 操作内容
    operate_user = Column(String(100))  # 操作用户
    operate_time = Column(DateTime, default=datetime.now)  # 操作时间
class Setting(Base):
    '''系统配置表'''
    __tablename__ = "setting"
    type = Column(String(40), primary_key=True, unique=True, nullable=False)  # 配置类型
    value = Column(Integer)  # 配置的值
    desc = Column(String(40))  # 配置的描述信息

class WhiteList(Base):
    '''白名单'''
    __tablename__ = "white_list"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    ip = Column(String(20), unique=True, nullable=False)  # ip
    description = Column(String(255))  # 描述信息
    create_user = Column(String(100))  # 创建者
    create_time = Column(DateTime, default=datetime.now)  # 创建时间

class Manage(Base):
    '''资产表'''
    __tablename__ = "manage"
    uuid = Column(String(40), primary_key=True, unique=True, nullable=False)  # 表id
    name = Column(String(255), unique=True, nullable=False)  # 自定义资产表名称
    table_name = Column(String(20), unique=True, nullable=False)  # 对应的数据库表名
    table_image = Column()  # 背景图片
    description = Column(Text)  # 描述信息
    create_user = Column(String(100))  # 创建者
    create_time = Column(DateTime, default=datetime.now)  # 创建时间

class Echart(Base):
    '''图表配置表'''
    __tablename__ = "echart"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    name = Column(String(255))  # 图标名称
    type = Column(Integer, default=1)  # 图表类型: 1-柱形图,2-折线图,3-饼图
    keyword = Column(String(100))  # 数据来源的字段
    table_name = Column(String(20))  # 数据来源的资产表
    config = Column(Text)  # 配置

class File(Base):
    '''文件上传信息表'''
    __tablename__ = "file"
    uuid = Column(String(40), primary_key=True, unique=True, nullable=False)  # 文件的唯一标识
    filename = Column(Text, nullable=False)  # 文件名
    filepath = Column(Integer, default=1)  # 文件路径: 1-excel_path,2-image_path,0-temp_path
    upload_user = Column(String(100))  # 上传者
    upload_time = Column(DateTime, default=datetime.now)  # 上传时间

class Header(Base):
    '''资产表表头表'''
    __tablename__ = "header"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)

class Task(Base):
    '''批量探测任务表'''
    __tablename__ = "task"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)  # 任务id
    status = Column(Integer, nullable=False)  # 任务状态: 0-未开始,1-进行中,2-已完成,3-失败
    create_user = Column(String(100))  # 任务创建者
    create_time = Column(DateTime, default=datetime.now)

class DetectResult(Base):
    '''批量探测任务结果表'''
    __tablename__ = "detect_result"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(40), nullable=False)  # 任务id
    ip = Column(String(20), nullable=False)  # ip
    status = Column(Integer, nullable=False) # 状态: 0-不在线,1-在线,2-未探测
    create_time = Column(DateTime, default=datetime.now)
    reason = Column(String(255))  # 未探测原因

class Notify(Base):
    '''到期提醒表'''
    __tablename__ = "notify"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)  # 任务id
    status = Column()
    create_user = Column(String(100))  # 任务创建者
    create_time = Column(DateTime, default=datetime.now)

def getManageTable():
    '''
    '''
    return 

init_db()
