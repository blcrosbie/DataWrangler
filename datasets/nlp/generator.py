import random
import uuid
from wrangler.core import BaseGenerator

class NlpGenerator(BaseGenerator):
    def generate(self, num_rows=5000):
        # Taxonomy categories
        categories = ['Electronics', 'Home Decor', 'Clothing', 'Books', 'Software']
        sentiments = ['positive', 'neutral', 'negative']
        
        # Reviews dataset
        reviews = []
        for _ in range(num_rows):
            reviews.append({
                'review_id': str(uuid.uuid4()),
                'category': random.choice(categories),
                'text': self.fake.sentence(nb_words=10),
                'sentiment_score': round(random.uniform(-1, 1), 2),
                'sentiment_label': random.choice(sentiments)
            })

        return {'reviews.csv': reviews}
