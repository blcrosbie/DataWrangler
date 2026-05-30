# SQL Optimization Problem Sets

These sets use the faker fintech practice tables:

- `users`
- `accounts`
- `merchants`
- `transaction_events`

The point is not one perfect answer. The point is comparing styles:

- nested query / correlated subquery style
- join-first aggregate style
- CTE / window style
- when each style is likely to break down

Assumptions:

- Deduplicate `transaction_events` by keeping the latest `ingested_at` per `processor_reference`.
- Collapse lifecycle rows by keeping the latest row per `logical_tx_id` after deduping.
- For spend and volume comparisons, filter to `currency = 'USD'` unless the prompt says otherwise.

## Reusable Latest Transaction CTE

Most optimized answers below reuse this shape.

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY te.processor_reference
                ORDER BY te.ingested_at DESC, te.event_id DESC
            ) AS dedupe_rank
        FROM transaction_events te
    ) ranked
    WHERE dedupe_rank = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY d.logical_tx_id
                ORDER BY d.event_time DESC, d.ingested_at DESC, d.event_id DESC
            ) AS lifecycle_rank
        FROM deduped d
    ) ranked
    WHERE lifecycle_rank = 1
)
SELECT *
FROM latest_tx;
```

## Set 01: Users With No Settled Transaction

Difficulty: Medium

Prompt: Return users who signed up in the last 180 days but have no settled transaction after deduping and latest-state collapse. Include `user_id`, `country`, `acquisition_channel`, and `created_at`.

### Nested / Correlated Style

```sql
SELECT
    u.user_id,
    u.country,
    u.acquisition_channel,
    u.created_at
FROM users u
WHERE u.created_at >= CURRENT_TIMESTAMP - INTERVAL '180 days'
  AND NOT EXISTS (
      SELECT 1
      FROM accounts a
      JOIN transaction_events te
        ON te.src_account_id = a.account_id
      WHERE a.user_id = u.user_id
        AND te.event_status = 'settled'
  )
ORDER BY u.created_at DESC;
```

Tradeoff: Easy to read, but wrong for this dataset because it ignores processor duplicates and lifecycle rows. It can also become expensive if the optimizer cannot turn the anti-subquery into an anti-join.

### Left Join Anti-Join Style

```sql
WITH settled_users AS (
    SELECT DISTINCT a.user_id
    FROM transaction_events te
    JOIN accounts a
      ON te.src_account_id = a.account_id
    WHERE te.event_status = 'settled'
)
SELECT
    u.user_id,
    u.country,
    u.acquisition_channel,
    u.created_at
FROM users u
LEFT JOIN settled_users su
  ON u.user_id = su.user_id
WHERE u.created_at >= CURRENT_TIMESTAMP - INTERVAL '180 days'
  AND su.user_id IS NULL
ORDER BY u.created_at DESC;
```

Tradeoff: Often efficient and easy to reason about, but still wrong if raw duplicate/lifecycle rows are not collapsed.

### CTE / Window Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
settled_users AS (
    SELECT DISTINCT a.user_id
    FROM latest_tx lt
    JOIN accounts a
      ON lt.src_account_id = a.account_id
    WHERE lt.event_status = 'settled'
)
SELECT
    u.user_id,
    u.country,
    u.acquisition_channel,
    u.created_at
FROM users u
LEFT JOIN settled_users su
  ON u.user_id = su.user_id
WHERE u.created_at >= CURRENT_TIMESTAMP - INTERVAL '180 days'
  AND su.user_id IS NULL
ORDER BY u.created_at DESC;
```

Efficiency read: Best benchmark answer because it respects data semantics and lets indexes on `processor_reference`, `logical_tx_id`, and account joins do useful work. If the latest-state result is reused heavily, materializing it into a temp table can be worth testing.

## Set 02: First Settled Transaction Per User

Difficulty: Medium

Prompt: Return each user's first settled transaction timestamp and amount. Include users only if they have at least one settled transaction.

### Nested / Correlated Style

```sql
SELECT
    u.user_id,
    (
        SELECT MIN(te.event_time)
        FROM accounts a
        JOIN transaction_events te
          ON te.src_account_id = a.account_id
        WHERE a.user_id = u.user_id
          AND te.event_status = 'settled'
    ) AS first_settled_at
FROM users u
WHERE (
    SELECT COUNT(*)
    FROM accounts a
    JOIN transaction_events te
      ON te.src_account_id = a.account_id
    WHERE a.user_id = u.user_id
      AND te.event_status = 'settled'
) > 0;
```

Tradeoff: Repeats nearly the same lookup twice per user and does not return the amount without another nested lookup. It is a common interview starting point, but it scales poorly.

### Buggy Join Aggregate Style

```sql
WITH first_times AS (
    SELECT
        a.user_id,
        MIN(te.event_time) AS first_settled_at
    FROM accounts a
    JOIN transaction_events te
      ON te.src_account_id = a.account_id
    WHERE te.event_status = 'settled'
    GROUP BY a.user_id
)
SELECT
    ft.user_id,
    ft.first_settled_at,
    te.amount
FROM first_times ft
JOIN accounts a
  ON ft.user_id = a.user_id
JOIN transaction_events te
  ON te.src_account_id = a.account_id
 AND te.event_time = ft.first_settled_at
 AND te.event_status = 'settled'
ORDER BY ft.first_settled_at;
```

Tradeoff: Better shape, but tied timestamps can duplicate users and raw events still overcount lifecycle noise.

### CTE / Window Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
ranked_user_tx AS (
    SELECT
        a.user_id,
        lt.event_time,
        lt.amount,
        lt.logical_tx_id,
        ROW_NUMBER() OVER (
            PARTITION BY a.user_id
            ORDER BY lt.event_time, lt.ingested_at, lt.event_id
        ) AS first_rank
    FROM latest_tx lt
    JOIN accounts a
      ON lt.src_account_id = a.account_id
    WHERE lt.event_status = 'settled'
)
SELECT
    user_id,
    event_time AS first_settled_at,
    amount,
    logical_tx_id
FROM ranked_user_tx
WHERE first_rank = 1
ORDER BY first_settled_at;
```

Efficiency read: Window ranking avoids tie bugs and returns columns from the exact winning row. This is the most LeetCode-style "top 1 per group" answer.

## Set 03: Top Merchant Category Per Country

Difficulty: Medium

Prompt: For settled USD card purchases, return the highest-volume merchant category in each user country.

### Nested / Correlated Style

```sql
SELECT
    country,
    category,
    total_amount
FROM (
    SELECT
        u.country,
        m.category,
        SUM(te.amount) AS total_amount
    FROM transaction_events te
    JOIN accounts a
      ON te.src_account_id = a.account_id
    JOIN users u
      ON a.user_id = u.user_id
    JOIN merchants m
      ON te.merchant_id = m.merchant_id
    WHERE te.event_status = 'settled'
      AND te.tx_type = 'card_purchase'
      AND te.currency = 'USD'
    GROUP BY u.country, m.category
) x
WHERE total_amount = (
    SELECT MAX(country_category_total)
    FROM (
        SELECT
            u2.country,
            m2.category,
            SUM(te2.amount) AS country_category_total
        FROM transaction_events te2
        JOIN accounts a2
          ON te2.src_account_id = a2.account_id
        JOIN users u2
          ON a2.user_id = u2.user_id
        JOIN merchants m2
          ON te2.merchant_id = m2.merchant_id
        WHERE te2.event_status = 'settled'
          AND te2.tx_type = 'card_purchase'
          AND te2.currency = 'USD'
          AND u2.country = x.country
        GROUP BY u2.country, m2.category
    ) country_totals
);
```

Tradeoff: This repeats the same expensive aggregation per country. Useful as a correctness strawman, not as a benchmark target.

### Join Aggregate Style

```sql
WITH category_totals AS (
    SELECT
        u.country,
        m.category,
        SUM(te.amount) AS total_amount
    FROM transaction_events te
    JOIN accounts a
      ON te.src_account_id = a.account_id
    JOIN users u
      ON a.user_id = u.user_id
    JOIN merchants m
      ON te.merchant_id = m.merchant_id
    WHERE te.event_status = 'settled'
      AND te.tx_type = 'card_purchase'
      AND te.currency = 'USD'
    GROUP BY u.country, m.category
),
country_max AS (
    SELECT
        country,
        MAX(total_amount) AS max_total_amount
    FROM category_totals
    GROUP BY country
)
SELECT
    ct.country,
    ct.category,
    ct.total_amount
FROM category_totals ct
JOIN country_max cm
  ON ct.country = cm.country
 AND ct.total_amount = cm.max_total_amount
ORDER BY ct.country;
```

Tradeoff: Good aggregate-join pattern. It returns ties, which may be desired. It still ignores lifecycle collapse.

### CTE / Window Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
category_totals AS (
    SELECT
        u.country,
        m.category,
        SUM(lt.amount) AS total_amount
    FROM latest_tx lt
    JOIN accounts a
      ON lt.src_account_id = a.account_id
    JOIN users u
      ON a.user_id = u.user_id
    JOIN merchants m
      ON lt.merchant_id = m.merchant_id
    WHERE lt.event_status = 'settled'
      AND lt.tx_type = 'card_purchase'
      AND lt.currency = 'USD'
    GROUP BY u.country, m.category
),
ranked_categories AS (
    SELECT
        country,
        category,
        total_amount,
        DENSE_RANK() OVER (
            PARTITION BY country
            ORDER BY total_amount DESC
        ) AS category_rank
    FROM category_totals
)
SELECT
    country,
    category,
    total_amount
FROM ranked_categories
WHERE category_rank = 1
ORDER BY country, category;
```

Efficiency read: The aggregate happens once, then ranking is cheap over a much smaller result. This is the cleanest hard-medium interview answer.

## Set 04: Rolling 7-Day Settled Volume Per Account

Difficulty: Hard

Prompt: For each source account and transaction day, return settled USD volume for that day and trailing 7-day settled USD volume.

### Self-Join Window Style

```sql
WITH daily AS (
    SELECT
        src_account_id,
        CAST(event_time AS DATE) AS tx_day,
        SUM(amount) AS daily_volume
    FROM transaction_events
    WHERE event_status = 'settled'
      AND currency = 'USD'
    GROUP BY src_account_id, CAST(event_time AS DATE)
)
SELECT
    d1.src_account_id,
    d1.tx_day,
    d1.daily_volume,
    SUM(d2.daily_volume) AS trailing_7_day_volume
FROM daily d1
JOIN daily d2
  ON d1.src_account_id = d2.src_account_id
 AND d2.tx_day BETWEEN d1.tx_day - INTERVAL '6 days' AND d1.tx_day
GROUP BY d1.src_account_id, d1.tx_day, d1.daily_volume
ORDER BY d1.src_account_id, d1.tx_day;
```

Tradeoff: Portable and intuitive, but the self-join can grow fast for dense daily data.

### Window Frame Style

```sql
WITH daily AS (
    SELECT
        src_account_id,
        CAST(event_time AS DATE) AS tx_day,
        SUM(amount) AS daily_volume
    FROM transaction_events
    WHERE event_status = 'settled'
      AND currency = 'USD'
    GROUP BY src_account_id, CAST(event_time AS DATE)
)
SELECT
    src_account_id,
    tx_day,
    daily_volume,
    SUM(daily_volume) OVER (
        PARTITION BY src_account_id
        ORDER BY tx_day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS trailing_7_row_volume
FROM daily
ORDER BY src_account_id, tx_day;
```

Tradeoff: Fast, but `ROWS BETWEEN 6 PRECEDING` means seven observed transaction days, not seven calendar days. That is wrong if days are missing.

### Latest-State Calendar-Aware Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
daily AS (
    SELECT
        src_account_id,
        CAST(event_time AS DATE) AS tx_day,
        SUM(amount) AS daily_volume
    FROM latest_tx
    WHERE event_status = 'settled'
      AND currency = 'USD'
    GROUP BY src_account_id, CAST(event_time AS DATE)
)
SELECT
    d1.src_account_id,
    d1.tx_day,
    d1.daily_volume,
    SUM(d2.daily_volume) AS trailing_7_day_volume
FROM daily d1
JOIN daily d2
  ON d1.src_account_id = d2.src_account_id
 AND d2.tx_day BETWEEN d1.tx_day - INTERVAL '6 days' AND d1.tx_day
GROUP BY d1.src_account_id, d1.tx_day, d1.daily_volume
ORDER BY d1.src_account_id, d1.tx_day;
```

Efficiency read: Correct calendar-window answer. For very large data, benchmark a date spine plus window frame, or use a database with interval `RANGE` support.

## Set 05: Accounts With Rising Decline Rate

Difficulty: Hard

Prompt: Return source accounts whose decline rate in the last 30 days is at least twice their decline rate in the previous 30 days. Include total transactions for each period.

### Conditional Aggregate Style

```sql
SELECT
    src_account_id,
    COUNT(*) FILTER (
        WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days'
    ) AS recent_total,
    COUNT(*) FILTER (
        WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days'
          AND event_status = 'declined'
    ) AS recent_declined,
    COUNT(*) FILTER (
        WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
          AND event_time < CURRENT_TIMESTAMP - INTERVAL '30 days'
    ) AS previous_total,
    COUNT(*) FILTER (
        WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
          AND event_time < CURRENT_TIMESTAMP - INTERVAL '30 days'
          AND event_status = 'declined'
    ) AS previous_declined
FROM transaction_events
WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
GROUP BY src_account_id
HAVING COUNT(*) FILTER (
        WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days'
    ) >= 10
   AND COUNT(*) FILTER (
        WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
          AND event_time < CURRENT_TIMESTAMP - INTERVAL '30 days'
    ) >= 10
   AND (
        COUNT(*) FILTER (
            WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days'
              AND event_status = 'declined'
        ) * 1.0
        / NULLIF(COUNT(*) FILTER (
            WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days'
        ), 0)
   ) >= 2 * (
        COUNT(*) FILTER (
            WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
              AND event_time < CURRENT_TIMESTAMP - INTERVAL '30 days'
              AND event_status = 'declined'
        ) * 1.0
        / NULLIF(COUNT(*) FILTER (
            WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
              AND event_time < CURRENT_TIMESTAMP - INTERVAL '30 days'
        ), 0)
   );
```

Tradeoff: Single pass over raw data, but verbose and duplicate-prone. It also ignores latest-state collapse.

### Period CTE Style

```sql
WITH periodized AS (
    SELECT
        src_account_id,
        event_status,
        CASE
            WHEN event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 'recent'
            WHEN event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days' THEN 'previous'
        END AS period
    FROM transaction_events
    WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
),
period_stats AS (
    SELECT
        src_account_id,
        period,
        COUNT(*) AS total_tx,
        COUNT(*) FILTER (WHERE event_status = 'declined') AS declined_tx
    FROM periodized
    WHERE period IS NOT NULL
    GROUP BY src_account_id, period
)
SELECT
    recent.src_account_id,
    recent.total_tx AS recent_total,
    recent.declined_tx AS recent_declined,
    previous.total_tx AS previous_total,
    previous.declined_tx AS previous_declined,
    recent.declined_tx * 1.0 / NULLIF(recent.total_tx, 0) AS recent_decline_rate,
    previous.declined_tx * 1.0 / NULLIF(previous.total_tx, 0) AS previous_decline_rate
FROM period_stats recent
JOIN period_stats previous
  ON recent.src_account_id = previous.src_account_id
WHERE recent.period = 'recent'
  AND previous.period = 'previous'
  AND recent.total_tx >= 10
  AND previous.total_tx >= 10
  AND recent.declined_tx * 1.0 / NULLIF(recent.total_tx, 0)
      >= 2 * previous.declined_tx * 1.0 / NULLIF(previous.total_tx, 0)
ORDER BY recent_decline_rate DESC;
```

Tradeoff: Clearer and easier to debug. This is usually what you want in an interview before optimizing further.

### Latest-State CTE Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
periodized AS (
    SELECT
        src_account_id,
        event_status,
        CASE
            WHEN event_time >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 'recent'
            WHEN event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days' THEN 'previous'
        END AS period
    FROM latest_tx
    WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '60 days'
),
period_stats AS (
    SELECT
        src_account_id,
        period,
        COUNT(*) AS total_tx,
        COUNT(*) FILTER (WHERE event_status = 'declined') AS declined_tx
    FROM periodized
    WHERE period IS NOT NULL
    GROUP BY src_account_id, period
)
SELECT
    recent.src_account_id,
    recent.total_tx AS recent_total,
    recent.declined_tx AS recent_declined,
    previous.total_tx AS previous_total,
    previous.declined_tx AS previous_declined,
    recent.declined_tx * 1.0 / NULLIF(recent.total_tx, 0) AS recent_decline_rate,
    previous.declined_tx * 1.0 / NULLIF(previous.total_tx, 0) AS previous_decline_rate
FROM period_stats recent
JOIN period_stats previous
  ON recent.src_account_id = previous.src_account_id
WHERE recent.period = 'recent'
  AND previous.period = 'previous'
  AND recent.total_tx >= 10
  AND previous.total_tx >= 10
  AND recent.declined_tx * 1.0 / NULLIF(recent.total_tx, 0)
      >= 2 * previous.declined_tx * 1.0 / NULLIF(previous.total_tx, 0)
ORDER BY recent_decline_rate DESC;
```

Efficiency read: Best correctness answer. If performance is poor, add a date predicate before deduping only if you can prove old lifecycle rows cannot affect current latest status.

## Set 06: Users With Multi-Currency Account Coverage

Difficulty: Medium

Prompt: Return users who have active accounts in at least three different currencies. Include business/consumer segment and currency count.

### Nested Style

```sql
SELECT
    u.user_id,
    CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment,
    (
        SELECT COUNT(DISTINCT a.currency)
        FROM accounts a
        WHERE a.user_id = u.user_id
          AND a.status = 'active'
    ) AS active_currency_count
FROM users u
WHERE (
    SELECT COUNT(DISTINCT a.currency)
    FROM accounts a
    WHERE a.user_id = u.user_id
      AND a.status = 'active'
) >= 3
ORDER BY active_currency_count DESC, u.user_id;
```

Tradeoff: Reads cleanly but repeats the same aggregate per user.

### Group By / Having Style

```sql
SELECT
    u.user_id,
    CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment,
    COUNT(DISTINCT a.currency) AS active_currency_count
FROM users u
JOIN accounts a
  ON u.user_id = a.user_id
WHERE a.status = 'active'
GROUP BY u.user_id, u.is_business
HAVING COUNT(DISTINCT a.currency) >= 3
ORDER BY active_currency_count DESC, u.user_id;
```

Tradeoff: Compact and efficient for this problem. This is the best answer unless you need additional per-currency detail.

### CTE Style

```sql
WITH active_currency_counts AS (
    SELECT
        user_id,
        COUNT(DISTINCT currency) AS active_currency_count
    FROM accounts
    WHERE status = 'active'
    GROUP BY user_id
)
SELECT
    u.user_id,
    CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment,
    acc.active_currency_count
FROM active_currency_counts acc
JOIN users u
  ON acc.user_id = u.user_id
WHERE acc.active_currency_count >= 3
ORDER BY acc.active_currency_count DESC, u.user_id;
```

Efficiency read: Same plan as the `GROUP BY` style in many optimizers, but easier to extend with segment-level rollups.

## Set 07: Merchant Category Retention

Difficulty: Hard

Prompt: For each signup month and merchant category, return users whose first settled card purchase in that category happened within 30 days of signup.

### Join Aggregate Style

```sql
WITH first_category_purchase AS (
    SELECT
        u.user_id,
        DATE_TRUNC('month', u.created_at) AS signup_month,
        m.category,
        MIN(te.event_time) AS first_category_purchase_at
    FROM users u
    JOIN accounts a
      ON u.user_id = a.user_id
    JOIN transaction_events te
      ON a.account_id = te.src_account_id
    JOIN merchants m
      ON te.merchant_id = m.merchant_id
    WHERE te.event_status = 'settled'
      AND te.tx_type = 'card_purchase'
      AND te.currency = 'USD'
    GROUP BY u.user_id, DATE_TRUNC('month', u.created_at), m.category
)
SELECT
    signup_month,
    category,
    COUNT(*) AS users_activated_in_category
FROM first_category_purchase
WHERE first_category_purchase_at <= signup_month + INTERVAL '1 month' + INTERVAL '30 days'
GROUP BY signup_month, category
ORDER BY signup_month, users_activated_in_category DESC;
```

Tradeoff: The 30-day filter is subtly wrong because it compares against truncated signup month instead of exact `created_at`.

### Correct Join Aggregate Style

```sql
WITH first_category_purchase AS (
    SELECT
        u.user_id,
        u.created_at,
        DATE_TRUNC('month', u.created_at) AS signup_month,
        m.category,
        MIN(te.event_time) AS first_category_purchase_at
    FROM users u
    JOIN accounts a
      ON u.user_id = a.user_id
    JOIN transaction_events te
      ON a.account_id = te.src_account_id
    JOIN merchants m
      ON te.merchant_id = m.merchant_id
    WHERE te.event_status = 'settled'
      AND te.tx_type = 'card_purchase'
      AND te.currency = 'USD'
    GROUP BY u.user_id, u.created_at, DATE_TRUNC('month', u.created_at), m.category
)
SELECT
    signup_month,
    category,
    COUNT(*) AS users_activated_in_category
FROM first_category_purchase
WHERE first_category_purchase_at <= created_at + INTERVAL '30 days'
GROUP BY signup_month, category
ORDER BY signup_month, users_activated_in_category DESC;
```

Tradeoff: Correct time boundary, but still raw-event based.

### Latest-State Window Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
ranked_category_purchase AS (
    SELECT
        u.user_id,
        u.created_at,
        DATE_TRUNC('month', u.created_at) AS signup_month,
        m.category,
        lt.event_time,
        ROW_NUMBER() OVER (
            PARTITION BY u.user_id, m.category
            ORDER BY lt.event_time, lt.event_id
        ) AS category_purchase_rank
    FROM users u
    JOIN accounts a
      ON u.user_id = a.user_id
    JOIN latest_tx lt
      ON a.account_id = lt.src_account_id
    JOIN merchants m
      ON lt.merchant_id = m.merchant_id
    WHERE lt.event_status = 'settled'
      AND lt.tx_type = 'card_purchase'
      AND lt.currency = 'USD'
)
SELECT
    signup_month,
    category,
    COUNT(*) AS users_activated_in_category
FROM ranked_category_purchase
WHERE category_purchase_rank = 1
  AND event_time <= created_at + INTERVAL '30 days'
GROUP BY signup_month, category
ORDER BY signup_month, users_activated_in_category DESC;
```

Efficiency read: Strong benchmark problem because it tests exact date logic, dedupe logic, and `ROW_NUMBER` ranking by a composite group.

## Set 08: Transfer Graph Fan-Out

Difficulty: Hard

Prompt: Find source accounts that sent settled transfers to at least five distinct destination accounts in a 24-hour period. Return the earliest qualifying window per source account.

### Self-Join Style

```sql
WITH transfers AS (
    SELECT
        src_account_id,
        dest_account_id,
        event_time
    FROM transaction_events
    WHERE event_status = 'settled'
      AND tx_type = 'transfer'
      AND dest_account_id IS NOT NULL
),
windows AS (
    SELECT
        t1.src_account_id,
        t1.event_time AS window_start,
        MAX(t2.event_time) AS window_end,
        COUNT(DISTINCT t2.dest_account_id) AS distinct_destinations
    FROM transfers t1
    JOIN transfers t2
      ON t1.src_account_id = t2.src_account_id
     AND t2.event_time BETWEEN t1.event_time AND t1.event_time + INTERVAL '24 hours'
    GROUP BY t1.src_account_id, t1.event_time
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY src_account_id
            ORDER BY window_start
        ) AS rn
    FROM windows
    WHERE distinct_destinations >= 5
)
SELECT
    src_account_id,
    window_start,
    window_end,
    distinct_destinations
FROM ranked
WHERE rn = 1
ORDER BY window_start;
```

Tradeoff: Natural for rolling time-window fraud prompts. Can be expensive because each transfer can join to many later transfers.

### Pre-Filtered Latest-State Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
transfers AS (
    SELECT
        src_account_id,
        dest_account_id,
        event_time
    FROM latest_tx
    WHERE event_status = 'settled'
      AND tx_type = 'transfer'
      AND dest_account_id IS NOT NULL
),
windows AS (
    SELECT
        t1.src_account_id,
        t1.event_time AS window_start,
        MAX(t2.event_time) AS window_end,
        COUNT(DISTINCT t2.dest_account_id) AS distinct_destinations
    FROM transfers t1
    JOIN transfers t2
      ON t1.src_account_id = t2.src_account_id
     AND t2.event_time BETWEEN t1.event_time AND t1.event_time + INTERVAL '24 hours'
    GROUP BY t1.src_account_id, t1.event_time
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY src_account_id
            ORDER BY window_start
        ) AS rn
    FROM windows
    WHERE distinct_destinations >= 5
)
SELECT
    src_account_id,
    window_start,
    window_end,
    distinct_destinations
FROM ranked
WHERE rn = 1
ORDER BY window_start;
```

Efficiency read: The important optimization is reducing to settled transfers before the self-join. On large tables, benchmark adding an index on `(src_account_id, event_time)` and filtering by a bounded date range.

## Set 09: Fee Outlier By Transaction Type

Difficulty: Medium

Prompt: Return settled transactions whose fee amount is more than three times the average fee for their transaction type and currency.

### Correlated Aggregate Style

```sql
SELECT
    te.logical_tx_id,
    te.tx_type,
    te.currency,
    te.amount,
    te.fee_amount
FROM transaction_events te
WHERE te.event_status = 'settled'
  AND te.fee_amount > 3 * (
      SELECT AVG(te2.fee_amount)
      FROM transaction_events te2
      WHERE te2.event_status = 'settled'
        AND te2.tx_type = te.tx_type
        AND te2.currency = te.currency
  )
ORDER BY te.fee_amount DESC;
```

Tradeoff: Simple but may recompute averages many times. Some optimizers decorrelate it, but do not rely on that in interviews.

### Join Aggregate Style

```sql
WITH fee_baselines AS (
    SELECT
        tx_type,
        currency,
        AVG(fee_amount) AS avg_fee_amount
    FROM transaction_events
    WHERE event_status = 'settled'
    GROUP BY tx_type, currency
)
SELECT
    te.logical_tx_id,
    te.tx_type,
    te.currency,
    te.amount,
    te.fee_amount,
    fb.avg_fee_amount
FROM transaction_events te
JOIN fee_baselines fb
  ON te.tx_type = fb.tx_type
 AND te.currency = fb.currency
WHERE te.event_status = 'settled'
  AND te.fee_amount > 3 * fb.avg_fee_amount
ORDER BY te.fee_amount DESC;
```

Tradeoff: Better baseline pattern. It computes each average once.

### Window Aggregate Style

```sql
WITH settled_with_baseline AS (
    SELECT
        te.logical_tx_id,
        te.tx_type,
        te.currency,
        te.amount,
        te.fee_amount,
        AVG(te.fee_amount) OVER (
            PARTITION BY te.tx_type, te.currency
        ) AS avg_fee_amount
    FROM transaction_events te
    WHERE te.event_status = 'settled'
)
SELECT
    logical_tx_id,
    tx_type,
    currency,
    amount,
    fee_amount,
    avg_fee_amount
FROM settled_with_baseline
WHERE fee_amount > 3 * avg_fee_amount
ORDER BY fee_amount DESC;
```

Tradeoff: Very compact. Window aggregate preserves row detail without a second join.

### Latest-State Window Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
settled_with_baseline AS (
    SELECT
        logical_tx_id,
        tx_type,
        currency,
        amount,
        fee_amount,
        AVG(fee_amount) OVER (
            PARTITION BY tx_type, currency
        ) AS avg_fee_amount
    FROM latest_tx
    WHERE event_status = 'settled'
)
SELECT
    logical_tx_id,
    tx_type,
    currency,
    amount,
    fee_amount,
    avg_fee_amount
FROM settled_with_baseline
WHERE fee_amount > 3 * avg_fee_amount
ORDER BY fee_amount DESC;
```

Efficiency read: This is the reference answer. It is a good benchmark for correlated subquery versus aggregate join versus window aggregate.

## Set 10: Monthly Active Users By Segment With Month-Over-Month Change

Difficulty: Hard

Prompt: A monthly active user is a user with at least one settled transaction in a month. Return monthly active users by segment and the month-over-month delta.

### Distinct Aggregate Style

```sql
WITH monthly_active AS (
    SELECT
        DATE_TRUNC('month', te.event_time) AS activity_month,
        CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment,
        COUNT(DISTINCT u.user_id) AS active_users
    FROM transaction_events te
    JOIN accounts a
      ON te.src_account_id = a.account_id
    JOIN users u
      ON a.user_id = u.user_id
    WHERE te.event_status = 'settled'
    GROUP BY
        DATE_TRUNC('month', te.event_time),
        CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END
)
SELECT
    activity_month,
    user_segment,
    active_users,
    active_users - LAG(active_users) OVER (
        PARTITION BY user_segment
        ORDER BY activity_month
    ) AS mom_active_user_delta
FROM monthly_active
ORDER BY activity_month, user_segment;
```

Tradeoff: Great compact answer, but raw-event based.

### Two-Step User Month Style

```sql
WITH user_months AS (
    SELECT DISTINCT
        DATE_TRUNC('month', te.event_time) AS activity_month,
        u.user_id,
        CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment
    FROM transaction_events te
    JOIN accounts a
      ON te.src_account_id = a.account_id
    JOIN users u
      ON a.user_id = u.user_id
    WHERE te.event_status = 'settled'
),
monthly_active AS (
    SELECT
        activity_month,
        user_segment,
        COUNT(*) AS active_users
    FROM user_months
    GROUP BY activity_month, user_segment
)
SELECT
    activity_month,
    user_segment,
    active_users,
    active_users - LAG(active_users) OVER (
        PARTITION BY user_segment
        ORDER BY activity_month
    ) AS mom_active_user_delta
FROM monthly_active
ORDER BY activity_month, user_segment;
```

Tradeoff: The explicit `user_months` grain makes correctness easier to inspect and prevents accidentally counting events instead of users.

### Latest-State CTE Style

```sql
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
),
user_months AS (
    SELECT DISTINCT
        DATE_TRUNC('month', lt.event_time) AS activity_month,
        u.user_id,
        CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment
    FROM latest_tx lt
    JOIN accounts a
      ON lt.src_account_id = a.account_id
    JOIN users u
      ON a.user_id = u.user_id
    WHERE lt.event_status = 'settled'
),
monthly_active AS (
    SELECT
        activity_month,
        user_segment,
        COUNT(*) AS active_users
    FROM user_months
    GROUP BY activity_month, user_segment
)
SELECT
    activity_month,
    user_segment,
    active_users,
    active_users - LAG(active_users) OVER (
        PARTITION BY user_segment
        ORDER BY activity_month
    ) AS mom_active_user_delta
FROM monthly_active
ORDER BY activity_month, user_segment;
```

Efficiency read: Best reference answer. It has clean grains: event row -> latest logical transaction -> user-month -> segment-month. That makes it easier to test and optimize step by step.
