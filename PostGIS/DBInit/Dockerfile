FROM postgis/postgis:16-3.5

# ogr_fdw + GDAL MSSQLSpatial need an ODBC driver (FreeTDS) registered in odbcinst.ini.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-16-ogr-fdw \
        gdal-bin \
        ca-certificates \
        unixodbc \
        tdsodbc \
        freetds-bin \
        freetds-common && \
    cp /usr/share/tdsodbc/odbcinst.ini /etc/odbcinst.ini && \
    rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/init.sql
