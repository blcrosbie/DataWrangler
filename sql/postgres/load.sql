COPY users
FROM '/workspace/practice_data/users.csv'
WITH (FORMAT csv, HEADER true, NULL '\N');

COPY accounts
FROM '/workspace/practice_data/accounts.csv'
WITH (FORMAT csv, HEADER true, NULL '\N');

COPY merchants
FROM '/workspace/practice_data/merchants.csv'
WITH (FORMAT csv, HEADER true, NULL '\N');

COPY transaction_events
FROM '/workspace/practice_data/transaction_events.csv'
WITH (FORMAT csv, HEADER true, NULL '\N');
