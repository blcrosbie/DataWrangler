from __future__ import annotations

import duckdb

from prep.dataset import build_practice_assets, initialize_duckdb, resolve_paths
from prep.grader import grade_exam
from prep.mock_exam import TRACK_DATA_ANALYST, TRACK_DATA_ENGINEER, build_mock_exam, write_mock_exam
from prep.quiz import choose_questions, filter_questions, load_questions


def test_build_assets_and_duckdb(tmp_path):
    manifest = build_practice_assets(
        tmp_path,
        seed=7,
        user_count=30,
        merchant_count=12,
        logical_tx_count=80,
        force=True,
    )
    assert manifest["user_rows"] == 30
    assert manifest["merchant_rows"] == 12
    assert manifest["transaction_event_rows"] >= 80

    db_path = initialize_duckdb(tmp_path, force=True)
    connection = duckdb.connect(str(db_path))
    try:
        counts = dict(
            connection.execute(
                """
                SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
                UNION ALL
                SELECT 'accounts', COUNT(*) FROM accounts
                UNION ALL
                SELECT 'merchants', COUNT(*) FROM merchants
                UNION ALL
                SELECT 'transaction_events', COUNT(*) FROM transaction_events
                """
            ).fetchall()
        )
    finally:
        connection.close()

    assert counts["users"] == 30
    assert counts["accounts"] >= 30
    assert counts["merchants"] == 12
    assert counts["transaction_events"] >= 80


def test_quiz_filters():
    questions = load_questions()
    fraud_questions = filter_questions(questions, topics=["fraud"])
    assert fraud_questions
    assert all("fraud" in question["topics"] for question in fraud_questions)

    engineer_questions = filter_questions(questions, track=TRACK_DATA_ENGINEER)
    assert engineer_questions
    assert all(TRACK_DATA_ENGINEER in question["tracks"] for question in engineer_questions)

    selected = choose_questions(fraud_questions, count=2, randomize=True, seed=11)
    assert len(selected) == 2
    assert selected[0]["id"] != selected[1]["id"]


def test_mock_exam_generation(tmp_path):
    exam = build_mock_exam(track=TRACK_DATA_ANALYST, seed=17)
    assert exam["track"] == TRACK_DATA_ANALYST
    assert len(exam["questions"]) == 5
    assert all(TRACK_DATA_ANALYST in question["tracks"] for question in exam["questions"])

    outputs = write_mock_exam(exam, base_dir=tmp_path)
    exam_text = outputs["exam_md"].read_text(encoding="utf-8")
    answers_text = outputs["answers_sql"].read_text(encoding="utf-8")
    metadata_text = outputs["metadata_json"].read_text(encoding="utf-8")

    assert "Data Analyst Mock Exam" in exam_text
    assert "-- Question 1:" in answers_text
    assert "-- BEGIN ANSWER " in answers_text
    assert '"track": "data_analyst"' in metadata_text


def test_grade_exam(tmp_path):
    build_practice_assets(tmp_path, seed=7, user_count=30, merchant_count=12, logical_tx_count=80, force=True)
    initialize_duckdb(tmp_path, force=True)
    exam = build_mock_exam(track=TRACK_DATA_ANALYST, seed=17, base_dir=tmp_path)
    outputs = write_mock_exam(exam, base_dir=tmp_path)

    answers_path = outputs["answers_sql"]
    answer_text = answers_path.read_text(encoding="utf-8")
    replacement = """
WITH deduped AS (
    SELECT *
    FROM (
        SELECT
            te.*,
            ROW_NUMBER() OVER (
                PARTITION BY processor_reference
                ORDER BY ingested_at DESC, event_id DESC
            ) AS rn
        FROM transaction_events te
    ) ranked
    WHERE rn = 1
),
latest_tx AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY logical_tx_id
                ORDER BY event_time DESC, ingested_at DESC, event_id DESC
            ) AS rn
        FROM deduped d
    ) ranked
    WHERE rn = 1
)
SELECT
    DATE_TRUNC('month', event_time) AS month,
    tx_type,
    COUNT(*) AS settled_tx_count,
    SUM(amount) AS total_amount,
    SUM(fee_amount) AS total_fee_amount
FROM latest_tx
WHERE event_status = 'settled'
GROUP BY 1, 2
ORDER BY month, tx_type;
""".strip()
    answer_text = answer_text.replace(
        "-- BEGIN ANSWER Q09\n\n-- Write your final answer query for Q09 below.\n\n-- END ANSWER Q09",
        f"-- BEGIN ANSWER Q09\n{replacement}\n-- END ANSWER Q09",
    )
    answers_path.write_text(answer_text, encoding="utf-8")

    report = grade_exam(exam_dir=outputs["run_dir"], base_dir=tmp_path)
    assert report["total_questions"] == 5
    assert any(question["question_id"] == "Q09" and question["status"] == "ok" for question in report["questions"])
    assert any(question["status"] == "missing" for question in report["questions"])
