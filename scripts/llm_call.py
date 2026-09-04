#!/usr/bin/env python3
"""
One place that knows how a model call fails, and what to do about each kind.

Three failure modes were being collapsed into one across this repo, and the
collapse is expensive in both directions:

  TRANSPORT   the gateway, the daemon or auth failed and the model NEVER RAN.
              Retrying almost always works. Counting it as a content failure
              silently drops the item and understates coverage -- 29% of the v2
              execution pass was this, misreported as the model disobeying its
              output contract.

  FORMAT      the model ran and answered, but not in the shape asked for.
              Retrying sometimes works; repairing the text often works better.

  CONTENT     the model ran, understood, and produced nothing usable -- an empty
              or refusing answer. Retrying is waste; record and move on.

Classify first, then retry only what retrying can fix.
"""
from __future__ import annotations
import random, re, time
from typing import Callable

TRANSPORT = re.compile(
    r"failed to create stream|inference request failed|failed to generate stream|"
    r"failed to invoke model|failed to send request|ai-gateway|502|503|504|"
    r"timed? ?out|connection (reset|refused|aborted)|ECONNRESET|rate limit|"
    r"unauthorized|authentication|too many requests", re.I)

REFUSAL = re.compile(r"^\s*(i (can|cannot|can't|won't)|as an ai|sorry[,.]? i)", re.I)


class Transport(RuntimeError):
    """The model never ran. Retry."""


class Format(ValueError):
    """The model ran; the output does not parse. Retry or repair."""


def classify(raw: str) -> str:
    if raw is None:
        return "transport"
    t = raw.strip()
    if not t:
        return "transport"          # an empty body is a dropped call, not a refusal
    # a transport error arrives AS the answer text, short and diagnostic
    if len(t) < 600 and TRANSPORT.search(t):
        return "transport"
    if REFUSAL.match(t):
        return "content"
    return "ok"


def call(ask: Callable[[str, str, str], str], system: str, user: str, model: str,
         parse: Callable[[str], object], *, attempts: int = 4,
         base_delay: float = 2.0) -> tuple[object | None, str]:
    """Call, classify, retry what is retryable. Returns (parsed, status).

    `parse` raises Format when the text does not parse; anything it returns is
    accepted. Backoff is exponential with jitter, because a gateway that just
    failed is likely failing for everyone and a synchronised retry storm makes
    it worse.
    """
    last = "unknown"
    for i in range(attempts):
        try:
            raw = ask(system, user, model)
        except Exception as e:
            last = f"transport: {str(e)[:120]}"
            _sleep(base_delay, i); continue

        kind = classify(raw)
        if kind == "transport":
            last = f"transport: {raw.strip()[:120]}"
            _sleep(base_delay, i); continue
        if kind == "content":
            return None, f"content: {raw.strip()[:120]}"
        try:
            return parse(raw), "ok"
        except Format as e:
            last = f"format: {e}"
            _sleep(base_delay * 0.5, i); continue
    return None, last


def _sleep(base: float, attempt: int) -> None:
    time.sleep(base * (2 ** attempt) * (0.5 + random.random()))
