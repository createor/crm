-- 数据库的定时计划任务: 删除一个月前的日志信息
-- 查看数据库是否开启计划任务: SHOW VARIABLES LIKE 'event_scheduler';
-- 如果没有则开启: SET GLOBAL event_scheduler = ON;
create event if not exists delete_old_data 
on schedule every 1 day -- 每天执行一次
starts timestamp(current_date() + interval 1 day) -- 任务开始时间: 从明天这个时间段开始执行
do
begin
    declare cutoff_date date;  -- 声明变量
    set cutoff_date = date_sub(current_date(), interval 1 month);  -- 变量赋值: 获取1个月前日期
	delete from logwhere operate_time > cutoff_date;  -- 删除1个月前数据
end;
