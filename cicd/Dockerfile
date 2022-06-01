FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get upgrade -y && apt-get clean && pip install -r /app/requirements.txt --no-cache-dir
CMD python script.py