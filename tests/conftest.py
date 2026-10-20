"""Shared test setup: starts the chatbot, provides helpers, and logs results to MLflow."""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

from app import config
from evals.recorder import RESULTS

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv("APP_PORT", "8000"))
OUTCOMES = {"passed": 0, "failed": 0}


# ---------- starting the app under test ----------

@pytest.fixture(scope="session")
def app_url():
    """Start the chatbot once for the whole test run (or use APP_URL if already running)."""
    if os.getenv("APP_URL"):
        yield os.environ["APP_URL"].rstrip("/")
        return
    if not config.GROQ_API_KEY:
        pytest.exit("GROQ_API_KEY is not set. Copy .env.example to .env and add your free Groq key.")

    url = f"http://127.0.0.1:{PORT}"
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)], cwd=ROOT
    )
    for _ in range(60):  # wait up to 30 s for the server to come up
        try:
            if requests.get(f"{url}/health", timeout=1).ok:
                break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        server.terminate()
        pytest.exit("The chatbot server did not start.")
    yield url
    server.terminate()
    server.wait()


def ask(app_url: str, message: str) -> dict:
    """Send one question to the chatbot API and return the JSON reply."""
    response = requests.post(f"{app_url}/chat", json={"message": message}, timeout=120)
    response.raise_for_status()
    return response.json()


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(round(0.95 * len(ordered))) - 1)]


# ---------- MLflow logging at the end of the run ----------

def pytest_runtest_logreport(report):
    if report.when == "call" and not report.skipped:
        OUTCOMES["passed" if report.passed else "failed"] += 1


def pytest_sessionfinish(session, exitstatus):
    if session.testscollected == 0 or os.getenv("DISABLE_MLFLOW") == "1":
        return
    import mlflow

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{ROOT / 'mlflow.db'}"))
    mlflow.set_experiment("genai-guardrail-suite")

    metrics = {"tests_passed": OUTCOMES["passed"], "tests_failed": OUTCOMES["failed"]}
    total = OUTCOMES["passed"] + OUTCOMES["failed"]
    if total:
        metrics["test_pass_rate"] = OUTCOMES["passed"] / total
    if RESULTS.get("security"):
        blocked = [r["blocked"] for r in RESULTS["security"]]
        metrics["injection_block_rate"] = sum(blocked) / len(blocked)
    if RESULTS.get("accuracy"):
        acc = RESULTS["accuracy"]
        metrics["accuracy_pass_rate"] = sum(r["passed"] for r in acc) / len(acc)
        metrics["avg_correctness"] = sum(r["correctness"] for r in acc) / len(acc)
        metrics["avg_groundedness"] = sum(r["groundedness"] for r in acc) / len(acc)
    if RESULTS.get("latency_ms"):
        metrics["latency_p50_ms"] = sorted(RESULTS["latency_ms"])[len(RESULTS["latency_ms"]) // 2]
        metrics["latency_p95_ms"] = p95(RESULTS["latency_ms"])
    if RESULTS.get("concurrent_latency_ms"):
        metrics["concurrent_p95_ms"] = p95(RESULTS["concurrent_latency_ms"])

    # Readable run names (local-2026-10-20-20-55) and the author shown as "Created by"
    run_name = os.getenv("GITHUB_SHA", "")[:8] or "local-" + time.strftime("%Y-%m-%d-%H-%M")
    author = os.getenv("RUN_AUTHOR", "Syed Umar")
    with mlflow.start_run(run_name=run_name, tags={"mlflow.user": author}):
        mlflow.log_params({
            "chat_model": config.CHAT_MODEL,
            "judge_model": config.JUDGE_MODEL,
            "output_guard": config.ENABLE_OUTPUT_GUARD,
        })
        mlflow.log_metrics(metrics)
        mlflow.log_dict(RESULTS, "detailed_results.json")  # every answer and score, for debugging