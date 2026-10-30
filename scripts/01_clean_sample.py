"""Step 1: load, profile, clean, and sample the H&M data.
Run from the project folder:  python3 scripts/01_clean_sample.py
Everything is deterministic: same input gives the same 10% sample.
"""
import duckdb, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(os.path.expanduser("~"), "hm_work"); os.makedirs(WORK, exist_ok=True); DB = os.path.join(WORK, "hm.duckdb")
OUT = os.path.join(ROOT, "outputs", "01_profile.txt")
SAMPLE_PCT = 10  # keep 1 in 10 customers

con = duckdb.connect(DB)
con.execute("SET memory_limit='1500MB'")
con.execute("SET temp_directory='" + os.path.join(WORK, "tmp") + "'")

log = open(OUT, "w")
def say(title, sql=None):
    print(f"\n== {title}", flush=True); log.write(f"\n== {title}\n")
    if sql:
        df = con.execute(sql).df()
        txt = df.to_string(index=False)
        print(txt, flush=True); log.write(txt + "\n")
    log.flush()

t0 = time.time()
con.execute(f"""
CREATE OR REPLACE TABLE customers_raw AS
SELECT * FROM read_csv('{ROOT}/customers.csv', header=true,
  types={{'customer_id':'VARCHAR','postal_code':'VARCHAR','club_member_status':'VARCHAR',
          'fashion_news_frequency':'VARCHAR','age':'DOUBLE','FN':'DOUBLE','Active':'DOUBLE'}})
""")
con.execute(f"""
CREATE OR REPLACE TABLE transactions_raw AS
SELECT * FROM read_csv('{ROOT}/transactions_train.csv', header=true,
  types={{'t_dat':'DATE','customer_id':'VARCHAR','article_id':'VARCHAR',
          'price':'DOUBLE','sales_channel_id':'INTEGER'}})
""")
con.execute(f"""
CREATE OR REPLACE TABLE articles AS
SELECT * FROM read_csv('{ROOT}/articles.csv', header=true, all_varchar=true)
""")
print(f"loaded in {time.time()-t0:.0f}s", flush=True)

say("ROW COUNTS", """
SELECT 'customers_raw' t, count(*) n FROM customers_raw
UNION ALL SELECT 'transactions_raw', count(*) FROM transactions_raw
UNION ALL SELECT 'articles', count(*) FROM articles""")

say("CUSTOMERS: missing values", """
SELECT count(*) n_rows, count(DISTINCT customer_id) distinct_ids,
 sum((age IS NULL)::int) age_null,
 sum((club_member_status IS NULL)::int) club_null,
 sum((fashion_news_frequency IS NULL)::int) news_null,
 sum((FN IS NULL)::int) fn_null, sum((Active IS NULL)::int) active_null
FROM customers_raw""")
say("CUSTOMERS: club_member_status", "SELECT club_member_status, count(*) n FROM customers_raw GROUP BY 1 ORDER BY 2 DESC")
say("CUSTOMERS: fashion_news_frequency", "SELECT fashion_news_frequency, count(*) n FROM customers_raw GROUP BY 1 ORDER BY 2 DESC")
say("CUSTOMERS: age", """
SELECT min(age) min_age, quantile_cont(age,0.5) median_age, max(age) max_age,
 sum((age<16)::int) under16, sum((age>90)::int) over90 FROM customers_raw""")

say("TRANSACTIONS: basics", """
SELECT count(*) n_rows, count(DISTINCT customer_id) buyers, min(t_dat) first_day, max(t_dat) last_day,
 min(price) min_price, round(avg(price),5) avg_price, max(price) max_price,
 sum((price<=0)::int) nonpositive_price FROM transactions_raw""")
say("TRANSACTIONS: sales channel", "SELECT sales_channel_id, count(*) n, round(sum(price),1) revenue_index FROM transactions_raw GROUP BY 1 ORDER BY 1")
say("TRANSACTIONS: exact duplicate rows (same customer, item, day, price, channel)", """
SELECT count(*) AS rows_that_are_repeats FROM (
 SELECT 1 FROM transactions_raw GROUP BY t_dat,customer_id,article_id,price,sales_channel_id HAVING count(*)>1)""")
say("LINKS: transaction customers missing from customers table", """
SELECT count(DISTINCT t.customer_id) n FROM transactions_raw t
LEFT JOIN customers_raw c USING(customer_id) WHERE c.customer_id IS NULL""")
say("LINKS: customers who never bought", """
SELECT count(*) n FROM customers_raw c WHERE NOT EXISTS
 (SELECT 1 FROM transactions_raw t WHERE t.customer_id=c.customer_id)""")

# ---- CLEAN ----
con.execute("""
CREATE OR REPLACE TABLE customers AS
SELECT customer_id,
  CASE WHEN age BETWEEN 16 AND 90 THEN CAST(age AS INTEGER) END AS age,
  coalesce(upper(trim(club_member_status)),'UNKNOWN') AS club_status,
  CASE upper(trim(fashion_news_frequency))
       WHEN 'REGULARLY' THEN 'Regularly' WHEN 'MONTHLY' THEN 'Monthly'
       WHEN 'NONE' THEN 'None' ELSE 'Unknown' END AS newsletter,
  postal_code
FROM customers_raw""")

# ---- SAMPLE (deterministic: hash of the customer id) ----
con.execute(f"""
CREATE OR REPLACE TABLE sample_customers AS
SELECT * FROM customers WHERE hash(customer_id) % 100 < {SAMPLE_PCT}""")
con.execute("""
CREATE OR REPLACE TABLE sample_transactions AS
SELECT t.t_dat, t.customer_id, t.article_id, t.price, t.sales_channel_id
FROM transactions_raw t SEMI JOIN sample_customers c USING(customer_id)""")

say("SAMPLE: size and sanity check against full data", """
SELECT 'full' which, (SELECT count(*) FROM customers) customers,
  (SELECT count(*) FROM transactions_raw) transactions,
  (SELECT round(avg(age),2) FROM customers) avg_age,
  (SELECT round(avg(price),5) FROM transactions_raw) avg_price
UNION ALL SELECT 'sample', (SELECT count(*) FROM sample_customers),
  (SELECT count(*) FROM sample_transactions),
  (SELECT round(avg(age),2) FROM sample_customers),
  (SELECT round(avg(price),5) FROM sample_transactions)""")
say("SAMPLE: club share, full vs sample", """
SELECT f.club_status, round(100.0*f.n/f.tot,2) full_pct, round(100.0*s.n/s.tot,2) sample_pct FROM
 (SELECT club_status, count(*) n, sum(count(*)) OVER () tot FROM customers GROUP BY 1) f
 JOIN (SELECT club_status, count(*) n, sum(count(*)) OVER () tot FROM sample_customers GROUP BY 1) s USING(club_status)
 ORDER BY 2 DESC""")
print(f"\nDONE in {time.time()-t0:.0f}s. Profile saved to outputs/01_profile.txt", flush=True)
