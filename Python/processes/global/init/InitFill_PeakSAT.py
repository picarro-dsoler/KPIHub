import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from bootstrap_paths import activate

activate()

from lib.handlers.CustomerHandler import add_peak_sat_file_id

add_peak_sat_file_id("Cadent", 2206415797785)
add_peak_sat_file_id("SGN", 2482855861926)
