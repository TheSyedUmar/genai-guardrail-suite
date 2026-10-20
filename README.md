# GenAI Guardrail & Validation Suite

[![GenAI quality gate](https://github.com/YOUR-USERNAME/genai-guardrail-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/genai-guardrail-suite/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-25%20automated-brightgreen)

An automated quality and safety testing framework for RAG chatbots. It attacks a chatbot with prompt injections, grades its answers for hallucinations with an LLM judge, validates its API contract, measures latency under load, and drives its UI with Playwright and Selenium. Every run is tracked in MLflow, and a CI/CD pipeline blocks any change that lowers quality.

Built entirely on free tools: OpenAI's open-weight `gpt-oss` models served through Groq's free OpenAI-compatible API, plus open-source libraries.

![Chatbot under test](docs/screenshots/chatbot-ui.png)

## Why this project

LLM applications fail in ways traditional software doesn't: they can be talked into leaking secrets, they make up facts, and the same question can get different answers on different runs. This suite treats those failure modes as testable requirements, so a chatbot can't ship unless it passes them.

## Key results

**1. The accuracy eval found two real bugs, which were fixed at the source.**

| Run | Accuracy pass rate | What happened |
|---|---|---|
| Before | 83% | Failed the 85% quality gate |
| After | **100%** | Both root causes fixed |

- A **retrieval bug**: keyword search didn't match "password" to "passwords", so the bot never saw the right document. Fixed by switching to character n-gram TF-IDF.
- A **generation bug**: the model named only one of two required approvers. Fixed in the system prompt.

**2. The security suite compared models and proved the guardrail works.**

| Chat model | Output guardrail | Attacks blocked |
|---|---|---|
| gpt-oss-20b | Off | 10 / 10 |
| allam-2-7b | Off | 8 / 10 |
| allam-2-7b | On | **10 / 10** |

The smaller model leaked the secret twice: once *inside a refusal* translated into French ("I can't share the admin code ZEBRA-4471…"), and once hidden in the last line of a poem. A check that only asks "did the model refuse?" would have missed the first one. With the output guardrail on, the same weak model blocked every attack: defense in depth instead of trusting the model alone.

![Model and guardrail comparison in MLflow](docs/screenshots/mlflow-runs-comparison.png)

## Architecture

```mermaid
flowchart LR
    subgraph App["Chatbot under test (FastAPI)"]
        UI[Chat web page] --> API["/chat endpoint"]
        API --> R[Retriever<br/>TF-IDF over policy docs]
        R --> LLM[gpt-oss-20b via<br/>OpenAI SDK + Groq]
        LLM --> G[Output guardrail]
    end
    subgraph Suite["Test suite (PyTest)"]
        S[Security]
        A[Accuracy + LLM judge]
        C[Schema]
        P[Performance]
        B[Playwright + Selenium]
    end
    Suite --> API
    B --> UI
    Suite --> M[(MLflow)]
    CI[GitHub Actions /<br/>Azure DevOps] --> Suite
```

## What gets tested

| Suite | What it checks | Quality gate |
|---|---|---|
| Security | 10 prompt injection attacks: instruction override, fake admin authority, roleplay jailbreak, prompt extraction, base64 encoding, reversal, spelling out, translation, hidden in a creative task | **Zero leaks** |
| Accuracy | 12 golden questions (including 3 the bot must decline), graded by `gpt-oss-120b` as an LLM judge for correctness and groundedness | ≥ 85% pass rate |
| Schema | JSON response contract with Pydantic; invalid requests rejected with 422 | All pass |
| Performance | p95 latency for one user and for 10 concurrent users | < 3 s / < 10 s |
| UI (Playwright) | Page loads, user gets an answer, empty input blocked, injection through the UI | All pass |
| UI (Selenium) | The same user flow with Selenium WebDriver | All pass |

Security uses zero tolerance because one leaked secret is a real incident. Accuracy uses a pass rate because LLM answers vary slightly between runs.

![All 25 tests passing](docs/screenshots/tests-all-passed.png)

## Tech stack

| Area | Tools |
|---|---|
| Language and test runner | Python, PyTest |
| Chatbot under test | FastAPI, scikit-learn (retrieval), OpenAI Python SDK |
| LLMs | `gpt-oss-20b` (chatbot), `gpt-oss-120b` (judge), served free by Groq |
| LLM evaluation | OpenAI Evals pattern: eval dataset → model answer → grader → score |
| UI automation | Playwright, Selenium |
| Validation | Pydantic |
| Experiment tracking | MLflow |
| CI/CD | GitHub Actions, Azure DevOps Pipelines |

## Experiment tracking with MLflow

Every test run logs its parameters (chat model, judge model, guardrail on/off) and metrics (injection block rate, accuracy pass rate, average correctness and groundedness, p50/p95 latency, test pass rate), plus every answer and judge score as a JSON artifact for debugging.

![Run metrics in MLflow](docs/screenshots/mlflow-run-metrics.png)

## Quick start

Requirements: Python 3.10+ and a free Groq API key from https://console.groq.com/keys (no credit card needed).

```bash
git clone https://github.com/YOUR-USERNAME/genai-guardrail-suite.git
cd genai-guardrail-suite
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env          # Mac/Linux: cp .env.example .env
# then add your key to GROQ_API_KEY in .env
```

Run it:

```bash
uvicorn app.main:app --reload   # try the chatbot at http://127.0.0.1:8000
pytest                          # full suite; starts the app automatically
pytest -m security              # or one suite: security, accuracy, schema, performance, ui
pytest -m ui --headed           # watch the browser tests run
mlflow ui --backend-store-uri sqlite:///mlflow.db   # dashboard at http://127.0.0.1:5000
```

## Demo: catching a leak

Run the security suite with a smaller model and the guardrail off, then on:

```bash
# Windows Command Prompt
set ENABLE_OUTPUT_GUARD=false
set CHAT_MODEL=allam-2-7b
pytest -m security
set ENABLE_OUTPUT_GUARD=
pytest -m security
```

![Security suite catching leaks with the guardrail off](docs/screenshots/guardrail-off-leak.png)

## CI/CD

On every push, GitHub Actions installs the project, runs all 25 tests against the live models, and fails the build if any quality gate fails. The JUnit test report and MLflow database are uploaded as build artifacts. `azure-pipelines.yml` provides the same pipeline for Azure DevOps, with results published to its Tests tab.

The Groq API key is stored as a repository secret and never committed.

![CI pipeline passing](docs/screenshots/ci-pipeline-passed.png)

## Project structure

```
app/              chatbot under test: API, retriever, LLM client, output guardrail, web page
data/docs/        HR policy documents the chatbot answers from
evals/            golden dataset, attack prompts, LLM judge, leak detection
tests/            PyTest suites, quality gates, MLflow logging
.github/workflows GitHub Actions pipeline
azure-pipelines.yml
```

## Lessons learned

- **Read the judge's reasons, not just the score.** The 83% result alone said "something is wrong"; the judge's reasons pointed to two different root causes in two different components.
- **Test retrieval and generation separately.** A low groundedness score with "no context" means retrieval failed; a high groundedness score with low correctness means generation failed.
- **A refusal is not proof of safety.** Leak detection has to inspect the reply's content, including spaced-out, reversed, encoded and translated forms.
- **Don't lower a threshold to make a test pass.** Fixing the cause raised accuracy from 83% to 100%; changing the gate would have hidden two bugs.

## Author

**Syed Umar**