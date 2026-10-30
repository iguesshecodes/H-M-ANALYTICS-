"""Press Play on this file to run Step 2 (the retention funnel).
It simply runs 02_retention_funnel.sql through run_sql.py and prints each result."""
import os, runpy, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["run_sql.py", os.path.join(here, "02_retention_funnel.sql"), "02"]
runpy.run_path(os.path.join(here, "run_sql.py"), run_name="__main__")
