FROM python:3.10.11
ENV PYTHONUNBUFFEREDBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/server

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .