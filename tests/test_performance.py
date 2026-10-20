"""Latency and load tests."""
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

from evals.recorder import record
from tests import thresholds
from tests.conftest import p95

pytestmark = pytest.mark.performance

QUESTIONS = [
    "How many days of annual leave do I get?",
    "What is the minimum password length?",
    "Which days are mandatory office days?",
    "What is the travel meal allowance?",
    "How do I report a lost laptop?",
]


def timed_request(app_url: str, question: str) -> tuple[int, float]:
    start = time.perf_counter()
    response = requests.post(f"{app_url}/chat", json={"message": question}, timeout=120)
    return response.status_code, (time.perf_counter() - start) * 1000


def test_single_user_latency_p95(app_url):
    latencies = []
    for question in QUESTIONS:
        status, ms = timed_request(app_url, question)
        assert status == 200
        latencies.append(ms)
        record("latency_ms", ms)
    assert p95(latencies) < thresholds.LATENCY_P95_MS, f"p95 latency {p95(latencies):.0f} ms too slow"


def test_concurrent_users(app_url):
    questions = [QUESTIONS[i % len(QUESTIONS)] for i in range(thresholds.CONCURRENT_USERS)]
    with ThreadPoolExecutor(max_workers=thresholds.CONCURRENT_USERS) as pool:
        results = list(pool.map(lambda q: timed_request(app_url, q), questions))

    statuses = [status for status, _ in results]
    latencies = [ms for _, ms in results]
    for ms in latencies:
        record("concurrent_latency_ms", ms)

    assert all(s == 200 for s in statuses), f"Some requests failed under load: {statuses}"
    assert p95(latencies) < thresholds.CONCURRENT_P95_MS, f"p95 under load {p95(latencies):.0f} ms"
