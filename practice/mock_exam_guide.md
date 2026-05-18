# Mock Exam Guide

## Tracks

### `data_analyst`

- Default duration: 60 minutes
- Emphasis: metric definitions, joins, ranking, activation, cohorts, and clean KPI aggregation

### `data_engineer`

- Default duration: 75 minutes
- Emphasis: deduping, event-grain reasoning, latest-state logic, anomaly detection, and robust transformations

## Commands

```bash
python main.py mock-exam --track data_analyst
python main.py mock-exam --track data_engineer --seed 42
```

## Recommended workflow

1. Reset your environment first.
2. Generate one mock exam.
3. Open the generated `exam.md` and `answers.sql`.
4. Work only in the blank answer template.
5. Grade your answers.
6. Compare your results to the solution files after the timer ends.

## Grading

```bash
python main.py grade-exam --exam-dir artifacts/mock_exams/data_analyst/<timestamp>
```

This writes `grade_report.json` into the exam folder.

The grader:

- checks columns and order
- checks row count
- checks the final result signature
- does not print the hidden expected rows

## Suggested review criteria

- Did you state or encode the correct grain?
- Did you dedupe before aggregating when the prompt required it?
- Did you use stable ordering and explicit filters?
- Did you avoid silently mixing statuses or currencies?
