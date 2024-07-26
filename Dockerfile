# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster as builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.10-slim-buster

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --from=builder /app /app

EXPOSE 5000

ENV FLASK_ENV=production
ENV FLASK_APP=run.py

CMD ["flask", "run", "--host=0.0.0.0"]
