FROM mhart/alpine-node

ENV HOME=/tmp
WORKDIR /opt

COPY "./.npmignore" "./"
COPY "./dist/" "./"

USER nobody
