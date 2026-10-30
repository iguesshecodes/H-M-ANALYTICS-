# Full refresh: re-runs steps 1 to 6, then writes the monthly summary. Takes a while.
import os, sys, runpy
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["07_monthly_summary.py", "--refresh"]
runpy.run_path(os.path.join(here, "07_monthly_summary.py"), run_name="__main__")
