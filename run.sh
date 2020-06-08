#!/bin/bash

docker rm -f houston
docker run -d --user $(id -u) -it --publish 3000:5000 --name houston -v $(pwd)/_db/:/opt/houston/_db/ wildme/houston:latest
