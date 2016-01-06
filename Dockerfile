FROM frolvlad/alpine-python3

COPY app/requirements.txt /opt/www/app/
COPY tasks /opt/www/tasks

RUN apk add --no-cache --virtual=build_dependencies musl-dev gcc python3-dev libffi-dev && \
    cd /opt/www && \
    pip install -r tasks/requirements.txt && \
    invoke app.dependencies.install && \
    apk del build_dependencies

COPY . /opt/www/

RUN chown -R nobody /opt/www/

USER nobody
WORKDIR /opt/www/
CMD [ "invoke", "app.run", "--no-install-dependencies", "--host", "0.0.0.0" ]
