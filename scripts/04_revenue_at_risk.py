"""Step 4: revenue at risk.
Idea: compare how long a customer has been quiet with THEIR OWN usual gap between shopping days.
  ratio = days since last shopping day / max(their median gap, 30 days)
  On track < 1  |  Slipping 1 to 2  |  Drifting 2 to 4  |  Gone quiet 4+
Only 'established' customers (3+ shopping days) get a rhythm. Others are counted separately.
Step A backtests the rule in the past (did quiet people really not come back?).
Step B applies it at the end of the data (22 Sep 2020) and adds up the money.
Revenue is a 'revenue index' (prices are scrambled in this dataset), never pounds.
"""
import duckdb, os, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect(os.path.join(os.path.expanduser("~"), "hm_work", "hm.duckdb"))
OUT = os.path.join(ROOT, "outputs")
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
END = "2020-09-22"

def build(cut, with_outcome):
    """One row per established customer, using ONLY data up to the cut date."""
    name = "status_" + cut.replace("-", "")
    outcome = (f"""(SELECT 1 FROM sample_transactions f WHERE f.customer_id = s.customer_id
                    AND f.t_dat > DATE '{cut}' AND f.t_dat <= DATE '{cut}' + INTERVAL 90 DAY LIMIT 1) IS NOT NULL"""
               if with_outcome else "NULL")
    con.execute(f"""
    CREATE OR REPLACE TABLE {name} AS
    WITH v AS (SELECT DISTINCT customer_id, t_dat AS d FROM sample_transactions WHERE t_dat <= DATE '{cut}'),
    g AS (SELECT customer_id, d, date_diff('day', lag(d) OVER (PARTITION BY customer_id ORDER BY d), d) AS gap FROM v),
    s AS (SELECT customer_id, count(*) AS n_days, max(d) AS last_day, median(gap) AS med_gap FROM g GROUP BY 1),
    r AS (SELECT customer_id, sum(price) AS rev365 FROM sample_transactions
          WHERE t_dat <= DATE '{cut}' AND t_dat > DATE '{cut}' - INTERVAL 365 DAY GROUP BY 1)
    SELECT s.customer_id, s.n_days, s.last_day, s.med_gap, coalesce(r.rev365, 0) AS rev365,
           date_diff('day', s.last_day, DATE '{cut}') AS days_since,
           date_diff('day', s.last_day, DATE '{cut}') / greatest(s.med_gap, 30) AS ratio,
           CASE WHEN s.n_days < 3 THEN 'Not established (1-2 days)'
                WHEN date_diff('day', s.last_day, DATE '{cut}') / greatest(s.med_gap, 30) < 1 THEN '1 On track'
                WHEN date_diff('day', s.last_day, DATE '{cut}') / greatest(s.med_gap, 30) < 2 THEN '2 Slipping'
                WHEN date_diff('day', s.last_day, DATE '{cut}') / greatest(s.med_gap, 30) < 4 THEN '3 Drifting'
                ELSE '4 Gone quiet' END AS status,
           {outcome} AS bought_next_90d
    FROM s LEFT JOIN r USING (customer_id)""")
    return name

# ---------- A. BACKTEST ----------
rows = []
for cut in ["2019-12-24", "2020-03-24", "2020-06-24"]:
    t = build(cut, True)
    df = con.execute(f"""SELECT '{cut}' AS cut_date, status, count(*) AS customers,
        round(100.0*avg(bought_next_90d::int),1) AS bought_again_in_90d_pct
        FROM {t} WHERE status NOT LIKE 'Not%' GROUP BY 2 ORDER BY 2""").df()
    rows.append(df)
bt = pd.concat(rows)
bt.to_csv(os.path.join(OUT, "04_backtest_by_status.csv"), index=False)
print("== A. BACKTEST: of people in each status on the cut date, how many bought in the next 90 days?")
print(bt.pivot(index="status", columns="cut_date", values="bought_again_in_90d_pct").to_string())
print()
print(bt.pivot(index="status", columns="cut_date", values="customers").to_string())

# pooled chance of NOT coming back, per status (used for the cautious 'likely gone' number)
pooled = con.execute("""
SELECT status, count(*) n, round(100.0*avg((NOT bought_next_90d)::int),1) AS stays_gone_pct FROM (
  SELECT status, bought_next_90d FROM status_20191224 UNION ALL
  SELECT status, bought_next_90d FROM status_20200324 UNION ALL
  SELECT status, bought_next_90d FROM status_20200624) WHERE status NOT LIKE 'Not%' GROUP BY 1 ORDER BY 1""").df()
pooled.to_csv(os.path.join(OUT, "04_pooled_stay_gone.csv"), index=False)
print("\n== pooled chance of NOT buying in next 90 days"); print(pooled.to_string(index=False))

# ---------- B. TODAY (end of data) ----------
t = build(END, False)
# coverage: how much of last-year revenue do established customers cover?
cov = con.execute(f"""SELECT count(*) AS customers_shopped_last_365d_or_before, round(sum(rev365),1) AS rev_index_last_365d,
  round(100.0*sum(CASE WHEN status NOT LIKE 'Not%' THEN rev365 END)/sum(rev365),1) AS pct_rev_from_established
  FROM {t} WHERE rev365 > 0""").df()
print("\n== coverage"); print(cov.to_string(index=False))

now = con.execute(f"""
SELECT status, count(*) AS customers, round(sum(rev365),1) AS rev_index_last_365d,
  round(100.0*sum(rev365)/sum(sum(rev365)) OVER (),1) AS pct_of_established_rev,
  round(avg(days_since),0) AS avg_days_quiet, round(avg(med_gap),0) AS avg_usual_gap
FROM {t} WHERE status NOT LIKE 'Not%' GROUP BY 1 ORDER BY 1""").df()
now.to_csv(os.path.join(OUT, "04_status_now.csv"), index=False)
print("\n== B. STATUS AT 22 SEP 2020 (established customers, 3+ shopping days)"); print(now.to_string(index=False))

# headline numbers
sg = dict(zip(pooled.status, pooled.stays_gone_pct))
rk = con.execute(f"SELECT status, sum(rev365) AS rev FROM {t} WHERE status IN ('3 Drifting','4 Gone quiet') GROUP BY 1").df()
tot_est = con.execute(f"SELECT sum(rev365) FROM {t} WHERE status NOT LIKE 'Not%'").fetchone()[0]
exposed = rk.rev.sum()
likely = sum(r.rev * sg[r.status] / 100 for r in rk.itertuples())
head = pd.DataFrame([{
  "established_rev_index_last_365d": round(tot_est, 1),
  "at_risk_exposure_drifting_plus_gone": round(exposed, 1),
  "exposure_pct_of_established_rev": round(100 * exposed / tot_est, 1),
  "likely_to_stay_gone_rev_index": round(likely, 1),
  "likely_gone_pct_of_established_rev": round(100 * likely / tot_est, 1)}])
head.to_csv(os.path.join(OUT, "04_headline.csv"), index=False)
print("\n== HEADLINE"); print(head.T.to_string(header=False))

# ---------- C. WHO IS AT RISK (segments) ----------
seg = con.execute(f"""
WITH b AS (SELECT s.*, c.age_band, c.club_status, c.newsletter, c.first_channel
           FROM {t} s JOIN seg_cust c USING (customer_id) WHERE s.status NOT LIKE 'Not%'),
long AS (
 SELECT 'Age' AS dimension, age_band AS segment, status, rev365 FROM b
 UNION ALL SELECT 'Club status', club_status, status, rev365 FROM b
 UNION ALL SELECT 'Newsletter', newsletter, status, rev365 FROM b
 UNION ALL SELECT 'First purchase channel', first_channel, status, rev365 FROM b)
SELECT dimension, segment, count(*) AS customers, round(sum(rev365),1) AS rev_index,
  round(100.0*sum(CASE WHEN status IN ('3 Drifting','4 Gone quiet') THEN rev365 END)/sum(rev365),1) AS pct_rev_at_risk,
  round(100.0*avg((status IN ('3 Drifting','4 Gone quiet'))::int),1) AS pct_customers_at_risk,
  CASE WHEN count(*) < 500 THEN 'too small to trust' ELSE '' END AS note
FROM long GROUP BY 1,2 ORDER BY 1,2""").df()
seg.to_csv(os.path.join(OUT, "04_at_risk_by_segment.csv"), index=False)
print("\n== C. AT-RISK SHARE BY SEGMENT"); print(seg.to_string(index=False))

# ---------- D. TREND at month-end cuts ----------
trend = []
for cut in pd.date_range("2019-09-30", "2020-08-31", freq="ME").strftime("%Y-%m-%d").tolist() + [END]:
    tt = build(cut, False)
    r = con.execute(f"""SELECT '{cut}' AS cut_date,
       round(100.0*sum(CASE WHEN status IN ('3 Drifting','4 Gone quiet') THEN rev365 END)/sum(rev365),1) AS pct_rev_at_risk,
       count(*) AS established_customers FROM {tt} WHERE status NOT LIKE 'Not%'""").df()
    trend.append(r)
trend = pd.concat(trend); trend.to_csv(os.path.join(OUT, "04_at_risk_trend.csv"), index=False)
print("\n== D. TREND of at-risk share of revenue (rule applied at each month end)"); print(trend.to_string(index=False))
