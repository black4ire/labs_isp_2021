
FROM python:3.8.3-slim

WORKDIR /usr/src/lab3

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && apt-get -y install libpq-dev gcc \
  && pip install psycopg2
# RUN apk update \
#     && apk add postgresql-dev gcc python3-dev musl-dev \
#     && pip install psycopg2 \
#     && apk add jpeg-dev zlib-dev libjpeg \
#     && pip install Pillow 


RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . /usr/src/lab3

ENTRYPOINT ["/usr/src/lab3/entrypoint.sh"]