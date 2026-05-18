from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from prep.dataset import resolve_paths
from prep.quiz import load_questions

TRACK_DATA_ANALYST = "data_analyst"
TRACK_DATA_ENGINEER = "data_engineer"
TRACKS = (TRACK_DATA_ANALYST, TRACK_DATA_ENGINEER)


@dataclass(frozen=True)
class ExamBlueprint:
    track: str
    title: str
    duration_min: int
    question_count: int
    difficulty_plan: tuple[str, ...]
    instructions: tuple[str, ...]
    scoring_notes: tuple[str, ...]


BLUEPRINTS: dict[str, ExamBlueprint] = {
    TRACK_DATA_ANALYST: ExamBlueprint(
        track=TRACK_DATA_ANALYST,
        title="Data Analyst Mock Exam",
        duration_min=60,
        question_count=5,
        difficulty_plan=("easy", "medium", "medium", "medium", "hard"),
        instructions=(
            "Optimize for readability first: use clear CTE names and stable sort order.",
            "Focus on business definitions, not just row filtering.",
            "State assumptions when handling nulls, duplicate events, or latest-state logic.",
        ),
        scoring_notes=(
            "Business correctness matters more than micro-optimizations.",
            "Use consistent date grain and metric definitions.",
            "Prefer one final answer query per question.",
        ),
    ),
    TRACK_DATA_ENGINEER: ExamBlueprint(
        track=TRACK_DATA_ENGINEER,
        title="Data Engineer Mock Exam",
        duration_min=75,
        question_count=5,
        difficulty_plan=("medium", "medium", "hard", "hard", "hard"),
        instructions=(
            "Prioritize robust deduping and lifecycle logic before final aggregation.",
            "Make intermediate steps explicit when the problem involves event collapse or anomaly detection.",
            "Be precise about grain: raw event, deduped event, or latest logical transaction.",
        ),
        scoring_notes=(
            "Data grain mistakes are more serious than minor syntax slips.",
            "A correct deduping strategy should be visible in the query.",
            "Window functions and self-joins are both acceptable if logic is sound.",
        ),
    ),
}


def get_blueprint(track: str) -> ExamBlueprint:
    try:
        return BLUEPRINTS[track]
    except KeyError as exc:
        raise ValueError(f"Unsupported track: {track}") from exc


def _questions_for_track(track: str, base_dir: Path | None = None) -> list[dict[str, object]]:
    questions = load_questions(base_dir)
    return [question for question in questions if track in question.get("tracks", [])]


def build_mock_exam(
    *,
    track: str,
    seed: int,
    duration_min: int | None = None,
    base_dir: Path | None = None,
) -> dict[str, object]:
    blueprint = get_blueprint(track)
    eligible = _questions_for_track(track, base_dir)
    if len(eligible) < blueprint.question_count:
        raise ValueError(f"Not enough questions configured for track {track}.")

    rng = random.Random(seed)
    remaining = eligible[:]
    selected: list[dict[str, object]] = []

    for difficulty in blueprint.difficulty_plan:
        pool = [question for question in remaining if question["difficulty"] == difficulty]
        if not pool:
            pool = remaining
        chosen = rng.choice(pool)
        selected.append(chosen)
        remaining = [question for question in remaining if question["id"] != chosen["id"]]

    actual_duration = duration_min or blueprint.duration_min
    return {
        "track": track,
        "title": blueprint.title,
        "duration_min": actual_duration,
        "question_count": blueprint.question_count,
        "seed": seed,
        "instructions": list(blueprint.instructions),
        "scoring_notes": list(blueprint.scoring_notes),
        "questions": selected,
    }


def _exam_run_dir(track: str, base_dir: Path | None = None) -> Path:
    paths = resolve_paths(base_dir)
    run_root = paths.artifacts_dir / "mock_exams" / track
    run_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return run_root / timestamp


def _checkpoints(duration_min: int) -> list[str]:
    return [
        f"0-{max(5, duration_min // 6)} min: scan all prompts and define grain/assumptions.",
        f"{max(5, duration_min // 6)}-{max(20, duration_min // 2)} min: finish the first two questions cleanly.",
        f"{max(20, duration_min // 2)}-{max(35, (duration_min * 4) // 5)} min: complete the harder questions.",
        f"{max(35, (duration_min * 4) // 5)}-{duration_min} min: validate row counts, ordering, and edge cases.",
    ]


def write_mock_exam(
    exam: dict[str, object],
    *,
    base_dir: Path | None = None,
) -> dict[str, Path]:
    run_dir = _exam_run_dir(str(exam["track"]), base_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now().replace(second=0, microsecond=0)
    finish_by = started_at + timedelta(minutes=int(exam["duration_min"]))

    exam_md = run_dir / "exam.md"
    answers_sql = run_dir / "answers.sql"
    metadata_json = run_dir / "metadata.json"

    exam_lines = [
        f"# {exam['title']}",
        "",
        f"- Track: `{exam['track']}`",
        f"- Duration: `{exam['duration_min']} minutes`",
        f"- Seed: `{exam['seed']}`",
        f"- Start at: `{started_at.isoformat(timespec='minutes')}`",
        f"- Finish by: `{finish_by.isoformat(timespec='minutes')}`",
        "",
        "## Instructions",
    ]
    exam_lines.extend([f"- {line}" for line in exam["instructions"]])
    exam_lines.extend(["", "## Timing Checkpoints"])
    exam_lines.extend([f"- {line}" for line in _checkpoints(int(exam["duration_min"]))])
    exam_lines.extend(["", "## Scoring Notes"])
    exam_lines.extend([f"- {line}" for line in exam["scoring_notes"]])
    exam_lines.extend(["", "## Questions"])

    answer_sections: list[str] = [
        f"-- {exam['title']}",
        f"-- Track: {exam['track']}",
        f"-- Duration: {exam['duration_min']} minutes",
        f"-- Seed: {exam['seed']}",
        "",
    ]

    for index, question in enumerate(exam["questions"], start=1):
        exam_lines.extend(
            [
                f"### {index}. [{question['id']}] {question['title']}",
                f"- Difficulty: `{question['difficulty']}`",
                f"- Topics: `{', '.join(question['topics'])}`",
                "",
                str(question["prompt"]).strip(),
                "",
            ]
        )
        answer_sections.extend(
            [
                f"-- Question {index}: [{question['id']}] {question['title']}",
                f"-- Difficulty: {question['difficulty']}",
                f"-- Topics: {', '.join(question['topics'])}",
                "",
                f"-- BEGIN ANSWER {question['id']}",
                "",
                f"-- Write your final answer query for {question['id']} below.",
                "",
                f"-- END ANSWER {question['id']}",
                "",
            ]
        )

    exam_md.write_text("\n".join(exam_lines).rstrip() + "\n", encoding="utf-8")
    answers_sql.write_text("\n".join(answer_sections).rstrip() + "\n", encoding="utf-8")
    metadata_json.write_text(
        json.dumps(
            {
                "track": exam["track"],
                "title": exam["title"],
                "duration_min": exam["duration_min"],
                "seed": exam["seed"],
                "question_ids": [question["id"] for question in exam["questions"]],
                "started_at": started_at.isoformat(timespec="minutes"),
                "finish_by": finish_by.isoformat(timespec="minutes"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "run_dir": run_dir,
        "exam_md": exam_md,
        "answers_sql": answers_sql,
        "metadata_json": metadata_json,
    }
