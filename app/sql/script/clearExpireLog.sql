-- 数据库的定时计划任务: 删除一个月前的日志信息
-- 查看数据库是否开启计划任务: SHOW VARIABLES LIKE "event_scheduler";
-- 如果没有则开启: SET GLOBAL event_scheduler = ON;
-- 查看当前时间: SELECT NOW();
-- 查看事件: SHOW EVENTS;
create event if not exists delete_old_log 
on schedule every 1 day -- 每天执行一次
-- starts timestamp(current_date() + interval 1 day) -- 任务开始时间: 从明天这个时间段开始执行
starts "2024-07-06 21:30:00"  -- 直接指定开始时间
on completion preserve
do
begin
	delete from `crm`.`crm_log` where crm_log.operate_time < date_sub(current_date(), interval 1 month);  -- 删除1个月前数据
end;
