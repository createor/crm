FROM python:3.12

COPY app.tar.gz /app

RUN cd /app && pip install -r requirements.txt

CMD [ "python", "/app/run.py" ]
