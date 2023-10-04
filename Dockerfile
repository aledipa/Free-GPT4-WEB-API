FROM python:3-slim

WORKDIR /app
COPY ./requirements.txt /app
COPY ./src/* /app

RUN apt update && apt install gcc python3-dev -y
RUN pip3 install -r requirements.txt

ENV PORT=5500
EXPOSE "$PORT/tcp"

#shell form necessary
SHELL ["python3","/app/FreeGPT4_Server.py"]
ENTRYPOINT ["python3","/app/FreeGPT4_Server.py"]
#CMD ["--cookie-file","/cookies.json"]
