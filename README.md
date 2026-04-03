# DataWrangler 🚀
**DataWrangler** is a modular, high-performance data engineering framework designed to generate, ingest, and analyze complex datasets using **DuckDB** and **Python**. 

Originally built 7 years ago as a SQL-helper library, it has been refactored into a modern **Multi-Scenario Data Engine** capable of spinning up realistic environments for Fintech, NLP, and Time-series analysis in seconds.

## 🌟 Key Features
- **Multi-Scenario Architecture:** Easily switch between `fintech`, `nlp`, and other custom datasets.
- **In-Process OLAP:** Powered by **DuckDB** for lightning-fast analytical queries without the overhead of a database server.
- **Realistic Data Generation:** Leverages `Faker` to produce 10k+ rows of domain-specific data, including fraud patterns (double-spend) and categorical taxonomies.
- **Dockerized Environment:** One-command setup for consistent benchmarking and testing.

---

## 🛠️ Quick Start (Docker)
The easiest way to run DataWrangler is via Docker Desktop.

1. **Launch a Scenario:**
   ```bash
   # Default: Fintech Scenario
   docker-compose up --build

   # Or run a specific scenario (e.g., NLP Taxonomy)
   docker-compose run -e SCENARIO=nlp data-wrangler
   ```

2. **Explore the Data:**
   Once the container is running, you can jump into the DuckDB shell:
   ```bash
   docker exec -it fintech_analysis_env duckdb fintech_analysis.db
   ```

---

## 📂 Project Structure
- `wrangler/`: Core abstract engine and base classes.
- `datasets/`: Domain-specific logic.
    - `fintech/`: Banking transactions, KYC status, and fraud-testing logic.
    - `nlp/`: Categorical sorting, sentiment analysis, and taxonomy ranking.
- `main.py`: The orchestrator for generating CSVs and initializing the DB.
- `docker-compose.yml`: DevOps configuration for portable execution.

---

## 📈 Benchmarking & Analysis
DataWrangler is built for optimization testing. Each scenario includes a `schema.sql` that demonstrates:
- **Fintech:** Window functions for rapid-fire transaction detection.
- **NLP:** Aggregations for sentiment ranking across complex categories.

---

## 🧪 Legacy Support
For the original ETL functions (v1.0), refer to the `common/` and `src/` directories. Note that the new modular framework is the recommended path for new analytical assessments.

**Author:** [blcrosbie](https://github.com/blcrosbie)  
**License:** MIT
