-- Q01
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY te.processor_reference
                ORDER BY te.ingested_at DESC, te.event_id DESC
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
                PARTITION BY d.logical_tx_id
                ORDER BY d.event_time DESC, d.ingested_at DESC, d.event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
)
SELECT
    u.country,
    m.category,
    COUNT(*) AS settled_tx_count,
    SUM(lt.amount) AS total_amount
FROM latest_tx lt
JOIN accounts a ON lt.src_account_id = a.account_id
JOIN users u ON a.user_id = u.user_id
JOIN merchants m ON lt.merchant_id = m.merchant_id
WHERE lt.event_status = 'settled'
  AND lt.tx_type = 'card_purchase'
  AND lt.currency = 'USD'
  AND lt.event_time >= CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY u.country, m.category
ORDER BY total_amount DESC;

-- Q02
WITH ranked AS (
    SELECT
        processor_reference,
        event_id,
        event_time,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY processor_reference
            ORDER BY ingested_at DESC, event_id DESC
        ) AS duplicate_rank
    FROM transaction_events
)
SELECT
    processor_reference,
    event_id,
    event_time,
    ingested_at,
    duplicate_rank
FROM ranked
WHERE duplicate_rank > 1
ORDER BY processor_reference, duplicate_rank;

-- Q03
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
user_totals AS (
    SELECT
        u.country,
        u.user_id,
        SUM(lt.amount) AS total_amount
    FROM latest_tx lt
    JOIN accounts a ON lt.src_account_id = a.account_id
    JOIN users u ON a.user_id = u.user_id
    WHERE lt.event_status = 'settled'
      AND lt.currency = 'USD'
    GROUP BY u.country, u.user_id
),
ranked_users AS (
    SELECT
        country,
        user_id,
        total_amount,
        DENSE_RANK() OVER (
            PARTITION BY country
            ORDER BY total_amount DESC
        ) AS country_rank
    FROM user_totals
)
SELECT
    country,
    user_id,
    total_amount,
    country_rank
FROM ranked_users
WHERE country_rank <= 3
ORDER BY country, country_rank, user_id;

-- Q04
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
first_settled AS (
    SELECT
        a.user_id,
        MIN(lt.event_time) AS first_settled_at
    FROM latest_tx lt
    JOIN accounts a ON lt.src_account_id = a.account_id
    WHERE lt.event_status = 'settled'
    GROUP BY a.user_id
)
SELECT
    u.acquisition_channel,
    COUNT(*) AS signed_up_users,
    COUNT(*) FILTER (
        WHERE fs.first_settled_at <= u.created_at + INTERVAL '30 days'
    ) AS activated_users,
    ROUND(
        COUNT(*) FILTER (
            WHERE fs.first_settled_at <= u.created_at + INTERVAL '30 days'
        )::numeric / NULLIF(COUNT(*), 0),
        4
    ) AS activation_rate
FROM users u
LEFT JOIN first_settled fs ON u.user_id = fs.user_id
GROUP BY u.acquisition_channel
ORDER BY activation_rate DESC, signed_up_users DESC;

-- Q05
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
first_settled AS (
    SELECT
        a.user_id,
        MIN(lt.event_time) AS first_settled_at
    FROM latest_tx lt
    JOIN accounts a ON lt.src_account_id = a.account_id
    WHERE lt.event_status = 'settled'
    GROUP BY a.user_id
)
SELECT
    DATE_TRUNC('month', u.created_at) AS cohort_month,
    DATE_TRUNC('month', fs.first_settled_at) AS conversion_month,
    (
        EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', fs.first_settled_at), DATE_TRUNC('month', u.created_at))) * 12
        + EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', fs.first_settled_at), DATE_TRUNC('month', u.created_at)))
    )::int AS month_offset,
    COUNT(*) AS users_converted
FROM users u
JOIN first_settled fs ON u.user_id = fs.user_id
GROUP BY 1, 2, 3
ORDER BY cohort_month, month_offset;

-- Q06
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
settled_transfers AS (
    SELECT *
    FROM latest_tx
    WHERE event_status = 'settled'
      AND tx_type = 'transfer'
),
window_hits AS (
    SELECT
        t1.src_account_id,
        t1.event_time AS window_start,
        MAX(t2.event_time) AS window_end,
        COUNT(*) AS tx_count
    FROM settled_transfers t1
    JOIN settled_transfers t2
      ON t1.src_account_id = t2.src_account_id
     AND t2.event_time BETWEEN t1.event_time AND t1.event_time + INTERVAL '10 minutes'
    GROUP BY t1.src_account_id, t1.event_time
)
SELECT
    src_account_id,
    window_start,
    window_end,
    tx_count
FROM window_hits
WHERE tx_count >= 4
ORDER BY tx_count DESC, src_account_id, window_start;

-- Q07
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
settled_transfers AS (
    SELECT *
    FROM latest_tx
    WHERE event_status = 'settled'
      AND tx_type = 'transfer'
),
anomalies AS (
    SELECT
        t1.src_account_id,
        t1.amount,
        MIN(t2.event_time) AS first_tx_time,
        MAX(t2.event_time) AS last_tx_time,
        COUNT(*) AS tx_count
    FROM settled_transfers t1
    JOIN settled_transfers t2
      ON t1.src_account_id = t2.src_account_id
     AND t1.amount = t2.amount
     AND t2.event_time BETWEEN t1.event_time AND t1.event_time + INTERVAL '30 minutes'
    GROUP BY t1.src_account_id, t1.amount, t1.event_time
)
SELECT DISTINCT
    src_account_id,
    amount,
    first_tx_time,
    last_tx_time,
    tx_count
FROM anomalies
WHERE tx_count >= 3
ORDER BY tx_count DESC, last_tx_time DESC;

-- Q08
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
)
SELECT
    u.acquisition_channel,
    u.kyc_status,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE lt.event_status = 'declined') AS declined_transactions,
    ROUND(
        COUNT(*) FILTER (WHERE lt.event_status = 'declined')::numeric / NULLIF(COUNT(*), 0),
        4
    ) AS decline_rate
FROM latest_tx lt
JOIN accounts a ON lt.src_account_id = a.account_id
JOIN users u ON a.user_id = u.user_id
GROUP BY u.acquisition_channel, u.kyc_status
ORDER BY decline_rate DESC, total_transactions DESC;

-- Q09
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
)
SELECT
    DATE_TRUNC('month', event_time) AS month,
    tx_type,
    COUNT(*) AS settled_tx_count,
    SUM(amount) AS total_amount,
    SUM(fee_amount) AS total_fee_amount
FROM latest_tx
WHERE event_status = 'settled'
GROUP BY 1, 2
ORDER BY month, tx_type;

-- Q10
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
monthly_segment_volume AS (
    SELECT
        DATE_TRUNC('month', lt.event_time) AS month,
        CASE WHEN u.is_business THEN 'business' ELSE 'consumer' END AS user_segment,
        SUM(lt.amount) AS settled_volume
    FROM latest_tx lt
    JOIN accounts a ON lt.src_account_id = a.account_id
    JOIN users u ON a.user_id = u.user_id
    WHERE lt.event_status = 'settled'
      AND lt.currency = 'USD'
    GROUP BY 1, 2
)
SELECT
    month,
    user_segment,
    settled_volume,
    ROUND(
        settled_volume / NULLIF(SUM(settled_volume) OVER (PARTITION BY month), 0),
        4
    ) AS share_of_monthly_volume
FROM monthly_segment_volume
ORDER BY month, user_segment;
