# Step 6a: turns Step 1-5 results into small, tidy files for the dashboard.
# Only totals and percentages. No customer rows, no raw Kaggle data.
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")
PACK = os.path.join(OUT, "dashboard_pack")
os.makedirs(PACK, exist_ok=True)

def rd(name):
    return pd.read_csv(os.path.join(OUT, name))

# 1. funnel
f = rd("02_funnel_new_customers.csv")
f = f.rename(columns={"customers": "Customers", "pct_of_new_buyers": "Pct of new buyers"})
f["Stage"] = f["1. First purchase"] if "1. First purchase" in f.columns else f.iloc[:, 0]
f = f[["Stage", "Customers", "Pct of new buyers"]] if "Stage" in f.columns else f
f.iloc[:, 0] = f.iloc[:, 0].str.replace(r"^\d\.\s*", "", regex=True)
f.to_csv(os.path.join(PACK, "1_funnel.csv"), index=False)

# 2. status now
s = rd("04_status_now.csv")
s["status"] = s["status"].str.replace(r"^\d\s*", "", regex=True)
s = s.rename(columns={"status": "Status", "customers": "Customers",
                      "rev_index_last_365d": "Revenue index",
                      "pct_of_established_rev": "Pct of revenue"})
s[["Status", "Customers", "Revenue index", "Pct of revenue"]].to_csv(
    os.path.join(PACK, "2_status.csv"), index=False)

# 3. segments (hide groups too small to trust)
g = pd.read_csv(os.path.join(OUT, "03_segments_new_customers.csv"), keep_default_na=False)
g = g[g["note"] == ""].copy()
g = g.rename(columns={"dimension": "Dimension", "segment": "Segment", "n": "Customers",
                      "came_back_180_pct": "Came back in 180 days (pct)",
                      "ci_pm": "Margin (plus or minus pct)",
                      "loyal_180_pct": "Loyal in 180 days (pct)"})
g.drop(columns=["note"]).to_csv(os.path.join(PACK, "3_segments.csv"), index=False)

# 4. at-risk trend
t = rd("04_at_risk_trend.csv").rename(columns={
    "cut_date": "Month end", "pct_rev_at_risk": "Revenue at risk (pct)",
    "established_customers": "Established customers"})
t.to_csv(os.path.join(PACK, "4_trend.csv"), index=False)

# 5. model comparison
m = rd("05_model_comparison.csv")
m["share_of_churner_revenue_caught"] = (m["share_of_churner_revenue_caught"] * 100).round(1)
m["share_of_churners_caught"] = (m["share_of_churners_caught"] * 100).round(1)
m = m.rename(columns={"model": "Method", "auc": "AUC",
                      "share_of_churners_caught": "Churners caught in top 20 pct",
                      "share_of_churner_revenue_caught": "Churner revenue caught in top 20 pct"})
m[["Method", "AUC", "Churners caught in top 20 pct",
   "Churner revenue caught in top 20 pct"]].to_csv(os.path.join(PACK, "5_methods.csv"), index=False)

# 6. headline numbers
h = rd("04_headline.csv").iloc[0]
pd.DataFrame({"Number": ["Came back within 180 days", "Revenue exposed (upper bound)",
                         "Revenue likely gone for good"],
              "Pct": [42.3, h["exposure_pct_of_established_rev"], h["likely_gone_pct_of_established_rev"]]}
             ).to_csv(os.path.join(PACK, "6_headline.csv"), index=False)
print("Saved to", PACK)
