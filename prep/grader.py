from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb

from prep.dataset import resolve_paths


@dataclass(frozen=True)
class QueryResultSignature:
    columns: tuple[str, ...]
    row_count: int
    result_hash: str


def _extract_solution_queries(solution_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_id: str | None = None
    for line in solution_text.splitlines():
        if line.startswith("-- Q"):
            current_id = line.replace("--", "").strip()
            sections[current_id] = []
            continue
        if current_id is not None:
            sections[current_id].append(line)
    return {question_id: "\n".join(lines).strip() for question_id, lines in sections.items()}


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    prev_char = ""
    for char in sql_text:
        if char == "'" and not in_double and prev_char != "\\":
            in_single = not in_single
        elif char == '"' and not in_single and prev_char != "\\":
            in_double = not in_double
        if char == ";" and not in_single and not in_double:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        prev_char = char
    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def _extract_answer_queries(answer_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_id: str | None = None
    collecting = False
    marker_mode = False

    for line in answer_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("-- BEGIN ANSWER "):
            marker_mode = True
            current_id = stripped.replace("-- BEGIN ANSWER ", "").strip()
            sections[current_id] = []
            collecting = True
            continue

        if stripped.startswith("-- END ANSWER "):
            collecting = False
            current_id = None
            continue

        if stripped.startswith("-- Question ") and "[" in stripped and "]" in stripped and not marker_mode:
            current_id = stripped.split("[", 1)[1].split("]", 1)[0].strip()
            sections[current_id] = []
            collecting = True
            continue

        if collecting and current_id is not None:
            sections[current_id].append(line)

    answer_queries: dict[str, str] = {}
    for question_id, lines in sections.items():
        candidate = _strip_comment_lines("\n".join(lines))
        statements = _split_sql_statements(candidate)
        answer_queries[question_id] = statements[-1] if statements else ""
    return answer_queries


def _strip_comment_lines(sql_text: str) -> str:
    cleaned_lines = []
    for line in sql_text.splitlines():
        if line.strip().startswith("--"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _normalize_value(value: object) -> str:
    if value is None:
        return "<NULL>"
    if isinstance(value, float):
        return f"{value:.10f}"
    return str(value)


def _signature_from_rows(columns: list[str], rows: list[tuple[object, ...]]) -> QueryResultSignature:
    payload = "\n".join(
        [
            "|".join(columns),
            *["|".join(_normalize_value(value) for value in row) for row in rows],
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return QueryResultSignature(columns=tuple(columns), row_count=len(rows), result_hash=digest)


def _run_query(connection: duckdb.DuckDBPyConnection, query: str) -> QueryResultSignature:
    relation = connection.execute(query)
    if relation.description is None:
        raise ValueError("Query did not return a result set.")
    columns = [column[0] for column in relation.description]
    rows = relation.fetchall()
    return _signature_from_rows(columns, rows)


def _load_reference_signatures(
    *,
    db_path: Path,
    solution_path: Path,
    question_ids: list[str],
) -> dict[str, QueryResultSignature]:
    solution_queries = _extract_solution_queries(solution_path.read_text(encoding="utf-8"))
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        signatures = {}
        for question_id in question_ids:
            query = solution_queries[question_id]
            signatures[question_id] = _run_query(connection, query)
        return signatures
    finally:
        connection.close()


def grade_exam(
    *,
    exam_dir: Path,
    answers_path: Path | None = None,
    base_dir: Path | None = None,
) -> dict[str, object]:
    paths = resolve_paths(base_dir)
    package_root = Path(__file__).resolve().parents[1]
    metadata_path = exam_dir / "metadata.json"
    answers_sql_path = answers_path or exam_dir / "answers.sql"
    report_path = exam_dir / "grade_report.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    question_ids: list[str] = metadata["question_ids"]

    solution_path = package_root / "practice" / "solutions" / "duckdb.sql"
    reference = _load_reference_signatures(
        db_path=paths.duckdb_path,
        solution_path=solution_path,
        question_ids=question_ids,
    )
    answer_queries = _extract_answer_queries(answers_sql_path.read_text(encoding="utf-8"))

    connection = duckdb.connect(str(paths.duckdb_path), read_only=True)
    question_reports: list[dict[str, object]] = []
    passed_count = 0
    try:
        for question_id in question_ids:
            expected = reference[question_id]
            answer_query = answer_queries.get(question_id, "").strip()
            if not answer_query:
                question_reports.append(
                    {
                        "question_id": question_id,
                        "status": "missing",
                        "passed": False,
                        "expected_columns": list(expected.columns),
                        "expected_row_count": expected.row_count,
                        "actual_columns": [],
                        "actual_row_count": 0,
                        "checks": {
                            "columns_match": False,
                            "row_count_match": False,
                            "result_match": False,
                        },
                    }
                )
                continue

            try:
                actual = _run_query(connection, answer_query)
                columns_match = actual.columns == expected.columns
                row_count_match = actual.row_count == expected.row_count
                result_match = actual.result_hash == expected.result_hash
                passed = columns_match and row_count_match and result_match
                if passed:
                    passed_count += 1
                question_reports.append(
                    {
                        "question_id": question_id,
                        "status": "ok" if passed else "mismatch",
                        "passed": passed,
                        "expected_columns": list(expected.columns),
                        "expected_row_count": expected.row_count,
                        "actual_columns": list(actual.columns),
                        "actual_row_count": actual.row_count,
                        "checks": {
                            "columns_match": columns_match,
                            "row_count_match": row_count_match,
                            "result_match": result_match,
                        },
                    }
                )
            except Exception as exc:
                question_reports.append(
                    {
                        "question_id": question_id,
                        "status": "error",
                        "passed": False,
                        "expected_columns": list(expected.columns),
                        "expected_row_count": expected.row_count,
                        "actual_columns": [],
                        "actual_row_count": 0,
                        "checks": {
                            "columns_match": False,
                            "row_count_match": False,
                            "result_match": False,
                        },
                        "error": str(exc),
                    }
                )
    finally:
        connection.close()

    report = {
        "track": metadata["track"],
        "title": metadata["title"],
        "question_ids": question_ids,
        "passed_questions": passed_count,
        "total_questions": len(question_ids),
        "score_pct": round((passed_count / max(len(question_ids), 1)) * 100, 1),
        "questions": question_reports,
        "report_path": str(report_path),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
