FROM python:3.10.13-slim

RUN mkdir /app
WORKDIR /app

COPY . /app
RUN ls -la /app

RUN pip install -r requirements.txt

EXPOSE 80

CMD ["python", "app.py"]

