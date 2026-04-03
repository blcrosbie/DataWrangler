-- 1. Create Tables
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    kyc_status VARCHAR,
    country VARCHAR,
    created_at TIMESTAMP
);

CREATE TABLE accounts (
    account_id UUID PRIMARY KEY,
    user_id UUID,
    account_type VARCHAR,
    currency VARCHAR
);

CREATE TABLE transactions (
    tx_id UUID PRIMARY KEY,
    src_account_id UUID,
    dest_account_id UUID,
    amount DECIMAL(18, 2),
    tx_type VARCHAR,
    timestamp TIMESTAMP
);

-- 2. Load Data using read_csv_auto
COPY users FROM 'users.csv' (FORMAT CSV, HEADER);
COPY accounts FROM 'accounts.csv' (FORMAT CSV, HEADER);
COPY transactions FROM 'transactions.csv' (FORMAT CSV, HEADER);

-- 3. Validation queries
SELECT 'Users count:' as label, count(*) FROM users
UNION ALL
SELECT 'Accounts count:', count(*) FROM accounts
UNION ALL
SELECT 'Transactions count:', count(*) FROM transactions;

-- 4. Sample Fraud Check (Rapid-fire)
SELECT src_account_id, count(*) as tx_count
FROM transactions
GROUP BY src_account_id, date_trunc('minute', timestamp)
HAVING count(*) > 3
LIMIT 5;
