#!/bin/bash

# docker save --output houston.wildme.tar wildme/houston:latest
# rsync -azP houston.wildme.tar houston:/opt/houston/
# docker save wildme/houston:latest | bzip2 | pv | ssh houston 'bunzip2 | docker load'

echo "Sending Docker Image"
docker save wildme/houston:latest | pv | ssh houston 'docker load'

echo "Sending Run Script"
rsync -azP host.run.sh houston:/opt/houston/host.run.sh --no-perms --omit-dir-times

echo "Sending Permissions Script"
rsync -azP host.permissions.sh houston:/opt/houston/host.permissions.sh --no-perms --omit-dir-times

echo "Sending Backup Script"
rsync -azP host.backup.sh houston:/opt/houston/host.backup.sh --no-perms --omit-dir-times

echo "Pre-send Database: Backup existing content"
ssh houston '/opt/houston/host.backup.sh'

echo "Sending Database"
ssh houston '/opt/houston/host.permissions.sh'
# rsync -azP _db/ houston:/opt/houston/_db/ --no-perms --omit-dir-times
# rsync -azP houston:/opt/houston/_db/ _db/
rsync -azP _db/secrets.py houston:/opt/houston/_db/secrets.py --no-perms --omit-dir-times
