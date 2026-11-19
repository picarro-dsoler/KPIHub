# KPIHub Weekly KPI dashboard

Plotly Dash over **`kpihub."Weekly_KPI"`** on **PostgreSQL** (`kpihub-postgis`). Same table layout as [`ExcelOutput.py`](../Python/processes/global/ExcelOutput.py).

Port **8052** (does not use dash-demo **8050** or system-health-alarm **8051**).

## Run (recommended — Docker)

No `pip` / `pandas` on the host needed:

```bash
cd /home/dsoler/david-repos/KPIHub/dashboard
chmod +x run.sh
./run.sh
```

Or:

```bash
docker network create kpihub-net 2>/dev/null || true
docker compose up --build -d
```

Open **http://localhost:8052**

Connects to **`PGHOST=kpihub-postgis`** on `kpihub-net` (same as `PostGIS/DBInit/Dockerrun`).

Stop:

```bash
docker compose down
```

## Run locally (optional venv)

Use this only if you want to run `python app.py` on the host (not `python3` without a venv):

```bash
cd /home/dsoler/david-repos/KPIHub/dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PGHOST=localhost PGPORT=5432 PGUSER=dsoler PGPASSWORD=dsoler PGDATABASE=KPIHub_EU
python app.py
```

## Database prerequisites

After a fresh `kpihub-postgis` volume, apply KPIHub SQL (from repo root), e.g.:

```bash
docker exec -i kpihub-postgis psql -U dsoler -d KPIHub_EU -v ON_ERROR_STOP=1 \
  < KPIHub/PostGIS/PSQL_routines/init/ingesters/InitKPIHub.sql
docker exec -i kpihub-postgis psql -U dsoler -d KPIHub_EU -v ON_ERROR_STOP=1 \
  < KPIHub/PostGIS/PSQL_routines/init/output_views/Weekly_KPI.sql
```

The UI shows a setup hint if `kpihub."KPI_Customer"` or `Weekly_KPI` is missing.