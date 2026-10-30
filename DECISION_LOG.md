# Decision log: H&M customer retention project

Format for every entry: what I noticed, what I checked, what I decided, why.

## Step 1: Clean and sample (28 Oct 2026)

**1. Prices are scrambled**
- Noticed: prices are tiny numbers like 0.05, not pounds.
- Checked: min 0.000017, max 0.59, none zero or negative.
- Decided: call revenue a "revenue index", never pounds or dollars.
- Why: claiming real money would be made up. Ratios and percentages stay valid.

**2. The data stops in September 2020**
- Noticed: transactions run 20 Sep 2018 to 22 Sep 2020.
- Decided: "churn" means "stopped buying before the data ends", measured against 22 Sep 2020, not today.
- Why: this is a 2018 to 2020 picture of H&M, so it cannot say how H&M is doing now.

**3. Repeat rows are real purchases**
- Noticed: about 2.5M groups where one customer bought the same item, same day, same price more than once.
- Decided: keep them.
- Why: this looks like quantity (two of the same T-shirt), not a data error. Deleting them would understate revenue.

**4. Club and newsletter groups are very lopsided**
- Noticed: 92.75% of customers are ACTIVE club members, only 467 are LEFT CLUB. Newsletter is 64% None, 35% Regularly, and only 842 customers are Monthly.
- Decided: compare ACTIVE vs PRE-CREATE for club, and Regularly vs None for newsletter. Show LEFT CLUB and Monthly but label them "too small to trust".
- Why: tiny groups give noisy results that look dramatic and mean nothing. The data does not explain what PRE-CREATE means, so I will describe it as a label and not guess.

**5. Missing and odd values**
- Noticed: age missing for 1.2% of customers, 77 customers aged over 90, 9,699 customers who never bought.
- Decided: age outside 16 to 90 becomes blank. Missing newsletter becomes "Unknown". Customers with no purchases stay out of retention maths.
- Why: no one is under 16 in the file, and ages above 90 look like placeholders.

**6. Sample**
- Decided: keep a fixed 10% of customers (137,571) with all of their purchases (3,217,813 rows).
- Checked: average age 36.34 vs 36.38 full, average price 0.02786 vs 0.02783, club mix within 0.2 points.
- Why: sampling customers, not rows, keeps each person's full history, which retention needs. The sample matches the full data.

**7. Online vs store is an assumption**
- Noticed: sales_channel_id is 1 or 2 with no label in the file. Channel 2 is 70% of rows and about 76% of the revenue index.
- Decided: call them "Channel 1" and "Channel 2". Say "likely online" for 2 only as an assumption.
- Why: I could not confirm the labels from the data page.

## Step 2: Retention funnel (29 Oct 2026)

**8. What counts as a visit and as loyal**
- Noticed: a typical customer has 3 shopping days over two years. The top quarter have 8 or more.
- Decided: one "shopping day" is any calendar day with a purchase. Came back = 2+ shopping days. Loyal = 5+ shopping days.
- Checked: loyal at 5+ is 39.5% of buyers and 84.1% of the revenue index. At 8+ it is 27.3% and 73.5%. At 13+ it is 15.9% and 57.1%.
- Why: 5 is a simple, defensible line, and the story holds at any line I tried. A minority of customers carry most of the revenue.

**9. The first funnel was too flattering**
- Noticed: the whole-sample funnel says 67.4% came back and 39.5% became loyal.
- Checked: the data starts in Sept 2018, so many "first purchases" are really long-time customers whose earlier history we cannot see.
- Decided: use that funnel only as an "all customers" view. For "new customers" use people whose first purchase is between 20 Sep 2019 and 26 Mar 2020, so each has a clean year of no purchases before and 180 days of follow-up.
- Result for new customers: 18,122 people. 42.3% came back within 180 days. Only 7.2% became loyal within 180 days.

**10. A fake decline that I caught**
- Noticed: the 90-day repeat rate drops from 44% (Mar 2019 cohort) to about 30% (Dec 2019 cohort). It looked like H&M was getting worse at keeping new customers.
- Checked: customers returning after a 180+ day break repeat at 48.6%, vs 32.2% for truly new customers. Early cohorts hide many returners, so they look better than they are.
- Decided: do not claim a decline. Cohorts before Oct 2019 are labelled "mixed with returners". From Oct 2019 on, the rate is flat at about 30 to 32%, then 34 to 37% in May and June 2020.
- Why: I cannot say what caused the 2020 rise from this data, so I will report it and not explain it.

**11. Honest limits of the funnel**
- Time to come back (new customers who did return within 180 days): median 39 days, 25% within 10 days, 75% within 93 days. This only counts people who returned, so it is not the typical wait for everyone.
- All numbers are from the 10% sample. Counts for the full customer base are roughly 10 times larger, but I will quote percentages and not scaled-up headcounts.

## Step 3: Segments (29 Oct 2026)

**12. How I made the comparison fair**
- Noticed: older customers have had more time to shop, so comparing everyone's total visits is unfair.
- Decided: the main comparison uses only new customers (first purchase 20 Sep 2019 to 26 Mar 2020, 18,122 people) and asks one question: did they shop again within their own first 180 days?
- Also decided: every result shows a plus or minus margin (95%), and any group under 500 people is flagged "too small to trust".
- Why: same clock for everyone, and no dramatic claims from tiny groups.

**13. Newsletter: the clearest signal**
- Result: regular newsletter readers came back 49.5% (plus or minus 1.3) vs 40.8% (plus or minus 0.9) for no newsletter. Loyal within 180 days: 10.5% vs 6.1%.
- Checked: the gap is positive in every age band (5.3 to 16.3 points), so age does not explain it. It also holds inside active club members only (50.0% vs 42.0%).
- Decided: report it as "linked to" better retention, never "causes".
- Why: newsletter status is a snapshot from the end of the data. Engaged shoppers may simply be more likely to sign up. Only the A/B test in Step 8 can separate the two.

**14. Loyalty club: the data cannot fully answer this**
- Noticed: 92.7% of customers are ACTIVE members. There is no real "never joined" group.
- Result: ACTIVE came back 43.6% vs PRE-CREATE 26.1%. PRE-CREATE are 6.7% of customers but only 2.2% of revenue, average 2.0 shopping days, and just 7.8% were still active in the last 90 days.
- Checked: PRE-CREATE customers are not simply newer (median first purchase 11 Mar 2019 vs 14 Feb 2019 for ACTIVE).
- Decided: say plainly that the dataset has no true non-member group, and that I do not know what PRE-CREATE means because the data page does not say. Frame it as "ACTIVE vs PRE-CREATE".
- Why: guessing the meaning would be making things up.

**15. Age: young customers return most, 25 to 34 carry the money**
- Result: 16-24 came back 47.1%, falling steadily to 35.3% for 65+. But 25-34 are 29.3% of customers and 36.8% of revenue, while 16-24 are 25.2% of customers and 18.8% of revenue.
- Decided: treat 25 to 34 as the highest-value group and 16 to 24 as the biggest group worth keeping.
- Why: coming back often and spending a lot are different things.

**16. Sales channel: no real difference for new customers**
- Result: first purchase in Channel 1 came back 43.2% (plus or minus 1.4) vs Channel 2 41.8% (plus or minus 0.8). The margins overlap.
- Noticed: across all buyers the gap looks bigger (50.0% vs 37.0% loyal), but that view mixes in how long people have been customers.
- Decided: do not claim a channel effect. Channel labels stay "Channel 1 / Channel 2".
- Also noted: Unknown newsletter (795 new customers) came back only 16.7%. These may be incomplete profiles. I will report it and not interpret it.

## Step 4: Revenue at risk (29 Oct 2026)

**17. How I defined "gone quiet"**
- Noticed: one fixed rule (say 90 days) is unfair. Someone who shops every 2 months is fine at day 70, while someone who shops monthly is not.
- Decided: compare days since last shopping day with the customer's own median gap, with a 30 day minimum gap. On track is under 1x their gap, Slipping 1 to 2x, Drifting 2 to 4x, Gone quiet 4x or more. Only customers with 3+ shopping days get a rhythm (73,697 in the sample, 91.3% of last year's revenue index).
- Also decided: I fixed the 1, 2, 4 lines before looking at any result and did not tune them.
- Why: tuning lines until the results look good is how people fool themselves.

**18. Does the rule work? I tested it in the past**
- Checked: at three past dates (24 Dec 2019, 24 Mar 2020, 24 Jun 2020) I used only data up to that date, then looked at who bought in the following 90 days.
- Result: On track 63 to 67% bought again, Slipping 55%, Drifting 48 to 50%, Gone quiet 31 to 33%. The pattern is the same at all three dates.
- Also noted: 35% of On track customers still did not buy within 90 days, and about a third of Gone quiet customers did come back. So this is a ranking of risk, not a prediction for any single person. I use the word "quiet" and never "lost".

**19. The two revenue numbers (revenue index, last 12 months)**
- Exposure: Drifting plus Gone quiet customers spent 8,328 index points over the last 365 days. That is 21.5% of established customers' revenue.
- Likely to stay gone: applying the backtested chance of not returning (Drifting 50.8%, Gone quiet 67.9%) gives 4,685 index points, 12.1% of revenue.
- Decided: lead with the cautious 12.1% and show 21.5% as the upper bound. Both are percentages of the sample, never pounds.
- Limit: "last 365 days of spending" understates people quiet for nearly a year, because most of their spending falls outside the window.

**20. The trend: a lockdown bump, not a collapse**
- Result: the at-risk share of revenue was 20.2% (Sep 2019), rose to 27.4% (end April 2020), fell back to 18.7% (end July), and ended at 21.5% (22 Sep 2020).
- Decided: say the spring rise lines up with the 2020 lockdowns, when stores were shut in many countries, and that this data cannot prove the cause. Many "drifting" customers came back.
- Why it matters: year on year the share is about flat (20.2% vs 21.5%), so this data does not show customers leaving faster.

**21. What this data cannot say**
- It has no Zara or Shein data, so the "losing ground to competitors" idea cannot be tested here. I will say that in the write-up.
- At-risk share is similar across age (20.8 to 24.0%) and channel (21.6% vs 21.5%). Newsletter readers 19.2% vs none 23.2%. ACTIVE club 21.3% vs PRE-CREATE 35.4%.
- The 25 to 34 group holds about 35% of all at-risk revenue because it is the biggest pot, not because it is riskier.
- Customer-level tables stay out of the project folder. Only totals are exported, to respect the Kaggle data terms.

## Step 5: Churn model (30 Oct 2026)

**22. What "churn" means here**
- Decided: for a regular customer (3+ shopping days) on a given date, churn means no purchase in the next 90 days.
- Why: it is measurable from the data and matches the Step 4 backtest. It means "quiet", not "lost". About a third of quiet customers do come back.

**23. How I kept the test fair**
- Decided: every feature uses only data up to the prediction date. I trained on two earlier dates (24 Dec 2019 and 24 Mar 2020, 120,057 rows) and tested on a later date the model never saw (24 Jun 2020, 68,495 rows). Churn rates were similar: 45.4% train, 44.9% test.
- Also decided: club and newsletter status are left out, because they are end-of-data snapshots and could leak the future.
- Limits: the same customer can appear on more than one date. The training period overlaps the spring 2020 lockdowns, and the test date comes after them.

**24. Did the model beat the old rule? Yes. Which model? The simple one.**
- Result (AUC, where 0.5 is a coin flip): the Step 4 rule 0.656, logistic regression 0.769, gradient boosting 0.768.
- Decided: keep logistic regression. The fancy model added nothing, and the simple one is easier to explain, check and maintain.

**25. Predicted chance vs what really happened**
- Checked: in every risk group the model slightly over-predicted going quiet (riskiest 10%: predicted 85.1%, actual 81.1%. Safest 10%: predicted 8.4%, actual 6.0%).
- Decided: trust the model to rank customers, not to give exact percentages.

**26. The revenue twist: a better predictor can protect less money**
- Noticed: the riskiest 20% by the model catches only 11.0% of the revenue from customers who went quiet, while the old rule caught 17.4%.
- Checked: the riskiest group spent 0.046 on average last year and the safest spent 1.898, about 40 times more. The model's riskiest people are small spenders.
- Result: ranking by risk times last year's spend catches 49.4% of that revenue from the same 20% list, but only 18.7% of the quiet customers by headcount. Its list also goes quiet less often (41.9% vs 44.9% on average), so some contacted customers would have returned anyway.
- Decided: use risk times spend to choose who to contact first in the recommendations. Whether contacting them works is for the A/B test to answer.

**27. What the model can and cannot say**
- Most useful signals: number of past shopping days (the biggest by far) and days since the last purchase. These importance numbers are a rough guide, because several columns carry overlapping information.
- It predicts who goes quiet. It cannot say why, and it cannot say whether an offer would change their mind.

## Step 6: Dashboard (Tableau Public)

**28. Why Tableau and not Looker Studio**
- Noticed: Power BI Desktop only runs on Windows, and publishing it online needs a paid licence.
- Checked: Tableau Public is free, runs on a Mac, and publishes a public link. Tableau shows up in many analyst job ads.
- Decided: build the dashboard in Tableau Public. Looker Studio stays as a backup.
- Why: free tools only, and a skill that matches the jobs I am applying for.

**29. What goes into the dashboard**
- Decided: six small tables of totals and percentages (funnel, status, segments, trend, methods, headline numbers). No customer rows and no raw Kaggle data.
- Why: smaller risk with data terms, and a dashboard should show answers, not records.
- Decided: groups with fewer than 500 people are left out.
- Why: tiny groups swing wildly (8 people showed 12.5%), and a chart could mislead a reader.

**30. A wrong chart I caught**
- Noticed: the trend line had a spike of about 41.7 in September, and the bar at the bottom said 12 marks for 13 months.
- Checked: Tableau grouped by month name, so September 2019 (20.2) and September 2020 (21.5) were added together.
- Decided: use the month option that includes the year. The peak is now April 2020 at 27.4.
- Why: a summed spike would have told a false story.

**31. Wrong column on the methods chart**
- Noticed: the bars read 33.9, 33.9, 18.7, 30.1, which are people caught, not revenue caught.
- Checked: the revenue column reads 10.6, 11.0, 49.4, 17.4.
- Decided: chart revenue caught, because the business question is how much money is at risk.

**32. Honest labels on the dashboard**
- Decided: say "revenue index, not pounds" and "linked to, not caused by" on the page.
- Why: the prices in the data are scrambled, and only the A/B test can show cause.

## Step 7: Automation (local AI summary)

**33. Local AI instead of a paid one**
- Noticed: Ollama's default model was a cloud model that asked for payment (error 402).
- Decided: use llama3.2, which runs on my own Mac for free.
- Why: free tools only, and customer numbers never leave my computer.

**34. The AI made mistakes, so I added checks**
- Noticed: the first summary said 58.2 percent of customers were on track (it is revenue), called the newsletter a positive effect (we only know a link), and said the contact list was used (it was only a test on past data).
- Checked: a script compares every number in the summary with the fact sheet and flags cause or opinion words.
- Decided: keep the honesty notes fixed in the script, spell out what each number means, and always read the summary myself.
- Why: the number check passed even when the meaning was wrong. A check cannot replace reading.

**35. Run modes**
- Decided: the Play button writes the summary from saved results (fast). run_all.py refreshes steps 1 to 6 first (slow).

## Step 8: Recommendations and A/B test

**36. Ranking by revenue protected**
- Noticed: the newsletter looked best in Step 3 (49.5 vs 40.8 percent) but is smallest in money terms.
- Checked: sized each idea with what-if scenarios (middle case 1.2, 0.9 and 0.05 percent of yearly revenue).
- Decided: rank 1 contact slipping big spenders, 2 second purchase, 3 newsletter.
- Why: money at stake matters more than a good looking percentage. Ranks 1 and 2 overlap, so I say that out loud.

**37. A/B test design choices**
- Noticed: choosing engaged email openers would make the offer look better than it is.
- Decided: split the same risk x spend list at random, 50 and 50, and judge on revenue per customer over 90 days after discount.
- Why: randomness is what separates "linked to" from "caused by". Open rate only measures curiosity.
