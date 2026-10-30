"""Press Play on this file to run Step 3 (the segments).
It runs 03_segments.sql through run_sql.py and prints each result.
Run run_step2.py first, because Step 3 builds on its tables."""
import os, runpy, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["run_sql.py", os.path.join(here, "03_segments.sql"), "03"]
runpy.run_path(os.path.join(here, "run_sql.py"), run_name="__main__")
