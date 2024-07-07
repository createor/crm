@echo off
rem window创建定时备份任务

rem 需要备份的数据库
set db_name=crm

rem 备份使用到的用户
set db_user=backup

rem 备份使用到的用户的密码
set db_pass=123456

rem 备份路径
set backup_path=C:\

rem 获取当前日期
set today=%date

rem 使用mysqldump备份
"C:\\mysqldump" -u %db_user% -p%db_pass% %db_name% > "%backup_path%\%db_name%_%today%.sql"