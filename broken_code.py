"""Intentionally broken LLM integration used for the LLM 911 demo.

This file shows a minimal example of how *not* to call an LLM:
- The timeout is unrealistically low (2 seconds).
- There are no retries or backoff for flaky network/LLM behavior.
- There is no error handling, so timeouts bubble straight up into Sentry.

This is the kind of code that would generate the timeout- and latency-related
incidents you see in the sample Sentry and Galileo data.
"""

from __future__ import annotations

import requests

# In a real app, this would be your LLM provider's HTTPS endpoint.
# We use an example.com-style placeholder so this code is not accidentally
# wired to a real service.
LLM_ENDPOINT = "https://api.llm-provider.example/v1/rewrite"


def rewrite_query(query: str) -> str:
    """Rewrite a user's natural-language query using an LLM.

    This function is intentionally "broken" for teaching purposes:

    - It uses a very small timeout (2 seconds), which is likely to cause
      ReadTimeout errors during normal production load or provider slowness.
    - It does not implement any retries or exponential backoff, so a single
      transient blip immediately surfaces as a user-visible failure.
    - It does not catch exceptions, so timeouts and HTTP errors propagate
      directly to the caller (and into Sentry).
    - It assumes the response JSON shape is always correct and does no
      validation, which can lead to confusing downstream errors.
    """

    # NOTE: Hard-coding timeout=2.0 means this call will regularly fail when
    # the upstream LLM is slow. This directly maps to the timeout incidents you
    # see in the sample Sentry events.
    response = requests.post(
        LLM_ENDPOINT,
        json={"query": query},
        timeout=2.0,  # <- TOO LOW: this is the root cause of frequent timeouts.
    )

    # NOTE: We immediately call raise_for_status() without any retries. A 500,
    # 502, 503, 504, or 429 from the provider will raise an exception instead of
    # being retried with backoff.
    response.raise_for_status()

    # NOTE: No validation of the response structure. If the provider changes its
    # schema or returns an error payload, this may KeyError or silently fall
    # back to returning the original query.
    data = response.json()
    return data.get("rewritten_query", query)
