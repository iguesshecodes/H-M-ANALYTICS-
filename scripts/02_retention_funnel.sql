-- Step 2: retention funnel. Runs on the 10% sample made in Step 1.
-- A "shopping day" = one calendar day on which a customer bought anything.
-- Data window: 2018-09-20 to 2020-09-22.

-- One row per customer: the building block for everything below.
CREATE OR REPLACE TABLE cust_summary AS
SELECT customer_id,
       min(t_dat)                 AS first_day,
       max(t_dat)                 AS last_day,
       count(DISTINCT t_dat)      AS shopping_days,
       sum(price)                 AS revenue_index,
       count(*)                   AS items
FROM sample_transactions
GROUP BY customer_id;

-- Second shopping day for each customer (needed for "time to come back").
CREATE OR REPLACE TABLE second_visit AS
SELECT customer_id, min(t_dat) AS second_day
FROM (
  SELECT customer_id, t_dat,
         dense_rank() OVER (PARTITION BY customer_id ORDER BY t_dat) AS rk
  FROM (SELECT DISTINCT customer_id, t_dat FROM sample_transactions)
) WHERE rk = 2
GROUP BY customer_id;

-- A. Whole-sample funnel: bought, came back, became loyal (5+ shopping days).
--    Caveat: includes people who were already H&M customers before Sept 2018.
-- name: funnel_all
SELECT stage, customers,
       round(100.0 * customers / first_value(customers) OVER (ORDER BY ord), 1) AS pct_of_buyers,
       round(100.0 * customers / lag(customers) OVER (ORDER BY ord), 1)          AS pct_of_previous_stage
FROM (
  SELECT 1 ord, '1. Bought at least once'        AS stage, count(*) AS customers FROM cust_summary
  UNION ALL SELECT 2, '2. Came back (2+ shopping days)', count(*) FROM cust_summary WHERE shopping_days >= 2
  UNION ALL SELECT 3, '3. Loyal (5+ shopping days)',     count(*) FROM cust_summary WHERE shopping_days >= 5
) ORDER BY ord;

-- B. "New to us" funnel. Only customers whose first purchase in the data is
--    on/after 2019-09-20 (a full year with no purchase first, so almost all are truly new;
--    see 02b check: returners from a long break repeat far more, so earlier starts look too good)
--    AND at least 180 days before the data ends (fair time to come back and become loyal).
-- name: funnel_new_customers
WITH new_c AS (
  SELECT * FROM cust_summary
  WHERE first_day >= DATE '2019-09-20' AND first_day <= DATE '2020-03-26'
),
within AS (  -- count shopping days inside each customer's own first 180 days
  SELECT n.customer_id, count(DISTINCT t.t_dat) AS days_in_180
  FROM new_c n JOIN sample_transactions t USING (customer_id)
  WHERE t.t_dat < n.first_day + INTERVAL 180 DAY
  GROUP BY n.customer_id
)
SELECT stage, customers,
       round(100.0 * customers / first_value(customers) OVER (ORDER BY ord), 1) AS pct_of_new_buyers,
       round(100.0 * customers / lag(customers) OVER (ORDER BY ord), 1)         AS pct_of_previous_stage
FROM (
  SELECT 1 ord, '1. First purchase'                      AS stage, count(*) AS customers FROM within
  UNION ALL SELECT 2, '2. Came back within 180 days',    count(*) FROM within WHERE days_in_180 >= 2
  UNION ALL SELECT 3, '3. Loyal within 180 days (5+ days)', count(*) FROM within WHERE days_in_180 >= 5
) ORDER BY ord;

-- C. How long until people come back? (new customers who did return)
-- name: days_to_second_visit
SELECT count(*) AS returners,
       quantile_cont(date_diff('day', c.first_day, s.second_day), 0.25) AS p25_days,
       quantile_cont(date_diff('day', c.first_day, s.second_day), 0.50) AS median_days,
       quantile_cont(date_diff('day', c.first_day, s.second_day), 0.75) AS p75_days
FROM cust_summary c JOIN second_visit s USING (customer_id)
WHERE c.first_day >= DATE '2019-09-20' AND c.first_day <= DATE '2020-03-26'
  AND s.second_day < c.first_day + INTERVAL 180 DAY;

-- D. Repeat rate by first-purchase month (90-day window, full 90 days of follow-up only).
-- name: repeat_rate_by_cohort
SELECT strftime(c.first_day, '%Y-%m') AS cohort_month,
       CASE WHEN strftime(c.first_day, '%Y-%m') >= '2019-10' THEN 'clean' ELSE 'mixed with returners' END AS cohort_quality,
       count(*)                       AS new_customers,
       sum((s.second_day IS NOT NULL AND s.second_day < c.first_day + INTERVAL 90 DAY)::int) AS repeated_in_90d,
       round(100.0 * sum((s.second_day IS NOT NULL AND s.second_day < c.first_day + INTERVAL 90 DAY)::int) / count(*), 1) AS repeat_rate_90d_pct
FROM cust_summary c LEFT JOIN second_visit s USING (customer_id)
WHERE c.first_day >= DATE '2019-03-20' AND c.first_day <= DATE '2020-06-24'
GROUP BY 1 ORDER BY 1;

-- E. Cohort grid for the heatmap: of customers whose first purchase was in month X,
--    what % bought again in each following month? (months 1 to 6; cohorts with full 6 months of data)
-- name: cohort_grid
WITH cohort AS (
  SELECT customer_id, date_trunc('month', first_day) AS cohort_month
  FROM cust_summary
  WHERE first_day >= DATE '2019-03-20' AND first_day < DATE '2020-03-01'
),
cohort_size AS (SELECT cohort_month, count(*) AS size FROM cohort GROUP BY 1),
activity AS (
  SELECT DISTINCT customer_id, date_trunc('month', t_dat) AS active_month FROM sample_transactions
)
SELECT strftime(c.cohort_month, '%Y-%m') AS cohort_month, z.size AS cohort_size,
       date_diff('month', c.cohort_month, a.active_month) AS months_since_first,
       count(DISTINCT c.customer_id) AS active_customers,
       round(100.0 * count(DISTINCT c.customer_id) / z.size, 1) AS pct_active
FROM cohort c
JOIN activity a USING (customer_id)
JOIN cohort_size z USING (cohort_month)
WHERE date_diff('month', c.cohort_month, a.active_month) BETWEEN 1 AND 6
GROUP BY c.cohort_month, z.size, months_since_first
ORDER BY c.cohort_month, months_since_first;

-- F. Sensitivity check: does moving the "loyal" line change the story?
-- name: loyal_threshold_check
SELECT t AS loyal_means_shopping_days_at_least, count(*) AS customers,
       round(100.0 * count(*) / (SELECT count(*) FROM cust_summary), 1) AS pct_of_buyers,
       round(100.0 * sum(revenue_index) / (SELECT sum(revenue_index) FROM cust_summary), 1) AS pct_of_revenue
FROM cust_summary, (VALUES (3), (5), (8), (13)) v(t)
WHERE shopping_days >= t
GROUP BY t ORDER BY t;
