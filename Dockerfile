FROM python:3.12

ADD app.tar.gz /app

WORKDIR /app

RUN pip install -r requirements.txt -i https://pypi.doubanio.com/simple/ --default-timeout=100

EXPOSE 8080/TCP

VOLUME ["/app/app/logs", "/app/app/files", "/app/app/socket"]

CMD [ "python", "/app/run.py" ]
