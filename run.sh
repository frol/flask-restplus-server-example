#!/usr/bin/env bash

docker rm -f houston
docker run -d -it --publish 5000:5000 --name houston -v $(pwd)/_db/:/opt/houston/_db/ wildme/houston:latest
