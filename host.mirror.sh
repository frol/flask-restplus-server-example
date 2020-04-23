#!/usr/bin/env bash

echo "Mirroring Prodiction Database"
rsync -azP houston:/opt/houston/_db/ _db/ --exclude secrets.py
