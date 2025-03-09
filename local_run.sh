# Create directories if it doesn't exists
mkdir -p tests/sftp
mkdir -p tests/app
mkdir -p tests/app/config
mkdir -p tests/app/log
mkdir -p tests/app/tmp
mkdir -p tests/app/backups

# Copy config to tests/app
cp --update=none settings.yml tests/app/config/settings.yml

# Run containers locally
if [ "$1" == "standalone" ]; then
    echo "Starting containers [detached]..."
    docker compose up -d --build
else
    echo "Starting containers [attached]..."
    docker compose up --build
fi
