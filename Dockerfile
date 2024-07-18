# docker build --no-cache -t crm:latest .
FROM python:3.12-slim

# 声明工作目录
WORKDIR /usr/local/crm

# 拷贝源码
ADD app.tar.gz /usr/local/crm

# 安装依赖
RUN pip install -r requirements.txt -i https://pypi.doubanio.com/simple/ --default-timeout=100 && pip cache purge

# 暴露端口
EXPOSE 8080/TCP

# 挂载目录
VOLUME ["/usr/local/crm/app/logs", "/usr/local/crm/app/files", "/usr/local/crm/app/temp"]

# 启动程序
CMD [ "python", "/usr/local/crm/run.py" ]
