#!/bin/bash
# @Desc: 数据库定时备份
# @Time: 2024/05/11
# @Usage: 通过cron定时任务 10 1 * * * bash /path/to/backup.sh

# 备份文件路径,容器内部路径
BACKUP_DIR=/data/backup
# 今天日期
TODAY=$(date +"%Y-%m-%d")
# 备份使用到的用户
BACKUP_USER=root
# 备份使用到的用户密码
BACKUP_PWD=123456
# 需要备份的数据库
BACKUP_DB=crm
# 备份命令
docker exec -it mysql mysqldump -u${BACKUP_USER} -p${BACKUP_PWD} ${BACKUP_DB} > ${BACKUP_DIR}/${BACKUP_DB}_${TODAY}.sql
