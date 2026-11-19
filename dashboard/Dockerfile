FROM python:3.12-slim

WORKDIR /app

COPY KPIHub/dashboard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY KPIHub/dashboard/ ./dashboard/
COPY KPIHub/Python/ ./Python/
COPY KPIHub/PostGIS/PSQL_routines/ ./PostGIS/PSQL_routines/

ENV PYTHONPATH=/app/dashboard:/app/Python
ENV KPIHUB_DASH_PORT=8052

WORKDIR /app/dashboard
EXPOSE 8052

CMD ["python", "app.py"]