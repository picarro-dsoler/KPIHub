import os
import sys
from datetime import datetime

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

import pandas as pd
from boxsdk import Client, CCGAuth
from dotenv import load_dotenv

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.handlers.CustomerHandler import *
from lib.config import *
from lib.KPIHubConnection import *

load_dotenv(override=True)

CLIENT_ID = os.getenv("BOXCLIENTID")
CLIENT_SECRET = os.getenv("BOXCLIENTSECRET")
assert CLIENT_ID and CLIENT_SECRET, "Set BOXCLIENTID and BOXCLIENTSECRET in your environment"

auth = CCGAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, enterprise_id=20888)
client = Client(auth)

FOLDER_ID = "370739222165"  # EU-ANALYTICAL-CUSTOMER-OUTPUT

EXCLUDED_FOLDERS = {
    "ANALYZERS-LOCATION-TRACKING",
    "CUSTOMER GLOBAL LEAK EXTRACTIONS",
    "GAS-DATA-BOT-EU-OUTPUT",
    "MASTER VIEW REPORTS",
}

KPI_SUBFOLDER_NAME = "KPI"
SKIP_KPI_FOLDERS = {"UK-CADENT"}

CUSTOMER_ALIASES = {
    "WALES & WEST UTILITIES": "WALES AND WEST UTILITIES",
}


def list_folder_items(client, folder_id, limit=1000):
    folder = client.folder(folder_id).get()
    items = []
    offset = 0
    while True:
        batch = list(
            client.folder(folder_id).get_items(
                limit=limit,
                offset=offset,
                fields=["id", "name", "type", "size", "modified_at", "created_at"],
            )
        )
        if not batch:
            break
        items.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return folder, items


def get_or_create_subfolder(client, parent_folder_id, subfolder_name):
    parent = client.folder(parent_folder_id)
    for item in parent.get_items(limit=1000, fields=["id", "name", "type"]):
        if item.type == "folder" and item.name == subfolder_name:
            return item.id
    return parent.create_subfolder(subfolder_name).id


def normalize_customer(name):
    if pd.isna(name):
        return name
    key = str(name).strip().upper()
    key = CUSTOMER_ALIASES.get(key, key)
    return key.upper()


folder, items = list_folder_items(client, FOLDER_ID)
print(f"Folder: {folder.name} (id={folder.id})")
print(f"Total items: {len(items)}")

rows = [
    {
        "type": item.type,
        "id": item.id,
        "folder_name": item.name,
        "size": getattr(item, "size", None),
        "modified_at": getattr(item, "modified_at", None),
        "created_at": getattr(item, "created_at", None),
    }
    for item in sorted(items, key=lambda x: (x.type, x.name.lower()))
    if item.name not in EXCLUDED_FOLDERS
]

folder_df = pd.DataFrame(rows)

kpi_folder_ids = []
for _, row in folder_df.iterrows():
    if row["folder_name"] in SKIP_KPI_FOLDERS:
        kpi_folder_ids.append("375691804502")
        continue

    kpi_id = get_or_create_subfolder(client, row["id"], KPI_SUBFOLDER_NAME)
    kpi_folder_ids.append(kpi_id)

folder_df["kpi_folder_id"] = kpi_folder_ids
folder_df[["country", "customer"]] = folder_df["folder_name"].str.split("-", n=1, expand=True)

kpi_customer = Query(
    "SELECT CustomerId, Name FROM KPI_Customer"
).execute(KPIHub_Conn)

folder_df["customer_key"] = folder_df["customer"].map(normalize_customer)
kpi_customer["customer_key"] = kpi_customer["Name"].map(normalize_customer)

folder_df = pd.merge(
    folder_df,
    kpi_customer.rename(columns={"Name": "NameKPI"}),
    on="customer_key",
    how="left",
).drop(columns=["customer_key"])

output = folder_df[["CustomerId", "kpi_folder_id"]].dropna()
output["LastUpdated"] = datetime.now()
output.rename(columns={"kpi_folder_id": "BoxFolderId"}, inplace=True)
KPI_OutputExcelLocation.update_table(
    arguments={"DataFrame": output, "db_path": DB_PATH, "PrimaryKey": "CustomerId"}
)

print(f"Updated {len(output)} KPI output folder locations in {DB_PATH}")
