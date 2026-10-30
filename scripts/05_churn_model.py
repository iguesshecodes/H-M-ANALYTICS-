"""Step 5: a simple, honest churn model.

Question: for a regular customer (3+ shopping days) on a given date, will they buy ANYTHING in the next 90 days?
"Churn" here means: no purchase in the next 90 days. (Quiet, not necessarily lost.)

Honest setup:
  * Every feature uses only data up to the date we predict from (no peeking at the future).
  * We train on two earlier dates and test on a LATER date the model never saw.
  * We compare the model against the simple rule from Step 4 (the 'ratio'). A model that cannot beat it is not worth using.
  * Club and newsletter status are left out on purpose: they are end-of-data snapshots and could leak the future.
"""
import os
import numpy as np, pandas as pd, duckdb
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
con = duckdb.connect(os.path.join(os.path.expanduser("~"), "hm_work", "hm.duckdb"), read_only=True)
pd.set_option("display.width", 200)

TRAIN_CUTS = ["2019-12-24", "2020-03-24"]
TEST_CUT = "2020-06-24"
FEATURES = ["n_days", "days_since", "med_gap", "ratio", "days_90", "days_180",
            "rev90", "rev365", "items365", "ch1_share", "tenure_days", "age"]

def features(cut):
    """One row per regular customer, built only from data up to `cut`, plus what happened in the next 90 days."""
    return con.execute(f"""
    WITH v AS (SELECT DISTINCT customer_id, t_dat AS d FROM sample_transactions WHERE t_dat <= DATE '{cut}'),
    g AS (SELECT customer_id, d, date_diff('day', lag(d) OVER (PARTITION BY customer_id ORDER BY d), d) AS gap FROM v),
    s AS (SELECT customer_id, count(*) AS n_days, min(d) AS first_day, max(d) AS last_day, median(gap) AS med_gap FROM g GROUP BY 1),
    a AS (SELECT customer_id,
            count(DISTINCT CASE WHEN t_dat >  DATE '{cut}' - INTERVAL 90  DAY THEN t_dat END) AS days_90,
            count(DISTINCT CASE WHEN t_dat >  DATE '{cut}' - INTERVAL 180 DAY THEN t_dat END) AS days_180,
            sum(CASE WHEN t_dat > DATE '{cut}' - INTERVAL 90  DAY THEN price ELSE 0 END) AS rev90,
            sum(CASE WHEN t_dat > DATE '{cut}' - INTERVAL 365 DAY THEN price ELSE 0 END) AS rev365,
            count(CASE WHEN t_dat > DATE '{cut}' - INTERVAL 365 DAY THEN 1 END) AS items365,
            avg((sales_channel_id = 1)::int) AS ch1_share
          FROM sample_transactions WHERE t_dat <= DATE '{cut}' GROUP BY 1)
    SELECT s.customer_id, s.n_days, s.med_gap,
           date_diff('day', s.last_day, DATE '{cut}') AS days_since,
           date_diff('day', s.last_day, DATE '{cut}') / greatest(s.med_gap, 30) AS ratio,
           a.days_90, a.days_180, a.rev90, a.rev365, a.items365, a.ch1_share,
           date_diff('day', s.first_day, DATE '{cut}') AS tenure_days,
           c.age,
           (SELECT 1 FROM sample_transactions f WHERE f.customer_id = s.customer_id
              AND f.t_dat > DATE '{cut}' AND f.t_dat <= DATE '{cut}' + INTERVAL 90 DAY LIMIT 1) IS NULL AS churned
    FROM s JOIN a USING (customer_id) JOIN sample_customers c USING (customer_id)
    WHERE s.n_days >= 3""").df()

train = pd.concat([features(c) for c in TRAIN_CUTS], ignore_index=True)
test = features(TEST_CUT)
Xtr, ytr = train[FEATURES], train["churned"].astype(int).values
Xte, yte = test[FEATURES], test["churned"].astype(int).values
rev_te = test["rev365"].values

print("== DATA")
print(f"train rows {len(train):,} (dates {TRAIN_CUTS}), churn rate {ytr.mean():.1%}")
print(f"test  rows {len(test):,} (date {TEST_CUT}),   churn rate {yte.mean():.1%}")

# ---- three contenders ----
lr = make_pipeline(SimpleImputer(strategy="median"), FunctionTransformer(np.log1p), StandardScaler(),
                   LogisticRegression(max_iter=1000))
gbm = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                     min_samples_leaf=50, early_stopping=False, random_state=42)
lr.fit(Xtr, ytr); gbm.fit(Xtr, ytr)
scores = {"Step 4 rule (ratio only)": test["ratio"].values,
          "Logistic regression": lr.predict_proba(Xte)[:, 1],
          "Gradient boosting": gbm.predict_proba(Xte)[:, 1]}

def capture(score, frac=0.2):
    k = int(len(score) * frac); idx = np.argsort(-score)[:k]
    return {"churn_rate_in_top20pct": yte[idx].mean(),
            "lift_vs_average": yte[idx].mean() / yte.mean(),
            "share_of_churners_caught": yte[idx].sum() / yte.sum(),
            "share_of_churner_revenue_caught": rev_te[idx][yte[idx] == 1].sum() / rev_te[yte == 1].sum()}

rows = []
for name, sc in scores.items():
    rows.append({"model": name, "auc": roc_auc_score(yte, sc), **capture(sc)})
# Business view: rank by (chance of going quiet) x (what they spent last year), so big spenders come first.
value_score = scores["Logistic regression"] * rev_te
rows.append({"model": "Logistic risk x past spend", "auc": np.nan, **capture(value_score)})
comp = pd.DataFrame(rows).round(3)
comp.to_csv(os.path.join(OUT, "05_model_comparison.csv"), index=False)
print("\n== MODEL COMPARISON on the unseen test date (auc: 0.5 = coin flip, 1.0 = perfect)")
print(comp.to_string(index=False))

# ---- decile table for the gradient boosting model ----
p = scores["Gradient boosting"]
d = pd.DataFrame({"p": p, "y": yte, "rev": rev_te})
d["risk_group"] = pd.qcut(d["p"].rank(method="first", ascending=False), 10, labels=list(range(1, 11)))
dec = d.groupby("risk_group", observed=True).agg(customers=("y", "size"), predicted_churn=("p", "mean"),
        actual_churn=("y", "mean"), avg_rev365=("rev", "mean")).round(3).reset_index()
dec.to_csv(os.path.join(OUT, "05_risk_groups.csv"), index=False)
print("\n== RISK GROUPS (1 = riskiest 10%). Do predicted and actual churn agree?")
print(dec.to_string(index=False))

# ---- what drives the model ----
rng = np.random.RandomState(42)
sel = rng.choice(len(Xte), size=min(15000, len(Xte)), replace=False)
pi = permutation_importance(gbm, Xte.iloc[sel], yte[sel], scoring="roc_auc", n_repeats=5, random_state=42)
imp = pd.DataFrame({"feature": FEATURES, "auc_drop_when_scrambled": pi.importances_mean}).sort_values(
        "auc_drop_when_scrambled", ascending=False).round(4)
imp.to_csv(os.path.join(OUT, "05_feature_importance.csv"), index=False)
print("\n== WHAT MATTERS MOST (how much the model gets worse if we scramble that column)")
print(imp.to_string(index=False))
