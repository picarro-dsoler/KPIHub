FROM postgis/postgis:16-3.5

RUN apt-get update && \
apt-get install -y --no-install-recommends postgresql-contrib && \
rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/init.sql