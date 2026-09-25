import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from bootstrap_paths import activate

activate()

from lib.handlers.CustomerHandler import add_peak_sat_file_id
from lib.config import DB_PATH
from lib.KPIHubConnection import KPIHub_Conn

add_peak_sat_file_id("Cadent", 2206415797785, KPIHub_Conn)
add_peak_sat_file_id("SGN", 2482855861926, KPIHub_Conn)

print(f"Updated Peak SAT location for Cadent in {DB_PATH}")
