#!/bin/bash

./permissions.sh

docker rm -f houston
docker run -d -it --publish 3000:5000 --name houston -v $(pwd)/_db/:/opt/houston/_db/ --restart unless-stopped wildme/houston:latest
