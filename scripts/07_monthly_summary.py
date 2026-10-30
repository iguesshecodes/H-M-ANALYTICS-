# Step 7: refresh the numbers, then let a free local AI (Ollama) write a plain-English summary.
# Play button = write the summary from the latest saved results (fast).
# run_all.py = full refresh of steps 1 to 6 first, then the summary (slow).
import os, re, sys, json, subprocess, urllib.request
import pandas as pd

MODEL = "llama3.2"          # must match the model you downloaded in Ollama (no ":cloud")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")

REFRESH = ["01_clean_sample.py", "run_step2.py", "run_step3.py",
           "04_revenue_at_risk.py", "05_churn_model.py", "06_dashboard_pack.py"]

def refresh():
    for name in REFRESH:
        print("Running", name, "...")
        r = subprocess.run([sys.executable, os.path.join(HERE, name)])
        if r.returncode != 0:
            sys.exit("Stopped: " + name + " failed. Fix it first, then run again.")

def rd(name):
    return pd.read_csv(os.path.join(OUT, name), keep_default_na=False)

def facts():
    h = rd("04_headline.csv").iloc[0]
    st = rd("04_status_now.csv")
    tr = rd("04_at_risk_trend.csv")
    seg = rd("03_segments_new_customers.csv")
    fn = rd("02_funnel_new_customers.csv")
    md = rd("05_model_comparison.csv")
    nl = seg[(seg["dimension"] == "Newsletter") & (seg["segment"] == "Regularly")].iloc[0]
    nn = seg[(seg["dimension"] == "Newsletter") & (seg["segment"] == "None")].iloc[0]
    last, prev = tr.iloc[-1], tr.iloc[-2]
    best = md[md["model"].str.contains("risk x past spend")].iloc[0]
    L = []
    L.append("Data runs to " + str(last["cut_date"]) + ". Revenue figures are an index, not pounds.")
    L.append("New customers: " + str(fn.iloc[1]["pct_of_new_buyers"]) + " percent came back within 180 days.")
    L.append("Share of established revenue at risk now: " + str(last["pct_rev_at_risk"]) +
             " percent, versus " + str(prev["pct_rev_at_risk"]) + " percent at " + str(prev["cut_date"]) + ".")
    L.append("Revenue that is at risk and might be lost, at most: " + str(h["exposure_pct_of_established_rev"]) +
             " percent. This is NOT revenue already lost. Revenue likely to be lost for good: " + str(h["likely_gone_pct_of_established_rev"]) + " percent of established revenue.")
    for _, r in st.iterrows():
        L.append("Customers with status " + str(r["status"])[2:] + " account for " + str(r["pct_of_established_rev"]) + " percent of established revenue (this is revenue, not a share of customers).")
    L.append("Regular newsletter readers who are new customers came back " + str(nl["came_back_180_pct"]) +
             " percent, versus " + str(nn["came_back_180_pct"]) +
             " percent for people with no newsletter. This is a link, not proof of cause.")
    L.append("In a test on past data (nobody was actually contacted), a contact list ranked by risk times past spend would have caught " +
             str(round(float(best["share_of_churner_revenue_caught"]) * 100, 1)) +
             " percent of the revenue that was later lost from customers who went quiet, using the top 20 percent of customers on that list. Say \"would have caught\", never \"has helped\".")
    return L

def ask_llm(fact_lines):
    prompt = ("You write a short monthly update for a retail manager who is not a data person.\n"
              "Use ONLY the facts below. Do not add any number that is not listed. "
              "Do not guess causes. Say revenue is an index, not pounds. "
              "Say the newsletter result is a link, not proof. "
              "Write 4 to 6 short sentences in plain English. No bullet points, no dashes. "
              "Do not call any result good or bad, stable or unstable, and never use the words effect, cause, because, improve or positive. "
              "Keep each fact's meaning exactly as written, including whether it is revenue or customers. "
              "Do not compare anything unless the facts give both numbers.\n\nFACTS:\n"
              + "\n".join(fact_lines))
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())["response"].strip()
    except Exception as e:
        sys.exit("Could not reach Ollama. Is the app open and is the model '" + MODEL + "' downloaded? " + str(e))

RISKY = ["effect", "caus", "because", "due to", "positive", "negative", "stable", "improv", "worse", "good", "bad", "great", "strong", "weak", "driven"]

def check_words(text):
    low = text.lower().replace("for good", "")
    return [w for w in RISKY if w in low]

def check_numbers(text, fact_lines):
    allowed = set(re.findall(r"\d+(?:\.\d+)?", " ".join(fact_lines)))
    used = set(re.findall(r"\d+(?:\.\d+)?", text))
    return sorted(n for n in used if n not in allowed)

if __name__ == "__main__":
    if "--refresh" in sys.argv:
        refresh()
    F = facts()
    print("\n".join(F))
    if "--no-llm" in sys.argv:
        sys.exit()
    text = ask_llm(F)
    bad = check_numbers(text, F)
    note = ("All numbers in the summary match the fact sheet." if not bad else
            "WARNING: these numbers are not in the fact sheet, check before using: " + ", ".join(bad))
    words = check_words(text)
    if words:
        note += "\nWARNING: opinion or cause words found (" + ", ".join(words) + "). Read it yourself before using."
    else:
        note += "\nNo cause or opinion words found. Still read it yourself: a check cannot catch every wrong meaning."
    fixed = ("Always read with care: revenue figures are an index, not pounds. "
             "The newsletter result is a link, not proof that the newsletter causes buying.")
    md = ("# Monthly retention summary\n\n" + text + "\n\n" + fixed + "\n\n---\n" + note +
          "\n\nFact sheet the AI was given:\n\n" + "\n".join("- " + x for x in F) + "\n")
    path = os.path.join(OUT, "monthly_summary.md")
    open(path, "w").write(md)
    print("\n" + text + "\n\n" + note + "\nSaved to " + path)
