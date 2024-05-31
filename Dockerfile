FROM python:3.12-slim

WORKDIR /app/
COPY --chown=www-data:www-data . .

RUN apt update && apt install gcc chromium libsqlite3-dev -y
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

WORKDIR /app/src

ENV PORT=5500
EXPOSE "$PORT/tcp"

#shell form necessary
SHELL ["python3","FreeGPT4_Server.py"]
ENTRYPOINT ["python3","FreeGPT4_Server.py"]
#CMD ["--cookie-file","/cookies.json"]