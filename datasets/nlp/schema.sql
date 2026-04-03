CREATE TABLE IF NOT EXISTS reviews (
    review_id UUID,
    category VARCHAR,
    text VARCHAR,
    sentiment_score DECIMAL(5,2),
    sentiment_label VARCHAR
);

-- Load CSV data
COPY reviews FROM 'reviews.csv' (FORMAT CSV, HEADER);

-- Sample Query for Analysis (Sentiment Rank by Category)
SELECT category, AVG(sentiment_score) as avg_sentiment
FROM reviews
GROUP BY category
ORDER BY avg_sentiment DESC;
