FROM frolvlad/alpine-python3

ENV API_SERVER_HOME=/opt/www
COPY tasks "$API_SERVER_HOME/tasks"
COPY config.py "$API_SERVER_HOME/"
COPY app/requirements.txt "$API_SERVER_HOME/app/"

RUN apk add --no-cache --virtual=build_dependencies musl-dev gcc python3-dev libffi-dev && \
    cd /opt/www && \
    pip install -r tasks/requirements.txt && \
    invoke app.dependencies.install && \
    rm -rf ~/.cache/pip && \
    apk del build_dependencies

COPY . /opt/www/

RUN chown -R nobody "$API_SERVER_HOME/" && \
    if [ ! -e "$API_SERVER_HOME/local_config.py" ]; then \
        cp "$API_SERVER_HOME/local_config.py.template" "$API_SERVER_HOME/local_config.py" ; \
    fi

USER nobody
WORKDIR /opt/www/
CMD [ "invoke", "app.run", "--no-install-dependencies", "--host", "0.0.0.0" ]
