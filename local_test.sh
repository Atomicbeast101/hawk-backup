# Create directories if it doesn't exists
mkdir -p tests/sftp
mkdir -p tests/app
mkdir -p tests/app/config
mkdir -p tests/app/log
mkdir -p tests/app/tmp

# Copy config to tests/app
cp --update=none settings.yml tests/app/config/settings.yml

# Start docker containers
docker compose up --build
