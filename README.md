# DataWrangler SQL Screening Prep

DataWrangler is now a focused SQL screening-prep repo built around one realistic fintech-style dataset and two practice targets:

- DuckDB for fast local iteration
- Postgres 16 for DBeaver-backed practice in a warehouse-style environment
- Python algorithm drills for Codility-style correctness and performance checks

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
- A Codility-style Python and SQL harness for NULL, empty, negative-value, and large-input practice

## Repo Layout

- [prep/](prep): CLI, dataset generation, mock exam, and grading logic
- [practice/questions.json](practice/questions.json): prompt bank
- [practice/solutions/duckdb.sql](practice/solutions/duckdb.sql): DuckDB reference answers
- [practice/solutions/postgres.sql](practice/solutions/postgres.sql): Postgres reference answers
- [practice/schema_reference.md](practice/schema_reference.md): schema guide
- [practice/exercises.md](practice/exercises.md): exercise index
- [practice/mock_exam_guide.md](practice/mock_exam_guide.md): mock-exam workflow
- [data_wrangler/testing_harness.py](data_wrangler/testing_harness.py): Codility-style Python and SQL correctness/performance harness
- [data_wrangler/exercises/analytical_patterns.py](data_wrangler/exercises/analytical_patterns.py): Python hash map, sliding window, and two-pointer references
- [data_wrangler/exercises/sql_challenges.sql](data_wrangler/exercises/sql_challenges.sql): PostgreSQL reference challenges for sum, event deltas, and match points
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

## How Quiz Mode Works

`quiz` does not execute SQL for you. It prints one or more prompts, and you solve them yourself in DuckDB or Postgres.

### DuckDB quiz loop

1. Build the local database:

```bash
python main.py setup --engine duckdb --force
```

2. Print a prompt:

```bash
python main.py quiz --random --count 1
```

3. Open `artifacts/screening_prep.duckdb` in DBeaver or DuckDB CLI.

4. Write and run your SQL against these tables:

- `users`
- `accounts`
- `merchants`
- `transaction_events`

5. If you want to compare your answer after you finish, check:

- [practice/solutions/duckdb.sql](practice/solutions/duckdb.sql)

### Postgres quiz loop

1. Start Postgres 16:

```bash
docker compose -f docker-compose.quiz.yml up --build -d postgres16 quiz-shell
```

2. Print a prompt:

```bash
python main.py quiz --track data_engineer --random --count 1
```

3. Connect from DBeaver using:

- Host: `localhost`
- Port: `55432`
- Database: `screening_prep`
- User: `quiz_user`
- Password: `quiz_pass`

4. Write and run your SQL in DBeaver against the same four tables.

5. Reset the database when you want a clean state:

```bash
docker compose -f docker-compose.quiz.yml run --rm postgres-reset
```

6. Compare your answer after you finish, if needed:

- [practice/solutions/postgres.sql](practice/solutions/postgres.sql)

### Good quiz commands

Single random prompt:

```bash
python main.py quiz --random --count 1
```

Two data-analyst prompts:

```bash
python main.py quiz --track data_analyst --random --count 2
```

Two fraud-focused engineer prompts:

```bash
python main.py quiz --track data_engineer --topic fraud --count 2
```

One specific question by id:

```bash
python main.py quiz --id Q06
```

## Python and Codility-Style Practice

The `data_wrangler/` module is a compact practice set for the non-SQL part of a Codility-style screen. It focuses on patterns that avoid timeouts and memory blowups on large arrays:

- hash maps and sets for O(1) lookup
- sliding windows for cumulative stream metrics
- two pointers for sorted-array search and filtering
- SQL CTE/window-function exercises with NULL and empty-table handling

Run the harness locally:

```bash
python data_wrangler/testing_harness.py --rows 50000
```

For a faster smoke test:

```bash
python data_wrangler/testing_harness.py --rows 10000
```

The harness runs two matrices:

- Correctness: empty arrays, empty tables, NULL-only records, missing records, negative values, and sparse data
- Performance: synthetic 10,000+ row inputs, elapsed-time checks, and peak-memory checks

The SQL file is PostgreSQL-first, but the harness executes compatible query blocks through in-memory SQLite so you can run it without starting a database. For Postgres practice, copy the query blocks from [data_wrangler/exercises/sql_challenges.sql](data_wrangler/exercises/sql_challenges.sql) into DBeaver or `psql` against equivalent tables.

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

## Docker Exam Prep Platform

Use `docker-compose.quiz.yml` as the exam-prep platform. It gives you:

- `postgres16`: a real Postgres 16 database for SQL practice
- `quiz-shell`: an interactive Python/DuckDB/Postgres-client container
- `postgres-reset`: a one-command database reset
- `exam-harness`: a one-shot test runner for unit tests plus Codility-style checks

Start the full SQL practice environment:

```bash
docker compose -f docker-compose.quiz.yml up --build -d postgres16 quiz-shell
```

Run all repo unit tests and the new Codility-style Python/SQL harness inside Docker:

```bash
docker compose -f docker-compose.quiz.yml run --rm exam-harness
```

Use a larger synthetic dataset when you want a stricter performance pass:

```bash
ROWS=100000 docker compose -f docker-compose.quiz.yml run --rm exam-harness
```

On Windows PowerShell, set `ROWS` like this:

```powershell
$env:ROWS = "100000"
docker compose -f docker-compose.quiz.yml run --rm exam-harness
Remove-Item Env:ROWS
```

Run only the Codility-style harness inside the container:

```bash
docker compose -f docker-compose.quiz.yml run --rm quiz-shell python data_wrangler/testing_harness.py --rows 50000
```

Run only pytest inside the container:

```bash
docker compose -f docker-compose.quiz.yml run --rm quiz-shell pytest
```

Interactive container loop:

```bash
docker compose -f docker-compose.quiz.yml exec quiz-shell bash
python main.py quiz --random --count 1
python data_wrangler/testing_harness.py --rows 50000
pytest
```

## LeetCode-Style Practice Strategy

This repo should not depend on live LeetCode execution. LeetCode does not provide a stable official public judge API for arbitrary local submissions, and scraping or automating submissions is brittle and can violate platform rules.

The durable approach is to build local LeetCode-style adapters:

- Store each Python problem as a normal function in `data_wrangler/exercises/`.
- Store visible and hidden-style test cases as local pytest parametrizations.
- For SQL problems, keep each answer as a named SQL block and test it against seeded DuckDB, SQLite-compatible, or Postgres tables.
- Run everything through `exam-harness` so correctness and performance checks happen before you look at solutions.

A good target platform shape is:

- `data_wrangler/exercises/`: reference patterns and problem solutions
- `tests/codility/`: pytest tests for Python algorithms
- `tests/sql/`: SQL fixture setup and result-signature checks
- `practice/questions.json`: prompt metadata, difficulty, topic, and expected runtime class
- `docker-compose.quiz.yml`: one-shot `exam-harness` plus interactive `quiz-shell`

That gives you the same muscle memory LeetCode/Codility tests require: write a function or SQL query, run a hidden-style test suite, check edge cases, then increase input size until the algorithmic complexity is obvious.

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
- Docker exam-harness can also run the Codility-style Python and SQL practice checks

## Notes

- The legacy `common/`, `src/`, and older tests are still in the repo, but they are not the active practice workflow.
- The grading harness is intentionally strict about output shape and result correctness.
- The Postgres environment is for practice execution; the current self-grader evaluates against DuckDB.
- Live LeetCode integration should be treated as manual submit/review; local tests are the reliable automation layer.
