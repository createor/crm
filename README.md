# CRM 资产管理系统

本系统涵盖了管理员和普通用户权限,管理员用户可以单独管理系统用户、查看操作日志、修改系统配置，普通用户可以使用资产管理用户，创建、更新资产信息,支持用户首次登录进行引导说明,支持对用户上传的文件进行安全扫描,有效防止病毒的入侵渗透......

## 技术选型

代理服务器： openresty

前端：layui框架

后端：Flask

缓存：redis

数据库：mysql

其他组件：clamav(安全扫描)

## 架构说明

## 目录介绍

- |--app（后端服务）
- |----src（源码目录）
- |----utils（常用函数集合目录）
- |----static（前端需要使用到的静态文件目录）
- |----templates（模板html文件目录）
- |----temp（生成需要下载的文件目录）
- |----files（上传文件目录）
- |------ excels（上传的表格文件目录）
- |------images（上传的图片文件目录）
- |----logs（日志目录）
- |----sql（数据库相关脚本）
- |------init.sql（数据库初始化脚本）
- |------script（脚本目录）
- |--------backup.sh（数据库定时备份脚本）
- |--------clearExpireLog.sql（数据库删除数据任务脚本）
- |--run.py（启动后端服务的入口文件）
- |--requirements.txt（声明依赖的文件）
- |--Dockerfile（用于生成后端服务镜像的文件）

## 使用说明

```bash
# 生成后端镜像,在Dockerfile所在目录执行以下命令
docker build --no-cache . -t app:latest
# 通过docker-compose命令启动服务,在docker-compose.yaml文件所在目录执行以下命令
docker-compose up -d
# 停止服务
docker-compose down -d
```

访问：http://服务所在ip，会自动重定向到https协议



## 维护说明

### calamav病毒库更新说明

```bash
# 通过此命令将最新病毒库下载到当前路径的data目录下
# 将data目录下的文件上传至服务端的clamav服务的病毒库挂载路径后,重启容器即可
docker run -it --rm --name clamav -v $(pwd)/data:/var/lib/clamav -e CLAMAV_NO_FRESHCLAMD=false clamav/clamav:1.2_base
```

## FAQ
