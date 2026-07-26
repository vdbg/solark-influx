FROM python:3.11-alpine

RUN addgroup -S solark && adduser -S solark -G solark

USER solark

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH /home/solark/.local/bin:$PATH

COPY requirements.txt     /app/

RUN pip install --no-cache-dir --disable-pip-version-check --upgrade pip
RUN pip install --no-cache-dir -r ./requirements.txt

COPY *.py                 /app/
COPY template.config.toml /app/

ENTRYPOINT python main.py
