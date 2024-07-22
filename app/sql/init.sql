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
    `is_first` tinyint(1) default 1 comment "是否第一次登录:1-是,0-不是",
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
    `is_ip` tinyint(1) default 0 comment "是否IP:1-是,0-否",
    `must_input` tinyint(1) default 0 comment "是否必填:1-是,0-否",
    `length` int default 0 comment "长度",
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
    `value` tinyint(1) default 0 comment "值:0-关闭,1-开启",
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

-- 任务表
create table if not exists `crm_task` (
    `id` varchar(40) not null unique primary key comment "任务id",
    `name` varchar(255) not null comment "任务名称",
    `keyword` varchar(255) not null comment "任务关键字",
    `table_name` varchar(20) not null comment "所属资产表别名",
    `status` tinyint(1) default 0 comment "任务状态0-未开始,1-进行中,2-已完成,3-失败",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间",
    unique key `uuid_idx` (`id`)
) engine=InnoDB default charset=utf8mb4;

-- 任务结果表
create table if not exists `crm_detect_result` (
    `id` int autoincrement primary key comment "id",
    `task_id` varchar(40) not null comment "任务id",
    `ip` varchar(20) not null comment "ip",
    `status` tinyint(1) not null comment "状态:0-离线,1-在线",
    `reason` varchar(255) comment "原因",
    `create_time` datetime default current_timestamp comment "创建时间"
) engine=InnoDB default charset=utf8mb4;

-- 过期通知任务表
create table if not exists `crm_notify` (
    `id` varchar(40) not null unique primary key comment "任务id",
    `name` varchar(255) not null comment "任务名称",
    `keyword` varchar(20) not null comment "任务关键字",
    `table_name` varchar(20) not null comment "所属资产表别名",
    `status` tinyint(1) default 1 comment "任务状态0-停止,1-开始",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间",
    `update_user` varchar(100) comment "更新者",
    `update_time` datetime default current_timestamp on update current_timestamp comment "更新时间",
    unique key `uuid_idx` (`id`)
) engine=InnoDB default charset=utf8mb4;

-- 用户通知表
create table if not exists `crm_notice` (
    `id` int autoincrement primary key comment "id",
    `message` varchar(40) not null comment "信息",
    `notify_id` varchar(40) not null comment "任务id",
    `is_read` tinyint(1) default 0 comment "是否已读:0-未读,1-已读",
    `create_time` datetime default current_timestamp comment "创建时间",
    `update_time` datetime default current_timestamp on update current_timestamp comment "更新时间"
) engine=InnoDB default charset=utf8mb4;

-- 历史记录表
create table if not exists `crm_history` (
    `id` varchar(40) not null unique primary key comment "id",
    `file_uuid` varchar(40) comment "文件id",
    `err_file` varchar(40) comment "错误文件id",
    `mode` tinyint(1) not null comment "模式:1-导入,2-导出",
    `status` tinyint(1) default 0 comment "状态:0-排队中,1-在执行,2-执行成功,3-执行失败",
    `table_name` varchar(20) not null comment "资产表别名",
    `create_user` varchar(100) comment "创建者",
    `create_time` datetime default current_timestamp comment "创建时间",
    unique key `uuid_idx` (`id`)
) engine=InnoDB default charset=utf8mb4;

-- 初始化数据表
--- 初始化管理员用户
insert into `crm_user` (`name`, `username`, `password`, `pwd_expire_time`) select "管理员", "admin", "07967d4a89a0172d1f20c53424d1860e", "2099-12-31" where not exists (select 1 from `crm_user` where `username` = "admin");
--- 初始化系统配置
insert into `crm_setting` (`type`, `value`, `desc`) select "enable_failed", 1, "是否开启失败锁定,1-开启,0-关闭" where not exists (select 1 from `crm_setting` where `type` = "enable_failed");
insert into `crm_setting` (`type`, `value`, `desc`) select "enable_white", 0, "是否开启白名单模式,1-开启,0-关闭" where not exists (select 1 from `crm_setting` where `type` = "enable_white");
insert into `crm_setting` (`type`, `value`, `desc`) select "enable_single", 1, "是否开启单点登录功能,1-开启,0-关闭" where not exists (select 1 from `crm_setting` where `type` = "enable_single");
insert into `crm_setting` (`type`, `value`, `desc`) select "failed_count", 3, "登陆失败次数" where not exists (select 1 from `crm_setting` where `type` = "failed_count");
insert into `crm_setting` (`type`, `value`, `desc`) select "enable_watermark", 1, "是否开启水印,1-开启,0-关闭" where not exists (select 1 from `crm_setting` where `type` = "enable_watermark");
--- 初始化背景图片文件
insert into `crm_file` (`uuid`, `filename`, `filepath`, `affix`) select "crm", "crm.png", 2, "png" where not exists (select 1 from `crm_file` where `uuid` = "crm");
insert into `crm_file` (`uuid`, `filename`, `filepath`, `affix`) select "default", "default.png", 2, "png" where not exists (select 1 from `crm_file` where `uuid` = "default");
insert into `crm_file` (`uuid`, `filename`, `filepath`, `affix`) select "nodata", "nodata.png", 2, "png" where not exists (select 1 from `crm_file` where `uuid` = "nodata");
--- 初始化白名单
insert into `crm_white_list` (`ip`, `description`) select "127.0.0.1", "本地地址" where not exists (select 1 from `crm_white_list` where `ip` = "127.0.0.1");
