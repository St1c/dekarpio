FROM python:3.10-slim
RUN apt-get update
RUN apt-get install nano

RUN apt-get install -y build-essential gcc libglpk-dev glpk-utils

RUN mkdir wd
WORKDIR wd
COPY flask-server/requirements.txt .
RUN pip3 install -r requirements.txt

COPY flask-server/ ./

CMD [ "gunicorn", "--workers=5", "--threads=1", "--reload", "-b 0.0.0.0:3003", "app:server"]