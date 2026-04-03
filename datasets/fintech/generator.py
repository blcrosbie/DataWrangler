import random
import uuid
from wrangler.core import BaseGenerator

class FintechGenerator(BaseGenerator):
    def generate(self, num_rows=10000):
        # Users
        users = [{'user_id': str(uuid.uuid4()), 'kyc': random.choice(['V', 'P']), 'country': self.fake.country_code()} for _ in range(1000)]
        user_ids = [u['user_id'] for u in users]

        # Accounts
        accounts = [{'account_id': str(uuid.uuid4()), 'user_id': random.choice(user_ids), 'type': random.choice(['C', 'S'])} for _ in range(1500)]
        account_ids = [a['account_id'] for a in accounts]

        # Transactions
        transactions = []
        for _ in range(num_rows):
            transactions.append({
                'tx_id': str(uuid.uuid4()),
                'src_id': random.choice(account_ids),
                'amount': round(random.uniform(1, 5000), 2),
                'ts': self.fake.date_time_between(start_date='-1y').isoformat()
            })

        return {
            'users.csv': users,
            'accounts.csv': accounts,
            'transactions.csv': transactions
        }
