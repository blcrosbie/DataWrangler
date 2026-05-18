# Schema Reference

## `users`

- `user_id` UUID primary key
- `created_at` signup timestamp
- `country` ISO-style country code
- `acquisition_channel` source channel for funnel analysis
- `kyc_status` one of `verified`, `pending`, `rejected`
- `kyc_completed_at` nullable completion timestamp
- `is_business` boolean flag

## `accounts`

- `account_id` UUID primary key
- `user_id` foreign key to `users`
- `account_type` one of `checking`, `wallet`, `savings`, `merchant`
- `currency` one of `USD`, `EUR`, `GBP`, `SGD`
- `opened_at` account-open timestamp
- `status` one of `active`, `frozen`, `closed`

## `merchants`

- `merchant_id` UUID primary key
- `merchant_name` merchant label
- `category` merchant category used for spend aggregations
- `merchant_country` merchant country code

## `transaction_events`

This is the raw fact table and intentionally contains duplicate processor rows and multiple status rows per logical transaction.

- `event_id` UUID primary key
- `logical_tx_id` logical transaction key spanning multiple lifecycle rows
- `processor_reference` source reference that may duplicate during re-ingestion
- `src_account_id` source account
- `dest_account_id` nullable destination account for internal transfers
- `merchant_id` nullable merchant for card activity
- `amount` transaction amount
- `fee_amount` platform fee recognized on settled rows
- `currency` transaction currency
- `tx_type` one of `card_purchase`, `transfer`, `cash_out`, `card_refund`
- `event_status` one of `pending`, `settled`, `declined`, `reversed`
- `event_time` business event timestamp
- `ingested_at` warehouse-ingestion timestamp

## Practice Assumptions

- For deduping questions, keep the latest `ingested_at` per `processor_reference`.
- For lifecycle questions, derive the latest state per `logical_tx_id` after deduping.
- For volume comparisons, either filter to `USD` or state that you are comparing native-currency amounts.
