DROP TABLE IF EXISTS transaction_events;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    country VARCHAR NOT NULL,
    acquisition_channel VARCHAR NOT NULL,
    kyc_status VARCHAR NOT NULL,
    kyc_completed_at TIMESTAMP,
    is_business BOOLEAN NOT NULL
);

CREATE TABLE accounts (
    account_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    account_type VARCHAR NOT NULL,
    currency VARCHAR NOT NULL,
    opened_at TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL
);

CREATE TABLE merchants (
    merchant_id UUID PRIMARY KEY,
    merchant_name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    merchant_country VARCHAR NOT NULL
);

CREATE TABLE transaction_events (
    event_id UUID PRIMARY KEY,
    logical_tx_id UUID NOT NULL,
    processor_reference VARCHAR NOT NULL,
    src_account_id UUID NOT NULL REFERENCES accounts(account_id),
    dest_account_id UUID,
    merchant_id UUID REFERENCES merchants(merchant_id),
    amount NUMERIC(12, 2) NOT NULL,
    fee_amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR NOT NULL,
    tx_type VARCHAR NOT NULL,
    event_status VARCHAR NOT NULL,
    event_time TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_transaction_events_logical_tx ON transaction_events(logical_tx_id);
CREATE INDEX idx_transaction_events_processor_reference ON transaction_events(processor_reference);
CREATE INDEX idx_transaction_events_src_account_time ON transaction_events(src_account_id, event_time);
