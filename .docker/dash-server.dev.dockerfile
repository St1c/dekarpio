FROM python:3.8-slim-buster
RUN apt-get update
RUN apt-get install nano

RUN mkdir wd
WORKDIR wd
COPY dash-server/requirements.txt .
RUN pip3 install -r requirements.txt

COPY dash-server/ ./

CMD [ "gunicorn", "--workers=5", "--threads=1", "--reload", "-b 0.0.0.0:3002", "app:server"]