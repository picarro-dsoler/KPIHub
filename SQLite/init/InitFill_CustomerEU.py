import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

import reverse_geocoder as rg

from locallib.picarrodb import *
from locallib.query import *

from lib.tables.IngesterTables import *
from lib.handlers.CustomerHandler import *
from lib.config import *
from lib.KPIHubConnection import *

ISO3166 = {
    "AD": "Andorra", "AL": "Albania", "AT": "Austria", "BA": "Bosnia and Herzegovina",
    "BE": "Belgium", "BG": "Bulgaria", "BY": "Belarus", "CH": "Switzerland",
    "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany", "DK": "Denmark",
    "EE": "Estonia", "ES": "Spain", "FI": "Finland", "FR": "France",
    "GB": "United Kingdom", "GR": "Greece", "HR": "Croatia", "HU": "Hungary",
    "IE": "Ireland", "IS": "Iceland", "IT": "Italy", "LI": "Liechtenstein",
    "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "MC": "Monaco",
    "MD": "Moldova", "ME": "Montenegro", "MK": "North Macedonia", "MT": "Malta",
    "NL": "Netherlands", "NO": "Norway", "PL": "Poland", "PT": "Portugal",
    "RO": "Romania", "RS": "Serbia", "RU": "Russia", "SE": "Sweden",
    "SI": "Slovenia", "SK": "Slovakia", "SM": "San Marino", "UA": "Ukraine",
    "VA": "Vatican City", "XK": "Kosovo",
}


def make_sequential_country_id(idx):
    return f"00000000-0000-0000-0000-{idx + 1:012d}"


query = Query("""SELECT Customer.Id as CustomerId, Name as Name,
                Location.Latitude as Latitude,
                Location.Longitude as Longitude,
                Location.Description as Location
                FROM Customer
                LEFT JOIN Location ON Customer.Id = Location.CustomerId
                WHERE Active = 1""")
customer_eu1 = query.execute(EU1_Conn)
customer_eu1["DBLocation"] = "EU1"
customer_eu2 = query.execute(EU2_Conn)
customer_eu2["DBLocation"] = "EU2"
customer_df = pd.concat([customer_eu1, customer_eu2])

customer_df = customer_df[
    ~customer_df["Name"].str.upper().str.contains("PICARRO", case=False)
    & ~customer_df["Name"].str.upper().str.contains("TEST", case=False)
]
customer_df = customer_df[~customer_df["Name"].str.strip().str.upper().eq("ITALGAS-SERVICE")]

located = customer_df.dropna(subset=["Latitude", "Longitude"]).copy()
if not located.empty:
    results = rg.search(
        list(zip(located["Latitude"].astype(float), located["Longitude"].astype(float))),
        mode=1,
    )
    located["Country"] = [ISO3166.get(r["cc"], r["cc"]) for r in results]
    country_by_customer = located.groupby("CustomerId")["Country"].agg(
        lambda s: s.mode().iloc[0] if not s.mode().empty else None
    )
else:
    country_by_customer = pd.Series(dtype=object)

customer_df = customer_df.groupby(["CustomerId", "Name", "DBLocation"], as_index=False).agg(
    Latitude=("Latitude", "mean"),
    Longitude=("Longitude", "mean"),
    LocationCount=("CustomerId", "size"),
)
customer_df["Country"] = customer_df["CustomerId"].map(country_by_customer)

customer_df = customer_df[customer_df["Country"] != "US"]
customer_df.loc[customer_df["Country"] == "GH", "Country"] = "Italy"
country_list = customer_df["Country"].dropna().unique()
country_list = pd.DataFrame(country_list, columns=["Country"]).reset_index(drop=True)
country_list.insert(0, "CountryId", [make_sequential_country_id(i) for i in range(len(country_list))])
country_list.rename(columns={"Country": "Name"}, inplace=True)

KPI_Country.reinit_table(arguments={"db_path": DB_PATH})
KPI_Country.update_table(
    arguments={"DataFrame": country_list, "db_path": DB_PATH, "PrimaryKey": "CountryId"}
)

for _, row in customer_df.iterrows():
    customer_name = row["Name"]
    db_location = row["DBLocation"]
    country = row["Country"] if pd.notna(row["Country"]) else None
    conn = EU1_Conn if db_location == "EU1" else EU2_Conn
    add_customer(customer_name, conn, country=country)

print(DB_PATH)
