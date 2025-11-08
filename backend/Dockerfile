FROM python:3.12-alpine

RUN apk add --no-cache \
    gcc musl-dev python3-dev libffi-dev \
    postgresql-libs postgresql-dev

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Saratov

WORKDIR /app


COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt


COPY . /app/
