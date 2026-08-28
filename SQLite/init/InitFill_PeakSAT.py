import os
import sys

init_directory = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(init_directory, ".."))

# Add KPIHub root to sys.path so `lib.*` imports resolve regardless of cwd.
sys.path.insert(0, _root)
os.chdir(_root)

from lib.handlers.CustomerHandler import add_peak_sat_file_id
from lib.config import DB_PATH
from lib.KPIHubConnection import KPIHub_Conn

add_peak_sat_file_id("Cadent", 2206415797785, KPIHub_Conn)

print(f"Updated Peak SAT location for Cadent in {DB_PATH}")
