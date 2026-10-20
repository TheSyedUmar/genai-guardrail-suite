"""Collects scores during the test run so they can be logged to MLflow at the end."""
RESULTS: dict[str, list] = {}


def record(category: str, value) -> None:
    RESULTS.setdefault(category, []).append(value)
