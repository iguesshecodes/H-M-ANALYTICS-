# Step 8a: how much revenue could each recommendation protect?
# These are WHAT-IF sizes, not promises. The A/B test is what finds the real number.
# Everything is a share of established yearly revenue (the revenue index from Step 4), so scale does not matter.
import os
import duckdb
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")
DB = os.environ.get("HM_DB", os.path.expanduser("~/hm_work/hm.duckdb"))
con = duckdb.connect(DB, read_only=True)

head = pd.read_csv(os.path.join(OUT, "04_headline.csv")).iloc[0]
models = pd.read_csv(os.path.join(OUT, "05_model_comparison.csv"))
seg = pd.read_csv(os.path.join(OUT, "03_segments_new_customers.csv"), keep_default_na=False)

BASE = float(head["established_rev_index_last_365d"])
LIKELY_GONE = float(head["likely_to_stay_gone_rev_index"])
CAUGHT = float(models[models["model"].str.contains("risk x past spend")]
               .iloc[0]["share_of_churner_revenue_caught"])

COHORT = "first_day BETWEEN DATE '2019-09-20' AND DATE '2020-03-26'"
n_new, n_ret = con.execute(
    "SELECT count(*), sum((days_in_180 >= 2)::int) FROM seg_cust WHERE " + COHORT).fetchone()
n_none = con.execute(
    "SELECT count(*) FROM seg_cust WHERE newsletter = 'None' AND " + COHORT).fetchone()[0]
rev_back = con.execute(
    "SELECT sum(t.price) FROM sample_transactions t JOIN seg_cust c USING (customer_id) "
    "WHERE c." + COHORT.replace("first_day", "first_day") +
    " AND c.days_in_180 >= 2 AND t.t_dat > c.first_day AND t.t_dat < c.first_day + INTERVAL 180 DAY"
).fetchone()[0]
value_per_returner = float(rev_back) / float(n_ret)   # revenue index per customer who came back, first 180 days
YEAR_FACTOR = 365 / 180   # the cohort window is about 6 months; scale to a year (rough)

nl = seg[(seg["dimension"] == "Newsletter") & (seg["segment"] == "Regularly")].iloc[0]["came_back_180_pct"]
nn = seg[(seg["dimension"] == "Newsletter") & (seg["segment"] == "None")].iloc[0]["came_back_180_pct"]
gap = (float(nl) - float(nn)) / 100.0

rows = []
# 1. Contact big spenders who are slipping: pool = revenue likely lost that the risk x spend list catches.
pool1 = LIKELY_GONE * CAUGHT
for save in (0.10, 0.20, 0.30):
    rows.append(("1. Contact big spenders who are slipping", "saves " + str(int(save * 100)) + "% of the caught revenue", pool1 * save))
# 2. Second purchase: +2, +5, +10 points of new customers come back.
for pts in (2, 5, 10):
    extra = n_new * pts / 100.0 * value_per_returner * YEAR_FACTOR
    rows.append(("2. Get new customers to buy a second time", "+" + str(pts) + " points come back", extra))
# 3. Newsletter: 10% or 20% of non-subscribers sign up, and only a quarter or half of the gap is real.
for signup in (0.10, 0.20):
    for real in (0.25, 0.50):
        extra = n_none * signup * gap * real * value_per_returner * YEAR_FACTOR
        rows.append(("3. Push the newsletter sign-up",
                     str(int(signup * 100)) + "% sign up, " + str(int(real * 100)) + "% of the gap is real", extra))

df = pd.DataFrame(rows, columns=["Recommendation", "What if", "Revenue protected (index per year)"])
df["Pct of established revenue"] = (df["Revenue protected (index per year)"] / BASE * 100).round(2)
df["Revenue protected (index per year)"] = df["Revenue protected (index per year)"].round(1)
df.to_csv(os.path.join(OUT, "08_recommendation_sizing.csv"), index=False)

print("Established yearly revenue index:", round(BASE, 1))
print("Value of one new customer who comes back (index, first 180 days):", round(value_per_returner, 2))
print("New customers in cohort:", n_new, "| came back:", n_ret, "| no newsletter:", n_none)
print(df.to_string(index=False))
print("\nSaved to", os.path.join(OUT, "08_recommendation_sizing.csv"))
