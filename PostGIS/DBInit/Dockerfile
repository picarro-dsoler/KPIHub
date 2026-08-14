FROM postgis/postgis:16-3.5

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-server-dev-16 \
        freetds-dev \
        freetds-bin \
        libsybdb5 \
        ca-certificates \
        git \
        build-essential \
        make \
        gcc && \
    git clone --branch v2.0.5 https://github.com/tds-fdw/tds_fdw.git /tmp/tds_fdw && \
    cd /tmp/tds_fdw && \
    make USE_PGXS=1 && \
    make USE_PGXS=1 install && \
    rm -rf /tmp/tds_fdw && \
    apt-get purge -y git build-essential make gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/init.sql
