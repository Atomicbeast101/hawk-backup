FROM python:3.10-slim

# Setup
RUN mkdir /app
RUN mkdir /log
RUN mkdir /config
RUN mkdir /backups
COPY apt_packages.txt /
RUN apt-get update && apt-get install $(cat /apt_packages.txt) -y
COPY pip_packages.txt /
RUN pip install --no-cache-dir -r /pip_packages.txt
## PostgreSQL Client Installation
RUN /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y && apt-get install postgresql-client -y
## MariaDB/MySQL Client Installation
# N/A
## MongoDB Client Installation
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
RUN echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list
RUN apt-get update && apt-get install mongodb-org-tools -y

# Transfer Files Over
COPY bin /app/bin
COPY app.py /app

# Start App
WORKDIR /app
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
