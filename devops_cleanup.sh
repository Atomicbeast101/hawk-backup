# Remove directories
rm -rf tests

# Stop docker containers
docker compose stop

# Cleanup containers/volumes
docker compose rm -f
