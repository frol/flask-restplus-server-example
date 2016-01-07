FROM frolvlad/alpine-python3

COPY tasks /opt/www/tasks
COPY config.py /opt/www/
COPY app/requirements.txt /opt/www/app/

RUN apk add --no-cache --virtual=build_dependencies musl-dev gcc python3-dev libffi-dev && \
    cd /opt/www && \
    pip install -r tasks/requirements.txt && \
    invoke app.dependencies.install && \
    rm -rf ~/.cache/pip && \
    apk del build_dependencies

COPY . /opt/www/

RUN chown -R nobody /opt/www/

USER nobody
WORKDIR /opt/www/
CMD [ "invoke", "app.run", "--no-install-dependencies", "--host", "0.0.0.0" ]
