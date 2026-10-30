# H&M Customer Retention Analysis

**Which customers are quietly leaving, and which ones are actually worth saving first.**

An independent analytics project built on 31.8 million real H&M purchases. I trained a churn model that scored a respectable 0.77 AUC, then showed why that number on its own would have protected almost none of the money at risk. The fix was not a fancier model. It was changing the question.

---

## The result in one line

Take the 20% of customers the model flags as most likely to leave. Chase them, and you protect **11.0%** of the revenue that later goes quiet. Now take the *same number* of customers, but rank them by risk multiplied by how much they usually spend. You protect **49.4%**.

Same list size. Same effort. About four and a half times the money saved.

> Accuracy is not the same as usefulness. A business does not want to catch the most customers. It wants to catch the most revenue.

That one shift is the whole project.

---

## Headline numbers

All money figures are an **index**, not pounds. Kaggle scrambles the prices, so these compare cleanly against each other but are not real currency.

| What | Number |
|---|---|
| New customers who came back within 180 days | 42.3% |
| Yearly revenue exposed to churn (upper bound) | 21.5% |
| Yearly revenue likely gone for good | 12.1% |
| Revenue sitting with "on track" customers | 58.2% |
| Revenue sitting with "gone quiet" customers | 6.9% |
| Best model AUC (logistic regression) | 0.769 |
| Churner revenue caught in top 20% by model score | 11.0% |
| Churner revenue caught in top 20% by risk x spend | 49.4% |

One segment worth a second look: customers who get the newsletter regularly came back at **49.5%**, against **40.8%** for those who get none. Linked to, not proven to cause, which is why it became an A/B test rather than a claim.

---

## Live and written output

- **Interactive dashboard (Tableau Public):** https://public.tableau.com/views/HMTableauDashboard/Dashboard1
- **What I would actually do about it:** [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md), ranked actions plus a full A/B test plan
- **Every decision and why I made it:** [`DECISION_LOG.md`](DECISION_LOG.md)
- **LinkedIn carousel:** [`docs/linkedin/`](docs/linkedin/)
- **Interview prep write-up:** [`docs/hm_retention_interview_prep.pdf`](docs/hm_retention_interview_prep.pdf)

---

## How it was built, step by step

1. **Clean and sample.** 31.8 million transactions is too big to iterate on quickly, so I worked on a reproducible 10% customer sample and checked it was not biased against the full set.
2. **Retention funnel.** Of 18,122 new customers, 42.3% came back within 180 days and only 7.2% became loyal (five or more shopping days).
3. **Segments.** Retention split by age, club status, first channel, and newsletter, with a margin of error on every number so small groups do not mislead.
4. **Revenue at risk.** A plain status rule (on track, slipping, drifting, gone quiet) from how overdue each customer is versus their own normal gap between visits.
5. **Churn model.** Logistic regression and gradient boosting, tested out of time (train on an earlier window, test on a later one) so the score is honest about the future, not just the past.
6. **Dashboard.** Six Tableau sheets plus one dashboard, fed by small aggregate CSVs in `outputs/dashboard_pack/`.
7. **Monthly summary.** A local LLM (Ollama, llama3.2) writes a plain-English monthly note, with an automatic number checker and a risky-word checker, because the model can get the meaning wrong even when the numbers are right.
8. **Recommendations and an A/B plan.** Ranked by revenue protected, each written as a hypothesis to test rather than a fact.

---

## Repository structure

```
.
├── scripts/            # the full pipeline, numbered 01 to 08
│   ├── 01_clean_sample.py
│   ├── 02_retention_funnel.sql
│   ├── 03_segments.sql
│   ├── 04_revenue_at_risk.py
│   ├── 05_churn_model.py
│   ├── 06_dashboard_pack.py
│   ├── 07_monthly_summary.py      # local AI summary + checks
│   ├── 08_recommendation_sizing.py
│   └── run_all.py                 # runs the whole thing
├── outputs/            # small aggregate results (safe to share, no customer rows)
│   └── dashboard_pack/            # the exact CSVs the Tableau dashboard reads
├── docs/               # LinkedIn carousel + interview prep PDF
├── data/               # how to get the raw data (it is not included)
├── H&M Tableau Dashboard.twb
├── RECOMMENDATIONS.md
├── DECISION_LOG.md
├── DATA_TERMS.md
├── requirements.txt
└── README.md
```

---

## Reproduce it yourself

```bash
# 1. Get the data (not included, see data/README.md for why)
#    Download from the Kaggle "H&M Personalized Fashion Recommendations"
#    competition into the project root:
#    transactions_train.csv, customers.csv, articles.csv

# 2. Set up a clean environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run the whole pipeline
python scripts/run_all.py
```

The monthly summary in step 07 is optional. It needs [Ollama](https://ollama.com) running locally with `llama3.2`. Skip it with `--no-llm` and you still get the fact sheet.

---

## Tools

Everything here is free and open source. No paid APIs, no cloud bills.

- **Python** with pandas, NumPy, scikit-learn
- **DuckDB** for fast SQL over the raw files, no database server to run
- **Tableau Public** for the dashboard
- **Ollama** (local llama3.2) for the written summary

---

## A note on honesty

I would rather undersell a real finding than oversell a shaky one. So:

- Money is an index, not pounds (Kaggle scrambles the prices).
- "Linked to" is not "caused by". The model spots patterns, not reasons.
- The raw data is not in this repo and never will be, per the Kaggle rules. See [`DATA_TERMS.md`](DATA_TERMS.md).
- Independent project. Not affiliated with or endorsed by H&M.

Built by **Varesh Nirbhavne**. [LinkedIn](https://www.linkedin.com/in/varesh-nirbhavne-1619a02a3/)
