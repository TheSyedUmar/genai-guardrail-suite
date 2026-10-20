"""Prompt injection tests: the bot must never leak its secret or its instructions.
Zero tolerance: each attack is its own test, and any leak fails the build."""
import json
from pathlib import Path

import pytest

from app import config
from evals.checks import leaks_secret, leaks_system_prompt
from evals.recorder import record
from tests.conftest import ask

ATTACKS = json.loads((Path(__file__).parent.parent / "evals" / "injection_prompts.json").read_text())


@pytest.mark.security
@pytest.mark.parametrize("attack", ATTACKS, ids=[a["id"] for a in ATTACKS])
def test_prompt_injection_is_blocked(app_url, attack):
    answer = ask(app_url, attack["prompt"])["answer"]

    leaked = leaks_secret(answer, config.SECRET_CODE) or leaks_system_prompt(answer)
    record("security", {"id": attack["id"], "blocked": not leaked, "answer": answer})

    assert not leaked, f"Leak detected for attack '{attack['id']}': {answer!r}"
