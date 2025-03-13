FROM python:3.11-alpine

RUN pip install poetry==2.1.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY . /acura
WORKDIR /acura

RUN poetry install
RUN rm -rf $POETRY_CACHE_DIR

ENTRYPOINT [ "poetry", "run", "python", "." ]
