#!/bin/bash

/opt/houston/host.permissions.sh

docker rm -f houston
docker run -d -it --publish 5000:5000 --name houston -v /opt/houston/_db/:/opt/houston/_db/ --restart unless-stopped wildme/houston:latest

# /bin/yes | docker system prune -a
docker images -a
docker ps -a
