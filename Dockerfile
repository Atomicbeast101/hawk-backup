ARG UBUNTU_VERSION=latest
ARG ARCHITECTURE=amd64

FROM ubuntu:$UBUNTU_VERSION

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
RUN wget https://downloads.mongodb.com/compass/mongodb-mongosh_2.4.2_${ARCHITECTURE}.deb -O /mongodb-mongosh_2.4.2_${ARCHITECTURE}.deb \
    && sudo apt-get install /mongodb-mongosh_2.4.2_${ARCHITECTURE}.deb -y \
    && rm -rf /mongodb-mongosh_2.4.2_${ARCHITECTURE}.deb

# Transfer Files Over
COPY bin /app/bin
COPY app.py /app

# Start App
WORKDIR /app
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
