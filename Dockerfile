FROM python:3.7

ENV INSTALL_PATH=/opt/houston

WORKDIR "${INSTALL_PATH}"

RUN apt update \
 # && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
 && apt update \
 && apt upgrade -y \
 && apt install -y \
        # Build
        build-essential \
        musl-dev \
        gcc \
        libffi-dev \
        # Python 3
        python3-dev \
        # Convenience
        htop \
        tmux \
        vim \
        git \
        # Magic with python-magic (MIME-type parser)
        libmagic1 \
        # nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY . .

RUN cd ${INSTALL_PATH} \
 && ./venv.sh \
 && virtualenv/houston3.7/bin/pip install -U pip \
 && virtualenv/houston3.7/bin/pip install -r app/requirements.txt \
 && virtualenv/houston3.7/bin/pip install -r tasks/requirements.txt \
 && virtualenv/houston3.7/bin/pip install utool ipython \
 && rm -rf ~/.cache/pip \
 && chown -R nobody .

USER nobody

CMD ["virtualenv/houston3.7/bin/invoke", "app.run", "--host", "0.0.0.0" ]
