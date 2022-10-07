# Start django api with gunicorn
FROM python:3.8.5-slim-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

# start server
CMD gunicorn core.wsgi:application --bind 0.0.0.0:$PORT