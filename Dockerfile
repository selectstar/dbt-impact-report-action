FROM python:3.10.13-bookworm

COPY . /app/
WORKDIR /app

RUN chmod +x entrypoint.sh

RUN pip install -r requirements.txt

ENTRYPOINT ["/app/entrypoint.sh"]
