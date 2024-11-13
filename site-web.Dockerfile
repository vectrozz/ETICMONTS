#FROM python:3.13.0-alpine3.20
FROM python:3.13.0-slim

RUN apt-get update 
RUN apt-get install -y python3-pip

COPY requirements.txt /etc/requirements.txt
RUN pip install -r /etc/requirements.txt

COPY templates /etc/templates
COPY app-docker.py /etc/app-docker.py


