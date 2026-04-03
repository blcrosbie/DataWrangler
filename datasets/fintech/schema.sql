CREATE TABLE IF NOT EXISTS users (user_id UUID, kyc VARCHAR, country VARCHAR);
CREATE TABLE IF NOT EXISTS accounts (account_id UUID, user_id UUID, type VARCHAR);
CREATE TABLE IF NOT EXISTS transactions (tx_id UUID, src_id UUID, amount DECIMAL(18,2), ts TIMESTAMP);

-- Initial Data Load
COPY users FROM 'users.csv' (FORMAT CSV, HEADER);
COPY accounts FROM 'accounts.csv' (FORMAT CSV, HEADER);
COPY transactions FROM 'transactions.csv' (FORMAT CSV, HEADER);
