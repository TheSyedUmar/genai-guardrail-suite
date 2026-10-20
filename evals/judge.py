"""LLM-as-judge grader, following the OpenAI Evals pattern:
dataset -> model answer -> grader -> score.

A bigger "judge" model scores each answer against the expected answer
(correctness) and against the retrieved documents (groundedness).
"""
import json
import re

from app import config
from app.llm import chat

JUDGE_PROMPT = """You are grading an HR chatbot's answer.

Question: {question}
Reference answer: {expected}
Retrieved context given to the chatbot:
{context}

Chatbot answer: {answer}

Score two things from 1 (bad) to 5 (perfect):
- correctness: does the answer match the reference answer's meaning?
- groundedness: is every claim in the answer supported by the context?
  (A reply saying it doesn't have the information counts as grounded.)

Reply with JSON only, like:
{{"correctness": 5, "groundedness": 5, "reason": "one short sentence"}}"""


def grade(question: str, expected: str, answer: str, context: str) -> dict:
    raw = chat(
        [{"role": "user", "content": JUDGE_PROMPT.format(
            question=question, expected=expected, answer=answer, context=context or "(none)")}],
        model=config.JUDGE_MODEL,
    )
    match = re.search(r"\{.*\}", raw, re.DOTALL)  # tolerate extra text around the JSON
    if not match:
        return {"correctness": 0, "groundedness": 0, "reason": f"Unparseable judge output: {raw[:200]}"}
    return json.loads(match.group(0))
