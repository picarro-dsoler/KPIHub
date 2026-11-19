# Standalone build (no prebuilt kpihub image). Bookworm + pgdg matches FDW/PostGIS packages.
FROM postgres:16-bookworm

# ogr_fdw + tds_fdw + PostGIS; GDAL MSSQLSpatial needs FreeTDS in odbcinst.ini.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        postgresql-16-postgis-3 \
        postgresql-16-postgis-3-scripts \
        postgresql-16-ogr-fdw \
        postgresql-16-tds-fdw \
        gdal-bin \
        ca-certificates \
        unixodbc \
        tdsodbc \
        freetds-bin \
        freetds-common; \
    cp /usr/share/tdsodbc/odbcinst.ini /etc/odbcinst.ini; \
    rm -rf /var/lib/apt/lists/*

COPY init-kpihub.sql /docker-entrypoint-initdb.d/01-init-kpihub.sql
COPY init-systemhealth.sh /docker-entrypoint-initdb.d/02-init-systemhealth.sh
RUN chmod +x /docker-entrypoint-initdb.d/02-init-systemhealth.sh