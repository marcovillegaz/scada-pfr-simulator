"""Make scada_app importable in tests the same way scada_app/main.py does at
runtime (sys.path.insert, not a proper installed package) — so tests can
exercise scada_app modules that don't need PyQt6 (e.g. scenarios/loader.py)
without a Qt dependency at collection time."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scada_app"))
