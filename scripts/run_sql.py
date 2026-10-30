"""Runs a .sql file made of blocks marked '-- name: xyz'. Saves each result to outputs/<prefix>_<xyz>.csv.
Usage: python3 scripts/run_sql.py scripts/02_retention_funnel.sql 02"""
import duckdb, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db = os.path.join(os.path.expanduser("~"), "hm_work", "hm.duckdb")
con = duckdb.connect(db)
sql_file, prefix = sys.argv[1], sys.argv[2]
text = open(sql_file).read()
# split into statements on ';' at end of line, keep the '-- name:' tag attached to the next statement
for stmt in [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]:
    m = re.search(r"--\s*name:\s*(\w+)", stmt)
    if m:
        name = m.group(1)
        df = con.execute(stmt).df()
        path = os.path.join(ROOT, "outputs", f"{prefix}_{name}.csv")
        df.to_csv(path, index=False)
        print(f"\n== {name}  ({len(df)} rows) -> {os.path.basename(path)}")
        print(df.to_string(index=False))
    else:
        con.execute(stmt)
