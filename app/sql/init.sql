-- 创建数据库
create database if not exists `crm` character set utf8mb4 collate utf8mb4_general_ci;

-- 创建用户表
create table if not exists `crm_user` (
    `uid` int auto_increment primary key comment "用户id",
    `name` varchar(100) comment "用户昵称",
    `username` varchar(100) not null unique comment "用户名",
    `password` varchar(40) not null comment "密码",
    `create_time` datetime default current_timestamp comment "创建时间",
    `create_user` varchar(100) comment "创建者",
    `update_time` datetime default current_timestamp on update current_timestamp comment "更新时间",
    `update_user` varchar(100) comment "更新者",
    `type` tinyint(1) default 1 comment "类型:1-永久用户,2-临时用户",
    `expire_time` datetime comment "临时用户过期时间",
    `pwd_expire_time` date comment "密码过期时间",
    `status` tinyint(1) default 1 comment "状态:1-有效,0-被锁定,2-过期",
    `company` varchar(100) comment "所属组织、公司",
    `avator` varchar(100) default "default" comment "头像图片地址",
    `is_first` int default 1 comment "是否第一次登录:1-是,0-不是",
    unique key `username_idx` (`username`)
) engine=InnoDB default charset=utf8mb4;

-- 资产表
create table if not exists `crm_manage` (
    `uuid` varchar(40) not null unique primary key comment "id",
    `name` varchar(255) not null unique comment "资产表名称",
    `table_name` varchar(20) not null unique comment "资产表别名"
    `table_image` varchar(20) default "crm" comment "资产表背景图片",
    `description` varchar(255) comment "描述信息",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间",
    `update_user` varchar(100) comment "更新者",
    `update_time` datetime default current_timestamp on update current_timestamp comment "更新时间",
    unique key `uuid_idx` (`uuid`),
    unique key `name_idx` (`name`),
    unique key `table_name_idx` (`table_name`)
) engine=InnoDB default charset=utf8mb4;

-- 资产表头部
create table if not exists `crm_header` (
    `id` int auto_increment primary key comment "id",
    `type` tinyint(1) default 1 comment "列类型:1-字符串,2-下拉选项",
    `name` varchar(255) not null comment "列名称",
    `value` varchar(255) not null comment "列别名",
    `value_type` tinyint(1) default 1 comment "列值类型",
    `table_name` varchar(20) not null comment "所属资产表别名",
    `is_unique` tinyint(1) default 0 comment "是否唯一:1-是,0-否",
    `is_desence` tinyint(1) default 0 comment "是否脱敏:1-是,0-否",
    `must_input` tinyint(1) default 0 comment "是否必填:1-是,0-否",
    `order` int default 0 comment "排列顺序",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间",
    `update_user` varchar(100) comment "更新者",
    `update_time` datetime default current_timestamp on update current_timestamp comment "更新时间"
) engine=InnoDB default charset=utf8mb4;

-- 下拉选项取值表
create table if not exists `crm_options` (
    `id` int auto_increment primary key comment "id",
    `option_name` varchar(255) not null comment "选项名称",
    `option_value` varchar(255) not null comment "选项值",
    `header_value` varchar(255) not null comment "所属列别名",
    `table_name` varchar(20) not null comment "所属资产表别名"
) engine=InnoDB default charset=utf8mb4;

-- 资产表图表展示
create table if not exists `crm_echart` (
    `id` int auto_increment primary key comment "id",
    `name` varchar(255) not null comment "图表名称",
    `type` tinyint(1) default 1 comment "类型:1-饼图,2-柱形图,3-折线图",
    `keyword` varchar(100) not null comment "取值字段",
    `date_keyword` varchar(100) comment "日期字段",
    `table_name` varchar(20) comment "所属资产表别名"
) engine=InnoDB default charset=utf8mb4;

-- 白名单
create table if not exists `crm_white_list` (
    `id` int auto_increment primary key comment "id",
    `ip` varchar(20) not null unique comment "白名单ip",
    `description` varchar(255) comment "备注信息",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间",
    unique key `ip_idx` (`ip`)
) engine=InnoDB default charset=utf8mb4;

-- 日志表
create table if not exists `crm_log` (
    `id` int autoincrement primary key comment "日志id",
    `ip` varchar(20) not null comment "操作IP",
    `operate_type` varchar(40) not null comment "操作类型",
    `operate_content` varchar(255) not null comment "操作内容",
    `operate_user` varchar(100) not null comment "操作用户",
    `operate_time` datetime default current_timestamp comment "操作时间",
) engine=InnoDB default charset=utf8mb4;

-- 系统配置表
create table if not exists `crm_setting` (
    `type` varchar(40) not null primary key comment "配置类型",
    `value` tinyint(1) default 0 comment "值",
    `desc` varchar(40) comment "注释"
) engine=InnoDB default charset=utf8mb4;

-- 文件表
create table if not exists `crm_file` (
    `uuid` varchar(40) not null unique primary key comment "文件id",
    `filename` varchar(255) not null comment "文件名称",
    `filepath` tinyint(1) default 1 comment "文件路径:1-excel_path,2-image_path,0-temp_path",
    `affix` varchar(10) not null comment "文件后缀",
    `password` varchar(20) comment "文件密码",
    `upload_user` varchar(100) comment "上传者",
    `upload_time` datetime default current_timestamp comment "上传时间",
    unique key `uuid_idx` (`uuid`)
) engine=InnoDB default charset=utf8mb4;

-- 初始化数据表
--- 初始化管理员用户
insert into `crm_user`(`name`, `username`, `password`, `pwd_expire_time`) value("管理员", "admin", "07967d4a89a0172d1f20c53424d1860e", "2099-12-31");
--- 初始化系统配置
insert into `setting` (`type`, `value`, `desc`) values 
("enable_failed", 1, "是否开启失败锁定,1-开启,0-关闭"),
("enable_white", 1, "是否开启白名单模式,1-开启,0-关闭"),
("enable_single", 1, "是否开启单点登录功能,1-开启,0-关闭"),
("failed_count", 3, "登陆失败次数"),
("enable_enable_watermark", 1, "是否开启水印,1-开启,0-关闭");
--- 初始化背景图片文件
insert into `crm_file` (`uuid`, `filename`, `filepath`, `affix`) values
("crm", "crm.png", 2, "png"),
("default", "default.png", 2, "png");
--- 初始化白名单
insert into `crm_white_list` (`ip`, `description`) value("127.0.0.1", "本地地址");

-- 创建联合索引
