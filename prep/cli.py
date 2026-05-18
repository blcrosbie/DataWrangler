from __future__ import annotations

import argparse
from pathlib import Path

from prep.dataset import (
    DEFAULT_LOGICAL_TX_COUNT,
    DEFAULT_MERCHANT_COUNT,
    DEFAULT_SEED,
    DEFAULT_USER_COUNT,
    build_practice_assets,
    initialize_duckdb,
    resolve_paths,
)
from prep.grader import grade_exam
from prep.mock_exam import TRACKS, build_mock_exam, write_mock_exam
from prep.quiz import choose_questions, filter_questions, load_questions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SQL screening prep workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Generate practice assets and optional DuckDB database")
    setup_parser.add_argument("--engine", choices=["assets", "duckdb"], default="duckdb")
    setup_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    setup_parser.add_argument("--user-count", type=int, default=DEFAULT_USER_COUNT)
    setup_parser.add_argument("--merchant-count", type=int, default=DEFAULT_MERCHANT_COUNT)
    setup_parser.add_argument("--logical-tx-count", type=int, default=DEFAULT_LOGICAL_TX_COUNT)
    setup_parser.add_argument("--force", action="store_true")

    quiz_parser = subparsers.add_parser("quiz", help="Print screening-style SQL prompts")
    quiz_parser.add_argument("--topic", action="append", dest="topics")
    quiz_parser.add_argument("--difficulty", choices=["easy", "medium", "hard"])
    quiz_parser.add_argument("--id", dest="question_id")
    quiz_parser.add_argument("--count", type=int, default=1)
    quiz_parser.add_argument("--random", action="store_true")
    quiz_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    quiz_parser.add_argument("--track", choices=TRACKS)

    mock_exam_parser = subparsers.add_parser("mock-exam", help="Generate a timed mock exam")
    mock_exam_parser.add_argument("--track", choices=TRACKS, required=True)
    mock_exam_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    mock_exam_parser.add_argument("--duration-min", type=int)

    grade_parser = subparsers.add_parser("grade-exam", help="Grade a completed mock exam answers.sql against DuckDB")
    grade_parser.add_argument("--exam-dir", required=True)
    grade_parser.add_argument("--answers")

    return parser


def _run_setup(args: argparse.Namespace) -> int:
    manifest = build_practice_assets(
        seed=args.seed,
        user_count=args.user_count,
        merchant_count=args.merchant_count,
        logical_tx_count=args.logical_tx_count,
        force=args.force,
    )
    paths = resolve_paths()
    print("Practice CSVs ready:")
    print(f"  {paths.practice_data_dir}")
    print(f"  users={manifest['user_rows']} accounts={manifest['account_rows']} merchants={manifest['merchant_rows']}")
    print(f"  transaction_events={manifest['transaction_event_rows']}")
    if args.engine == "duckdb":
        db_path = initialize_duckdb(force=args.force)
        print(f"DuckDB ready: {db_path}")
    print(f"Manifest: {paths.manifest_path}")
    return 0


def _render_question(question: dict[str, object]) -> str:
    prompt = "\n".join(
        [
            f"[{question['id']}] {question['title']}",
            f"Difficulty: {question['difficulty']}",
            f"Topics: {', '.join(question['topics'])}",
            f"Tracks: {', '.join(question.get('tracks', []))}",
            "",
            str(question["prompt"]).strip(),
        ]
    )
    return prompt


def _run_quiz(args: argparse.Namespace) -> int:
    questions = load_questions()
    filtered = filter_questions(
        questions,
        topics=args.topics,
        difficulty=args.difficulty,
        question_id=args.question_id,
        track=args.track,
    )
    if not filtered:
        raise SystemExit("No questions matched the supplied filters.")
    chosen = choose_questions(filtered, count=args.count, randomize=args.random, seed=args.seed)
    print("\n\n".join(_render_question(question) for question in chosen))
    return 0


def _run_mock_exam(args: argparse.Namespace) -> int:
    exam = build_mock_exam(
        track=args.track,
        seed=args.seed,
        duration_min=args.duration_min,
    )
    outputs = write_mock_exam(exam)
    print(f"{exam['title']} ready")
    print(f"  Track: {exam['track']}")
    print(f"  Duration: {exam['duration_min']} minutes")
    print(f"  Questions: {', '.join(question['id'] for question in exam['questions'])}")
    print(f"  Exam: {outputs['exam_md']}")
    print(f"  Answer template: {outputs['answers_sql']}")
    print(f"  Metadata: {outputs['metadata_json']}")
    return 0


def _resolve_cli_path(path_text: str) -> Path:
    candidate = Path(path_text)
    if candidate.is_absolute():
        return candidate
    return resolve_paths().root / candidate


def _run_grade_exam(args: argparse.Namespace) -> int:
    report = grade_exam(
        exam_dir=_resolve_cli_path(args.exam_dir),
        answers_path=_resolve_cli_path(args.answers) if args.answers else None,
    )
    print(f"Grade complete: {report['passed_questions']}/{report['total_questions']} passed ({report['score_pct']}%)")
    for question in report["questions"]:
        status = question["status"]
        question_id = question["question_id"]
        checks = question["checks"]
        summary = f"{question_id}: {status}"
        if status in {"ok", "mismatch"}:
            summary += (
                f" | columns={checks['columns_match']}"
                f" row_count={checks['row_count_match']}"
                f" result={checks['result_match']}"
            )
        if status == "error":
            summary += f" | error={question.get('error', '')}"
        print(summary)
    print(f"Report: {report['report_path']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "setup":
        return _run_setup(args)
    if args.command == "quiz":
        return _run_quiz(args)
    if args.command == "mock-exam":
        return _run_mock_exam(args)
    if args.command == "grade-exam":
        return _run_grade_exam(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2
