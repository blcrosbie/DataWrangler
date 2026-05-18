# Exercise Index

These prompts are tuned for 30 to 60 minute screening sessions.

## Suggested order

1. `Q01` joins + latest-state filtering
2. `Q02` window-based deduping
3. `Q03` ranking with partitions
4. `Q04` funnel conversion
5. `Q05` cohorting
6. `Q06` rapid-fire fraud detection
7. `Q07` repeated-amount anomaly detection
8. `Q08` decline-rate KPI
9. `Q09` fee revenue aggregation
10. `Q10` business vs consumer volume mix

## Fast quiz commands

```bash
python main.py quiz --random --count 1
python main.py quiz --topic fraud --count 2
python main.py quiz --difficulty hard --random --count 2
python main.py quiz --track data_engineer --random --count 2
```

## Mock exams

```bash
python main.py mock-exam --track data_analyst
python main.py mock-exam --track data_engineer --seed 99
python main.py mock-exam --track data_engineer --duration-min 90
```

Each run writes:

- `artifacts/mock_exams/<track>/<timestamp>/exam.md`
- `artifacts/mock_exams/<track>/<timestamp>/answers.sql`
- `artifacts/mock_exams/<track>/<timestamp>/metadata.json`

## Files

- Prompts: [questions.json](questions.json)
- Postgres solutions: [solutions/postgres.sql](solutions/postgres.sql)
- DuckDB solutions: [solutions/duckdb.sql](solutions/duckdb.sql)
