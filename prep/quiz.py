from __future__ import annotations

import json
import random
from pathlib import Path


def load_questions(base_dir: Path | None = None) -> list[dict[str, object]]:
    package_root = Path(__file__).resolve().parents[1]
    question_path = package_root / "practice" / "questions.json"
    return json.loads(question_path.read_text(encoding="utf-8"))


def filter_questions(
    questions: list[dict[str, object]],
    *,
    topics: list[str] | None = None,
    difficulty: str | None = None,
    question_id: str | None = None,
    track: str | None = None,
) -> list[dict[str, object]]:
    filtered = questions
    if topics:
        topic_set = {topic.lower() for topic in topics}
        filtered = [
            question
            for question in filtered
            if topic_set.intersection({topic.lower() for topic in question["topics"]})
        ]
    if difficulty:
        filtered = [question for question in filtered if question["difficulty"] == difficulty]
    if question_id:
        filtered = [question for question in filtered if question["id"] == question_id]
    if track:
        filtered = [
            question
            for question in filtered
            if track in question.get("tracks", [])
        ]
    return filtered


def choose_questions(
    questions: list[dict[str, object]],
    *,
    count: int = 1,
    randomize: bool = False,
    seed: int | None = None,
) -> list[dict[str, object]]:
    if count <= 0:
        return []
    if not randomize:
        return questions[:count]
    rng = random.Random(seed)
    sample_size = min(count, len(questions))
    return rng.sample(questions, k=sample_size)
