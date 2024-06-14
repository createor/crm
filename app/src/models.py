#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  models.py
@Time    :  2024/04/21 21:07:10
@Version :  1.0
@Desc    :  数据库模型模块
'''
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Text, Date
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from app.utils import redisClient, crmLogger, getUuid
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
        for item in white_ip:
            redisClient.setSet("white_ip_list", item.ip)
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
            password="07967d4a89a0172d1f20c53424d1860e",
            create_user="admin",
            type=1,
            pwd_expire_time="2099-12-31",
            avator="default",
            status=1,
            is_first=1
        ))
        crmLogger.info("已初始化用户admin")
    # 初始化图片文件
    init_bg_img = db_session.query(File).filter(File.uuid == "crm").first()          # 背景图片
    if init_bg_img is None:
        db_session.add(File(
            uuid="crm",
            filename="crm.png",
            filepath=2
        ))
        crmLogger.info("已初始化资产表默认背景图片")
    init_avator_img = db_session.query(File).filter(File.uuid == "default").first()  # 头像图片
    if init_avator_img is None:
        db_session.add(File(
            uuid="default",
            filename="default.png",
            filepath=2
        ))
        crmLogger.info("已初始化用户默认头像图片")
    # 初始化配置
    init_config = db_session.query(Setting).all()
    if len(init_config) == 0:
        db_session.add(Setting(type="enable_failed", value=0, desc="是否开启失败锁定,1-开启,0-关闭"))
        db_session.add(Setting(type="enable_white", value=0, desc="是否开启白名单模式,1-开启,0-关闭"))
        db_session.add(Setting(type="enable_single", value=0, desc="是否开启单点登录功能,1-开启,0-关闭"))
        db_session.add(Setting(type="failed_count", value=3, desc="失败次数"))
        crmLogger.info("已初始化默认系统配置")
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
        crmLogger.info("已初始化默认系统配置")        
    db_session.commit()
    crmLogger.info("数据库初始化完成")
    init_cache()

class User(Base):
    '''用户表'''
    __tablename__ = "user"
    uid = Column(Integer, primary_key=True, autoincrement=True)                   # 用户id
    name = Column(String(100))                                                    # 用户昵称
    username = Column(String(100), index=True, nullable=False, unique=True)       # 用户名
    password = Column(String(40), nullable=False)                                 # 用户密码
    create_time = Column(DateTime, default=datetime.now)                          # 用户创建时间
    create_user = Column(String(100))                                             # 用户创建者
    update_time = Column(DateTime)                                                # 用户更新时间
    update_user = Column(String(100))                                             # 用户更新者
    type = Column(Integer, default=1)                                             # 用户类型: 1-永久用户,2-临时用户
    expire_time = Column(Date, default=datetime.today() + timedelta(days=30))     # 临时用户到期时间,默认30天有效期
    pwd_expire_time = Column(Date, default=datetime.today() + timedelta(days=90)) # 密码过期时间,默认90天有效期
    status = Column(Integer, default=1)                                           # 状态: 1-正常,2-到期用户,0-锁定用户
    company = Column(String(100))                                                 # 用户所属组织或者公司
    avator = Column(String(100), default="default")                               # 用户头像地址
    is_first = Column(Integer, default=1)                                         # 用户是否第一次登录: 1-是,0-否,用于判断是否启动引导界面

class Log(Base):
    '''日志表'''
    __tablename__ = "log"
    id = Column(Integer, primary_key=True, autoincrement=True)  # 日志id
    ip = Column(String(20), nullable=False)                     # 操作用户的IP
    operate_type = Column(String(40), nullable=False)           # 操作类型
    operate_content = Column(Text, nullable=False)              # 操作内容
    operate_user = Column(String(100), nullable=False)          # 操作用户
    operate_time = Column(DateTime, default=datetime.now)       # 操作时间

class Setting(Base):
    '''系统配置表'''
    __tablename__ = "setting"
    type = Column(String(40), primary_key=True, unique=True, nullable=False)  # 配置类型
    value = Column(Integer, default=0)                                        # 配置的值
    desc = Column(String(40))                                                 # 配置的描述信息

class WhiteList(Base):
    '''白名单'''
    __tablename__ = "white_list"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    ip = Column(String(20), unique=True, nullable=False)        # 白名单ip
    description = Column(String(255))                           # 描述信息
    create_user = Column(String(100))                           # 白名单创建者
    create_time = Column(DateTime, default=datetime.now)        # 创建时间

class Manage(Base):
    '''资产表'''
    __tablename__ = "manage"
    uuid = Column(String(40), primary_key=True, unique=True, nullable=False)  # 资产表id
    name = Column(String(255), unique=True, nullable=False)                   # 自定义资产表名称
    table_name = Column(String(20), unique=True, nullable=False)              # 资产表对应的数据库表名
    table_image = Column(String(20), default="crm")                           # 资产表背景图片
    description = Column(Text)                                                # 资产表描述信息
    create_user = Column(String(100))                                         # 资产表创建者
    create_time = Column(DateTime, default=datetime.now)                      # 资产表创建时间

class Echart(Base):
    '''图表配置表'''
    __tablename__ = "echart"
    id = Column(Integer, primary_key=True, autoincrement=True)  # id
    name = Column(String(255), nullable=False)                  # 图表名称
    type = Column(Integer, default=1)                           # 图表类型: 1-柱形图,2-折线图,3-饼图
    keyword = Column(String(100), nullable=False)               # 图表数据来源的字段
    table_name = Column(String(20), nullable=False)             # 图表数据来源的资产表
    config = Column(Text, nullable=False)                       # 图表的配置

class File(Base):
    '''文件上传信息表'''
    __tablename__ = "file"
    uuid = Column(String(40), primary_key=True, unique=True, nullable=False)  # 文件的唯一标识
    filename = Column(String(255), nullable=False)                            # 文件名
    filepath = Column(Integer, default=1)                                     # 文件路径: 1-excel_path,2-image_path,0-temp_path
    upload_user = Column(String(100))                                         # 文件上传者
    upload_time = Column(DateTime, default=datetime.now)                      # 文件上传时间

class Header(Base):
    '''资产表表头表'''
    __tablename__ = "header"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    type = Column(Integer, default=1)                     # 表头类型: 1-普通字符串,2-下拉列表,3-日期
    name = Column(String(255), nullable=False)            # 中文名称
    value = Column(String(255), nullable=False)           # 英文字段
    value_type = Column(Integer, default=1)               # 值类型: 1-字符串,2-数字,3-日期,4-大文本
    table_name = Column(String(20), nullable=False)       # 归属哪个资产表
    is_desence = Column(Integer, default=0)               # 是否脱敏: 1-是,0-否
    must_input = Column(Integer, default=0)               # 是否必填: 1-是,0-否
    order = Column(Integer, default=0)                    # 排序
    create_user = Column(String(100))                     # 创建者
    create_time = Column(DateTime, default=datetime.now)  # 创建时间

class Options(Base):
    '''下拉选项表'''
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    option_name = Column(String(255), nullable=False)  # 选项名称
    option_value = Column(String(255), nullable=False) # 选项值
    header_value = Column(String(255), nullable=False) # 归属字段
    table_name =Column(String(20), nullable=False)     # 归属资产表

class Task(Base):
    '''批量探测任务表'''
    __tablename__ = "task"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)  # 任务id
    status = Column(Integer, default=0)                                     # 任务状态: 0-未开始,1-进行中,2-已完成,3-失败
    create_user = Column(String(100))                                       # 任务创建者
    create_time = Column(DateTime, default=datetime.now)                    # 任务创建时间

class DetectResult(Base):
    '''批量探测任务结果表'''
    __tablename__ = "detect_result"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(40), nullable=False)                # 任务id
    ip = Column(String(20), nullable=False)                     # 探测的ip
    status = Column(Integer, nullable=False)                    # 状态: 0-不在线,1-在线,2-未探测
    create_time = Column(DateTime, default=datetime.now)        # 创建时间
    reason = Column(String(255))                                # 未探测原因

class Notify(Base):
    '''到期提醒表'''
    __tablename__ = "notify"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)  # 任务id
    create_user = Column(String(100))                                       # 任务创建者
    create_time = Column(DateTime, default=datetime.now)                    # 任务创建时间

class NotifyMessage(Base):
    '''到期提醒消息表'''
    __tablename__ = "notify_message"
    id = Column(String(40), primary_key=True, unique=True, nullable=False)  # 任务id
    expire_table = Column(String(20), nullable=False)                       # 过期的资产表
    expire_id = Column(Integer, nullable=False)                             # 过期资产id
    receiver = Column(String(100))                                          # 过期提示消息接收者
    create_time = Column(DateTime, default=datetime.now)

def generateManageTable(table_name: str="", *cols):
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
    dynamic_table = Table(table_name, Base.metadata, *cols)
    Base.metadata.create(engine, [dynamic_table])  # 创建动态表格
    return dynamic_table

def initManageTable(table_name: str=""):
    '''
    实例化已有的资产表
    :pararm table_name: 资产表名称
    :return:
    '''
    return Table(table_name, Base.metadata, autoload_with=engine)

def addColumn(table_name: Table, col: Column) -> bool:
    '''
    资产表添加新字段
    :param table_name: 资产表名称
    :param col: 新数据列
    :return:
    '''
    try:
        db_session.execute(table_name.append_column(col).alter())
        db_session.commit()
        return True
    except:
        crmLogger.error(f"添加字段失败")
        return False
    
def alterColumn(table_name: str, col_name: str, source_type: str, dist_type: str) -> bool:
    '''
    资产表修改字段属性
    :param table_name: 资产表名称
    :param col: 新数据列
    :return:
    '''
    # try:
    #     db_session.execute(

init_db()
