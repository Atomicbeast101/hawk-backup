ARG OS_VERSION=latest
FROM ubuntu:${OS_VERSION}

ARG ARCH=amd64

# Setup
RUN mkdir /app
RUN mkdir /log
RUN mkdir /config
RUN mkdir /backups
COPY apt_packages.txt /
RUN apt-get update && apt-get install $(cat /apt_packages.txt) -y
COPY pip_packages.txt /
RUN pip install --no-cache-dir --break-system-packages -r /pip_packages.txt
## PostgreSQL Client Installation
RUN /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y \
    && apt-get install postgresql-client -y
## MariaDB/MySQL Client Installation
# N/A
## MongoDB Client Installation
# N/A - using Python pymongo package

# Transfer Files Over
COPY bin /app/bin
COPY gunicorn.conf.py /app
COPY app.py /app

# Run as Different User
RUN useradd -m -s /bin/bash hawkapp
USER hawkapp

# Start App
WORKDIR /app
EXPOSE 5000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app"]
