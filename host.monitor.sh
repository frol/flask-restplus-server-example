#!/bin/bash

ssh houston 'docker logs --tail 1000 --follow houston'
