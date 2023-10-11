FROM python:3.11-slim

WORKDIR /app/
COPY . .

RUN apt update && apt install gcc -y
RUN pip3 install -r requirements.txt

WORKDIR /app/src

ENV PORT=5500
EXPOSE "$PORT/tcp"

#shell form necessary
SHELL ["python3","FreeGPT4_Server.py"]
ENTRYPOINT ["python3","FreeGPT4_Server.py"]
#CMD ["--cookie-file","/cookies.json"]
