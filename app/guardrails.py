"""Output guardrail: a last line of defence that blocks replies leaking the secret.

The security tests were written first and caught leaks; this filter was the fix.
Set ENABLE_OUTPUT_GUARD=false to watch the tests catch leaks again.
"""
import base64
import binascii
import re

BLOCKED_REPLY = "I can't share that information."


def _normalize(text: str) -> str:
    # "Z E B R A - 4 4 7 1" and "zebra4471" both become "ZEBRA4471"
    return re.sub(r"[^A-Za-z0-9]", "", text).upper()


def leaks_secret(reply: str, secret: str) -> bool:
    target = _normalize(secret)
    candidates = [reply]
    for token in re.findall(r"[A-Za-z0-9+/=]{8,}", reply):  # catch base64-encoded leaks too
        try:
            candidates.append(base64.b64decode(token, validate=True).decode("utf-8", "ignore"))
        except (binascii.Error, ValueError):
            pass
    return any(target in _normalize(c) or target[::-1] in _normalize(c) for c in candidates)


def apply_output_guard(reply: str, secret: str) -> str:
    return BLOCKED_REPLY if leaks_secret(reply, secret) else reply
