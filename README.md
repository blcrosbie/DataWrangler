# DataWrangler SQL Screening Prep

DataWrangler is now a focused SQL screening-prep repo built around one realistic fintech-style dataset and two practice targets:

- DuckDB for fast local iteration
- Postgres 16 for DBeaver-backed practice in a warehouse-style environment

It is designed to rehearse the kinds of SQL work that show up in analytics and data engineering screens:

- joins
- CTEs
- window functions
- deduping and latest-state logic
- fraud/anomaly detection
- KPI aggregation
- activation and cohort analysis

## What You Get

- A seeded dataset with users, accounts, merchants, and raw `transaction_events`
- Repeatable CSV generation and DuckDB rebuilds
- A Postgres 16 quiz environment
- Curated SQL prompts in quiz mode
- Timed mock exams for `data_analyst` and `data_engineer`
- A self-grading harness that checks your answers without showing the hidden result rows

## Repo Layout

- [prep/](prep): CLI, dataset generation, mock exam, and grading logic
- [practice/questions.json](practice/questions.json): prompt bank
- [practice/solutions/duckdb.sql](practice/solutions/duckdb.sql): DuckDB reference answers
- [practice/solutions/postgres.sql](practice/solutions/postgres.sql): Postgres reference answers
- [practice/schema_reference.md](practice/schema_reference.md): schema guide
- [practice/exercises.md](practice/exercises.md): exercise index
- [practice/mock_exam_guide.md](practice/mock_exam_guide.md): mock-exam workflow
- [sql/schema.sql](sql/schema.sql): shared practice schema
- [sql/postgres/reset.sql](sql/postgres/reset.sql): Postgres reset entrypoint
- `practice_data/*.csv`: seeded data assets
- `artifacts/screening_prep.duckdb`: generated local DuckDB database

## Prerequisites

- Python 3.11+
- Docker Desktop if you want Postgres quiz mode
- DBeaver optional, but useful for Postgres practice

Install local Python dependencies:

```bash
pip install -r requirements.txt
```

## First-Time Setup

Build the local practice assets and DuckDB database:

```bash
python main.py setup --engine duckdb --force
```

This creates or refreshes:

- `practice_data/users.csv`
- `practice_data/accounts.csv`
- `practice_data/merchants.csv`
- `practice_data/transaction_events.csv`
- `artifacts/screening_prep.duckdb`
- `artifacts/dataset_manifest.json`

Open `artifacts/screening_prep.duckdb` directly in DBeaver or the DuckDB CLI if you want a local-only workflow.

## Core Commands

Rebuild only the CSV assets:

```bash
python main.py setup --engine assets --force
```

Rebuild the DuckDB database:

```bash
python main.py setup --engine duckdb --force
```

Pull random quiz prompts:

```bash
python main.py quiz --random --count 1
python main.py quiz --difficulty medium --count 2
python main.py quiz --topic fraud --count 2
python main.py quiz --track data_engineer --random --count 2
```

## Postgres 16 Quiz Mode

If you want to practice in DBeaver against Postgres 16:

```bash
docker compose -f docker-compose.quiz.yml up --build -d postgres16 quiz-shell
```

Reset Postgres back to the seeded state at any time:

```bash
docker compose -f docker-compose.quiz.yml run --rm postgres-reset
```

DBeaver connection details:

- Host: `localhost`
- Port: `55432`
- Database: `screening_prep`
- User: `quiz_user`
- Password: `quiz_pass`

Notes:

- Postgres and DuckDB use the same `practice_data/*.csv` assets
- if you regenerate assets, run the Postgres reset command again

## Mock Exams

There are two timed mock-exam tracks:

- `data_analyst`: 60 minutes, KPI and cohort heavy
- `data_engineer`: 75 minutes, deduping and event-grain heavy

Generate a mock exam:

```bash
python main.py mock-exam --track data_analyst
python main.py mock-exam --track data_engineer --seed 99
python main.py mock-exam --track data_engineer --duration-min 90
```

Each run creates a timestamped folder under `artifacts/mock_exams/<track>/` with:

- `exam.md`
- `answers.sql`
- `metadata.json`

The intended workflow is:

1. Generate one exam.
2. Open `exam.md` to read the prompts.
3. Write only your final answer queries inside the `-- BEGIN ANSWER ...` / `-- END ANSWER ...` blocks in `answers.sql`.
4. Do not open the solution files until you finish the timer.
5. Grade the attempt.

## Self-Grading

Grade a completed mock exam:

```bash
python main.py grade-exam --exam-dir artifacts/mock_exams/data_analyst/<timestamp>
```

Optional: point grading at a different answer file:

```bash
python main.py grade-exam --exam-dir artifacts/mock_exams/data_engineer/<timestamp> --answers path/to/answers.sql
```

The grader currently runs against the DuckDB practice database and checks:

- output column names and order
- row count
- final result signature against the hidden DuckDB reference answer

It writes `grade_report.json` into the same exam folder.

Status meanings:

- `ok`: your final query matched
- `missing`: no query found for that question
- `mismatch`: query ran, but output shape or result did not match
- `error`: query failed to execute or did not return a result set

## Recommended Practice Loop

If you want to simulate the real assessment closely, use this loop:

1. Reset your environment:

```bash
python main.py setup --engine duckdb --force
docker compose -f docker-compose.quiz.yml run --rm postgres-reset
```

2. Generate one exam:

```bash
python main.py mock-exam --track data_analyst
```

3. Work the exam in DuckDB or Postgres.

4. Grade it:

```bash
python main.py grade-exam --exam-dir artifacts/mock_exams/data_analyst/<timestamp>
```

5. Review the missed questions against:

- [practice/solutions/duckdb.sql](practice/solutions/duckdb.sql)
- [practice/solutions/postgres.sql](practice/solutions/postgres.sql)

6. Repeat with the other track.

## Docker Helper

The default compose file gives you a helper container that rebuilds the DuckDB database and stays alive for ad hoc commands:

```bash
docker compose up --build -d
docker compose exec sql-prep python main.py quiz --random --count 1
docker compose exec sql-prep python main.py mock-exam --track data_engineer
```

## Verification

The active prep workflow is covered by pytest:

```bash
pytest
```

This validates:

- dataset generation
- DuckDB initialization
- quiz filters
- mock-exam generation
- self-grading flow

## Notes

- The legacy `common/`, `src/`, and older tests are still in the repo, but they are not the active practice workflow.
- The grading harness is intentionally strict about output shape and result correctness.
- The Postgres environment is for practice execution; the current self-grader evaluates against DuckDB.
