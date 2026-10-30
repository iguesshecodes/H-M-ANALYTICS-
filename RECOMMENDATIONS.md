# Recommendations and A/B test plan

Revenue figures are an index (the prices in the data are scrambled), shown as a share of yearly revenue. These are what-if sizes with stated assumptions, not promises. Only the A/B test can give the real number.

## Top 3 recommendations, ranked by revenue protected (middle case)

| Rank | Recommendation | Range | Middle case | Why this rank |
|---|---|---|---|---|
| 1 | Contact big spenders who are slipping first (list ranked by risk times past spend) | 0.6% to 1.8% of yearly revenue | 1.2% | Starts from revenue we can see is leaving. In a test on past data the top 20% of this list would have caught 49.4% of the revenue that later went quiet. Assumes the offer saves 10%, 20% or 30% of it. |
| 2 | Get new customers to buy a second time | 0.4% to 1.9% | 0.9% | Only 42.3% of new customers come back within 180 days. Assumes 2, 5 or 10 more points come back. Depends on a large assumed lift, so more uncertain. |
| 3 | Push the fashion newsletter sign-up | 0.03% to 0.11% | 0.05% | Readers came back more (49.5% vs 40.8%), but people who already like H&M sign up, so only a quarter or half of that gap is counted. Cheap to run, small size. |

Ranks 1 and 2 overlap in range. Rank 1 is first because its starting pool is measured, rank 2's is assumed.

What these numbers do not say: contacting someone does not prove they stay. In the top 20% list, 41.9% still went quiet, so some contacted customers would have come back anyway.

## A/B test: does contacting the top of the risk x spend list save revenue?

**Question.** Does one personalised email with a modest offer raise revenue per customer over the next 90 days, compared with doing nothing?

**Who is in it.** Established customers (3 or more shopping days) in the top 20% of the risk x spend ranking on the start date.

**How they are split.** Randomly, 50 and 50, from the same list. Randomness makes the two groups equally keen and equally at risk, so any gap afterwards comes from the offer. Choosing engaged people (for example email openers) would be a trap: they buy more anyway, so we could not tell if the offer worked. Before launch, check that both groups look the same on age, past spend and days since last purchase.

**What each group gets.**
- Treatment: one personalised email with a modest offer.
- Control: nothing. No other campaign differs between the groups during the test.

**Main result (decides the test).** Revenue per customer in the next 90 days, after the cost of the discount.

**Also watched.**
- Share of each group who bought at least once.
- Unsubscribes and complaints (a guardrail: if they jump, stop).

**How many people.** About 4,300 per group is enough to detect a 3 point rise in the share who buy (a rough estimate, assuming about 58% buy in the control group). Revenue per customer is lopsided because a few people spend a lot, so the final size should use the real spread from past data.

**How long.** 90 days after sending, plus a short buffer for late purchases. No peeking and stopping early when it looks good.

**Decision rule.**
- Roll out if revenue per customer is higher and the 95% margin stays above zero after the discount cost.
- If the margin includes zero, it is not proven. Do not roll out, and consider a larger test.
- If unsubscribes jump, stop and review.

**What the test cannot tell us.** Why a customer went quiet, and whether the effect lasts beyond 90 days.
