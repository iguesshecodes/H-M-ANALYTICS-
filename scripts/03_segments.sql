-- Step 3: segments. Builds on cust_summary from Step 2.
-- Customer facts (age, club, newsletter) are a snapshot from the end of the data,
-- so every result here is "linked to", never "caused by".

-- One row per buyer with the segment labels and a fair 180-day outcome.
CREATE OR REPLACE TABLE seg_cust AS
WITH first180 AS (
  SELECT c.customer_id, count(DISTINCT t.t_dat) AS days_in_180
  FROM cust_summary c JOIN sample_transactions t USING (customer_id)
  WHERE t.t_dat < c.first_day + INTERVAL 180 DAY
  GROUP BY 1
),
first_ch AS (  -- channel used on the very first shopping day (so it cannot be caused by later behaviour)
  SELECT t.customer_id,
         CASE WHEN count(DISTINCT t.sales_channel_id) = 2 THEN 'Both channels'
              WHEN min(t.sales_channel_id) = 1 THEN 'Channel 1' ELSE 'Channel 2' END AS first_channel
  FROM sample_transactions t JOIN cust_summary c ON t.customer_id = c.customer_id AND t.t_dat = c.first_day
  GROUP BY 1
)
SELECT c.customer_id, c.first_day, c.last_day, c.shopping_days, c.revenue_index,
       f.days_in_180, ch.first_channel,
       CASE WHEN s.age IS NULL THEN 'Unknown' WHEN s.age < 25 THEN '16-24' WHEN s.age < 35 THEN '25-34'
            WHEN s.age < 45 THEN '35-44' WHEN s.age < 55 THEN '45-54' WHEN s.age < 65 THEN '55-64' ELSE '65+' END AS age_band,
       s.club_status, s.newsletter
FROM cust_summary c
JOIN sample_customers s USING (customer_id)
JOIN first180 f USING (customer_id)
JOIN first_ch ch USING (customer_id);

-- A. Fair comparison: new customers only (first purchase 20 Sep 2019 to 26 Mar 2020).
--    ci_pm = plus or minus points of uncertainty (95%). Groups under 500 people are flagged.
-- name: segments_new_customers
WITH nc AS (SELECT * FROM seg_cust WHERE first_day BETWEEN DATE '2019-09-20' AND DATE '2020-03-26'),
long AS (
  SELECT 'Age' AS dimension, age_band AS segment, days_in_180 FROM nc
  UNION ALL SELECT 'Club status', club_status, days_in_180 FROM nc
  UNION ALL SELECT 'Newsletter', newsletter, days_in_180 FROM nc
  UNION ALL SELECT 'First purchase channel', first_channel, days_in_180 FROM nc
)
SELECT dimension, segment, count(*) AS n,
       round(100.0 * avg((days_in_180 >= 2)::int), 1) AS came_back_180_pct,
       round(196.0 * sqrt(avg((days_in_180 >= 2)::int) * (1 - avg((days_in_180 >= 2)::int)) / count(*)), 1) AS ci_pm,
       round(100.0 * avg((days_in_180 >= 5)::int), 1) AS loyal_180_pct,
       CASE WHEN count(*) < 500 THEN 'too small to trust' ELSE '' END AS note
FROM long GROUP BY 1, 2 ORDER BY 1, 2;

-- B. All buyers who started before 24 Jun 2020: who carries the money, who is still shopping?
--    still_active = bought at least once in the last 90 days of data.
--    Older customers have had longer to build up, so read this as a "where is the value" view.
-- name: segments_all_buyers
WITH base AS (SELECT * FROM seg_cust WHERE first_day < DATE '2020-06-24'),
long AS (
  SELECT 'Age' AS dimension, age_band AS segment, * FROM base
  UNION ALL SELECT 'Club status', club_status, * FROM base
  UNION ALL SELECT 'Newsletter', newsletter, * FROM base
  UNION ALL SELECT 'First purchase channel', first_channel, * FROM base
)
SELECT dimension, segment, count(*) AS customers,
       round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY dimension), 1) AS pct_of_customers,
       round(100.0 * sum(revenue_index) / sum(sum(revenue_index)) OVER (PARTITION BY dimension), 1) AS pct_of_revenue,
       round(avg(shopping_days), 1) AS avg_shopping_days,
       round(100.0 * avg((shopping_days >= 5)::int), 1) AS loyal_pct,
       round(100.0 * avg((last_day >= DATE '2020-06-24')::int), 1) AS still_active_90d_pct,
       CASE WHEN count(*) < 500 THEN 'too small to trust' ELSE '' END AS note
FROM long GROUP BY 1, 2 ORDER BY 1, 2;

-- C. Confounding check 1: does the newsletter gap survive inside each age band?
-- name: check_newsletter_within_age
WITH nc AS (SELECT * FROM seg_cust WHERE first_day BETWEEN DATE '2019-09-20' AND DATE '2020-03-26'
            AND newsletter IN ('Regularly', 'None') AND age_band <> 'Unknown')
SELECT age_band,
       sum((newsletter = 'Regularly')::int) AS regular_n,
       round(100.0 * avg(CASE WHEN newsletter = 'Regularly' THEN (days_in_180 >= 2)::int END), 1) AS regular_back_pct,
       sum((newsletter = 'None')::int) AS none_n,
       round(100.0 * avg(CASE WHEN newsletter = 'None' THEN (days_in_180 >= 2)::int END), 1) AS none_back_pct,
       round(100.0 * (avg(CASE WHEN newsletter = 'Regularly' THEN (days_in_180 >= 2)::int END)
                    - avg(CASE WHEN newsletter = 'None' THEN (days_in_180 >= 2)::int END)), 1) AS gap_points
FROM nc GROUP BY 1 ORDER BY 1;

-- D. Confounding check 2: club and newsletter overlap. Look at all four combinations.
-- name: check_club_x_newsletter
SELECT club_status, newsletter, count(*) AS n,
       round(100.0 * avg((days_in_180 >= 2)::int), 1) AS came_back_180_pct,
       round(100.0 * avg((days_in_180 >= 5)::int), 1) AS loyal_180_pct
FROM seg_cust
WHERE first_day BETWEEN DATE '2019-09-20' AND DATE '2020-03-26'
  AND club_status IN ('ACTIVE', 'PRE-CREATE') AND newsletter IN ('Regularly', 'None')
GROUP BY 1, 2 ORDER BY 1, 2;

-- E. Confounding check 3: are some groups simply newer customers?
-- name: check_group_age_of_relationship
SELECT club_status, count(*) AS customers,
       quantile_disc(first_day, 0.5) AS median_first_purchase,
       round(100.0 * avg((first_day >= DATE '2019-09-20')::int), 1) AS pct_first_bought_in_last_year
FROM seg_cust GROUP BY 1 ORDER BY 2 DESC;
