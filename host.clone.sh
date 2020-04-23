#!/usr/bin/env bash

echo "Mirroring Production Database (with Secrets)"
rsync -azP houston:/opt/houston/_db/ _db/
