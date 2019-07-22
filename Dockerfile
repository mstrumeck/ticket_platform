FROM python:3.7

RUN apt update
RUN apt install -y postgresql \
    python-psycopg2 \
    libpq-dev

WORKDIR /tp
COPY ticket_platform /tp
COPY requirements.txt /tp/requirements.txt
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate

CMD gunicorn ticket_platform.wsgi:application