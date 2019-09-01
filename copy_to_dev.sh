#!/bin/sh
rsync -avP \
    --exclude=.git --exclude=__pycache__ --exclude=/tmp \
    --delete \
    . \
    coreos1:~/pload/
ssh coreos1 -t /home/core/bin/docker-compose -f pload/docker-compose.yml build
