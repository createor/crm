-- 创建数据库
create database if not exists `crm` character set utf8mb4 collate utf8mb4_general_ci;

-- 创建用户表
create table if not exists `user` (
    `uid` int auto_increment primary key comment "用户id",
    `name` varchar(100) comment "用户昵称",
    `username` varchar(100) not null unique comment "用户名",
    `password` varchar(40) not null comment "密码",
    `create_time` datetime default current_timestamp comment "创建时间",
    `create_user` varchar(100) comment "创建者",
    `update_time` datetime default current_timestamp on update current_timestamp comment "更新时间",
    `update_user` varchar(100) comment "更新者",
    `type` int default 1 comment "类型:1-永久用户,2-临时用户",
    `expire_time` datetime comment "临时用户过期时间",
    `pwd_expire_time` date comment "密码过期时间",
    `status` int default 1 comment "状态:1-有效,0-被锁定,2-过期",
    `company` varchar(100) comment "所属组织、公司",
    `avator` varchar(100) comment "头像图片地址",
    `is_first` int default 1 comment "是否第一次登录:1-是,0-不是"
) engine=InnoDB default charset=utf8mb4;

-- 资产表
create table if not exists `manage` (
    `uuid` varchar(40) comment "id",
    `name` varchar(100) not null unique comment "名称",
    `table_name` varchar(10) not null unique comment "表名"
    `description` text comment "描述信息",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间"
) engine=InnoDB default charset=utf8mb4;

-- 资产表头部
create table if not exists header (
    name commit "名称",
    keyword commit "字段名",
    table commit "所属表",
    status commit "是否展示:1-展示,0-不展示",
    type commit "1-字符串,2-下拉选项"
    order commit "顺序"
) engine=InnoDB default charset=utf8mb4;

-- 资产表图表展示
create table if not exists `echart` (
    `id` comment "id"
    `name` comment "名称",
    `type` comment "类型:1-折线图,2-,3-",
    `keyword` comment "取值字段",
    `table_name` comment "所属表格",
    `config` text comment "配置"
) engine=InnoDB default charset=utf8mb4;

-- 白名单
create table if not exists `white_list` (
    `id` int auto_increment primary key comment "id",
    `ip` varchar(20) not null unique comment "ip",
    `description` varchar(255) comment "备注信息",
    `create_time` datetime default current_timestamp comment "创建时间",
    `create_user` varchar(100) comment "创建者",
) engine=InnoDB default charset=utf8mb4;

-- 日志表
create table if not exists `log` (
    `id` int autoincrement primary key comment "id",
    `ip` varchar(20) comment "操作IP",
    `operate_type` varchar(40) comment "类型",
    `operate_content` text comment "操作内容",
    `operate_user` varchar(100) comment "操作用户",
    `operate_time` datetime default current_timestamp comment "操作时间",
) engine=InnoDB default charset=utf8mb4;

-- 系统配置表
create table if not exists `setting` (
    `type` varchar(40) comment "配置类型",
    `value` int comment "值",
    `desc` varchar(40) comment "注释"
) engine=InnoDB default charset=utf8mb4;

-- 文件表
create table if not exists file (
    uid commit "文件id"
    filename commit "文件名称"
    filepath commit "文件路径"
    upload_user commit "上传者"
    upload_time commit "上传时间"
) engine=InnoDB default charset=utf8mb4;

-- 初始化
insert into user(name, username, password, type, pwd_expire_time, status, avator, is_first) value("管理员", "admin", "07967d4a89a0172d1f20c53424d1860e", 1, "2099-12-31", 1, "/images/crm.png", 1);

insert into `setting` (`type`, `value`, `desc`) values 
("enable_failed", 0, "是否开启失败锁定,1-开启,0-关闭"),
("enable_white", 0, "是否开启白名单模式,1-开启,0-关闭"),
("enable_single", 0, "是否开启单点登录功能,1-开启,0-关闭"),
("failed_count", 3, "失败次数");


-- 创建索引
create index
