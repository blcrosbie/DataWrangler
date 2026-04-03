import csv
import random
import uuid
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

def generate_data(num_rows=10000):
    # 1. Generate Users
    num_users = 1000
    users = []
    for _ in range(num_users):
        users.append({
            'user_id': str(uuid.uuid4()),
            'kyc_status': random.choice(['verified', 'pending', 'failed']),
            'country': fake.country_code(),
            'created_at': fake.date_time_between(start_date='-2y', end_date='now').isoformat()
        })

    # 2. Generate Accounts
    accounts = []
    for user in users:
        # Each user has 1-3 accounts
        for _ in range(random.randint(1, 3)):
            accounts.append({
                'account_id': str(uuid.uuid4()),
                'user_id': user['user_id'],
                'account_type': random.choice(['checking', 'savings', 'investment']),
                'currency': random.choice(['USD', 'EUR', 'GBP', 'JPY'])
            })

    # 3. Generate Transactions
    transactions = []
    account_ids = [acc['account_id'] for acc in accounts]
    
    # 10,000 transactions
    for i in range(num_rows):
        tx_type = random.choice(['Internal', 'Deposit', 'Withdrawal'])
        src_account_id = random.choice(account_ids)
        dest_account_id = random.choice(account_ids) if tx_type == 'Internal' else None
        
        # Ensure src != dest for internal
        while tx_type == 'Internal' and src_account_id == dest_account_id:
            dest_account_id = random.choice(account_ids)

        timestamp = fake.date_time_between(start_date='-1y', end_date='now')
        
        transactions.append({
            'tx_id': str(uuid.uuid4()),
            'src_account_id': src_account_id,
            'dest_account_id': dest_account_id,
            'amount': round(random.uniform(1.0, 5000.0), 2),
            'tx_type': tx_type,
            'timestamp': timestamp.isoformat()
        })

    # Add Fraud Scenarios (Rapid-fire and Double-spend)
    for _ in range(50):
        # Rapid-fire: 5 transactions in 10 seconds from same account
        fraud_src = random.choice(account_ids)
        base_time = fake.date_time_between(start_date='-1y', end_date='now')
        for i in range(5):
            transactions.append({
                'tx_id': str(uuid.uuid4()),
                'src_account_id': fraud_src,
                'dest_account_id': random.choice(account_ids),
                'amount': round(random.uniform(10.0, 100.0), 2),
                'tx_type': 'Internal',
                'timestamp': (base_time + timedelta(seconds=i*2)).isoformat()
            })

    # Double-spend: Same source, same amount, almost same time
    for _ in range(20):
        fraud_src = random.choice(account_ids)
        fraud_dest = random.choice(account_ids)
        fraud_amount = round(random.uniform(500.0, 1000.0), 2)
        base_time = fake.date_time_between(start_date='-1y', end_date='now')
        for i in range(2):
            transactions.append({
                'tx_id': str(uuid.uuid4()),
                'src_account_id': fraud_src,
                'dest_account_id': fraud_dest,
                'amount': fraud_amount,
                'tx_type': 'Internal',
                'timestamp': (base_time + timedelta(milliseconds=random.randint(10, 500))).isoformat()
            })

    # Write to CSVs
    write_csv('users.csv', ['user_id', 'kyc_status', 'country', 'created_at'], users)
    write_csv('accounts.csv', ['account_id', 'user_id', 'account_type', 'currency'], accounts)
    write_csv('transactions.csv', ['tx_id', 'src_account_id', 'dest_account_id', 'amount', 'tx_type', 'timestamp'], transactions)

def write_csv(filename, fieldnames, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    generate_data()
    print("Data generation complete.")
