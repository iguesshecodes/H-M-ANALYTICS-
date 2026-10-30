-- Check for the Step 2 cohort trend: do "returning after a long break" customers repeat more than truly new ones?
-- If yes, early cohorts (which can't separate the two) look better than they should.
-- Only visits from 2019-09-20 on are used, so every entry has 12+ months of history behind it.
-- name: new_vs_returning_repeat
WITH visits AS (
  SELECT DISTINCT customer_id, t_dat AS visit_day FROM sample_transactions
),
ordered AS (
  SELECT customer_id, visit_day,
         lag(visit_day)  OVER (PARTITION BY customer_id ORDER BY visit_day) AS prev_day,
         lead(visit_day) OVER (PARTITION BY customer_id ORDER BY visit_day) AS next_day
  FROM visits
),
entries AS (
  SELECT *, CASE WHEN prev_day IS NULL THEN 'A. Truly new (never seen before)'
                 ELSE 'B. Returned after a 180+ day break' END AS kind
  FROM ordered
  WHERE (prev_day IS NULL OR date_diff('day', prev_day, visit_day) >= 180)
    AND visit_day BETWEEN DATE '2019-09-20' AND DATE '2020-06-24'
)
SELECT kind, count(*) AS entries,
       round(100.0 * sum((next_day IS NOT NULL AND next_day < visit_day + INTERVAL 90 DAY)::int) / count(*), 1) AS repeat_rate_90d_pct
FROM entries GROUP BY kind ORDER BY kind;
