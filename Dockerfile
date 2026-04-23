FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ .
RUN mkdir -p /data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
