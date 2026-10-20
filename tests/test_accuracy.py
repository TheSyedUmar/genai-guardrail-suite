"""Hallucination and accuracy evaluation (OpenAI Evals pattern: dataset -> answer -> LLM judge).

Answers vary slightly between runs, so instead of failing on one bad answer
we fail if the overall pass rate drops below the threshold."""
import json
from pathlib import Path

import pytest

from evals.judge import grade
from evals.recorder import record
from tests import thresholds
from tests.conftest import ask

DATASET = json.loads((Path(__file__).parent.parent / "evals" / "golden_dataset.json").read_text())


@pytest.mark.accuracy
def test_answers_are_correct_and_grounded(app_url):
    failures = []
    for item in DATASET:
        data = ask(app_url, item["question"])
        context = "\n".join(s["snippet"] for s in data["sources"])
        scores = grade(item["question"], item["expected"], data["answer"], context)

        passed = (scores["correctness"] >= thresholds.MIN_JUDGE_SCORE
                  and scores["groundedness"] >= thresholds.MIN_JUDGE_SCORE)
        record("accuracy", {**item, "answer": data["answer"], **scores, "passed": passed})
        if not passed:
            failures.append(f"- {item['question']}\n  got: {data['answer']}\n  judge: {scores}")

    pass_rate = 1 - len(failures) / len(DATASET)
    print(f"\nAccuracy pass rate: {pass_rate:.0%}")
    assert pass_rate >= thresholds.ACCURACY_PASS_RATE, (
        f"Pass rate {pass_rate:.0%} is below {thresholds.ACCURACY_PASS_RATE:.0%}. Failed:\n"
        + "\n".join(failures)
    )
