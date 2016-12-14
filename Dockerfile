FROM frolvlad/alpine-python3

ENV API_SERVER_HOME=/opt/www
WORKDIR "$API_SERVER_HOME"
COPY "./requirements.txt" "./"
COPY "./app/requirements.txt" "./app/"
COPY "./config.py" "./"
COPY "./tasks" "./tasks"

RUN apk add --no-cache --virtual=build_dependencies musl-dev gcc python3-dev libffi-dev && \
    cd /opt/www && \
    pip install -r tasks/requirements.txt && \
    invoke app.dependencies.install && \
    rm -rf ~/.cache/pip && \
    apk del build_dependencies

COPY "./" "./"

RUN chown -R nobody "." && \
    if [ ! -e "./local_config.py" ]; then \
        cp "./local_config.py.template" "./local_config.py" ; \
    fi

USER nobody
CMD [ "invoke", "app.run", "--no-install-dependencies", "--host", "0.0.0.0" ]
