"""Contract tests: the API must always return the JSON shape the frontend expects."""
import pytest
import requests
from pydantic import BaseModel, ConfigDict, Field

from tests.conftest import ask

pytestmark = pytest.mark.schema


# The contract is defined here, separately from the app, so the test catches
# any accidental change to the response format.
class SourceContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: str
    snippet: str


class ChatContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1)
    sources: list[SourceContract]
    latency_ms: float = Field(ge=0)


def test_health_endpoint(app_url):
    assert requests.get(f"{app_url}/health").json() == {"status": "ok"}


def test_chat_response_matches_contract(app_url):
    response = requests.post(f"{app_url}/chat", json={"message": "What is the meal allowance?"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    ChatContract.model_validate(response.json())  # raises if any field is missing or wrong


def test_answerable_question_cites_a_source_document(app_url):
    data = ask(app_url, "How many sick leave days do I get?")
    assert data["sources"], "Expected at least one retrieved source"
    assert all(s["document"].endswith(".txt") for s in data["sources"])


@pytest.mark.parametrize("bad_body", [{"message": ""}, {}, {"msg": "hi"}, {"message": "x" * 2001}])
def test_invalid_requests_are_rejected(app_url, bad_body):
    assert requests.post(f"{app_url}/chat", json=bad_body).status_code == 422
