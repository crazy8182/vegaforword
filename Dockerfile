FROM python:3.10-slim

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN pip3 install -U pip && pip3 install -U -r /requirements.txt
RUN mkdir -p /fwdbot
WORKDIR /fwdbot
COPY . /fwdbot/
RUN chmod +x /fwdbot/start.sh
CMD ["/bin/bash", "/fwdbot/start.sh"]
