FROM python:3.7


RUN apt update
RUN apt install -y postgresql \
    python-psycopg2 \
    libpq-dev

WORKDIR /tp
COPY ticket_platform /tp
COPY requirements.txt /tp/requirements.txt
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate

RUN chmod 777 /usr/local/bin/docker-entrypoint.sh \
    && ln -s /usr/local/bin/docker-entrypoint.sh /

CMD gunicorn ticket_platform.wsgi:application