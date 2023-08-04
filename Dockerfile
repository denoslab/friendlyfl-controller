FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y gcc python3-dev musl-dev libmagic1 libffi-dev netcat-traditional \
    build-essential libpq-dev

COPY poetry.lock pyproject.toml /app/

RUN pip3 install poetry

RUN poetry install

RUN pip3 install django-bootstrap-v5

COPY . /app/

RUN chmod +x ./entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]
