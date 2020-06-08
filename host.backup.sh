#!/bin/bash

TZ=America/Los_Angeles
TIMESTAMP=$(date +%Y-%m-01-%H-%M-%S)
mkdir -p /opt/houston/_backup/
tar -zcvf /opt/houston/_backup/_db.$TIMESTAMP.tar.gz /opt/houston/_db
