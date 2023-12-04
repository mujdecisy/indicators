FROM python:3.10.13-slim

RUN mkdir /app
WORKDIR /app

COPY * .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]

