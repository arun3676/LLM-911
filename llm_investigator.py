import os
import json
import re
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
from anthropic import Anthropic, APIStatusError
from browser_use_sdk import BrowserUse

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "data" / ".env"


def _get_anthropic_client() -> Anthropic:
    """Initialize and return an Anthropic client using the API key from .env/env.

    This function is small and focused so it can be reused and tested.
    """
    # Load environment variables from the data/.env file (if present).
    # This is safe to call multiple times; it only populates missing env vars.
    load_dotenv(dotenv_path=ENV_PATH, override=False)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Please add it to your .env or environment."
        )

    return Anthropic(api_key=api_key)


def check_provider_status() -> str:
    """Use Browser Use Cloud to check Anthropic's status page.

    Returns a short human-readable summary about provider health. If Browser Use
    is not configured or fails, a fallback message is returned.
    """
    try:
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        api_key = os.getenv("BROWSER_USE_API_KEY")
        if not api_key:
            return "Browser Use failed, skipping provider check."

        client = BrowserUse(api_key=api_key)

        task = client.tasks.create_task(
            task=(
                "Visit https://status.anthropic.com/ and return the plain text of "
                "the page. Do not summarize; just output the visible text content."
            ),
            llm="gpt-4.1",
        )

        result = task.complete()
        page_text = str(getattr(result, "output", ""))
        text_lower = page_text.lower()

        if any(k in text_lower for k in ["degraded performance", "latency", "incident"]):
            return (
                "Provider status warning: Anthropic status page mentions possible "
                "issues (degraded performance/latency/incident)."
            )
        return "Provider status: No issues reported on Anthropic status page."
    except Exception:
        return "Browser Use failed, skipping provider check."


def run_code_review(code_snippet: str, sentry_error: dict, galileo_trace: dict) -> str:
    """Simple CodeRabbit-style review using only basic Python logic.

    Args:
        code_snippet: The related source code as a string.
        sentry_error: A dict that may contain ``error_type``.
        galileo_trace: A dict that may contain ``latency_seconds``.

    Returns:
        A single combined string summarizing these observations.
    """
    observations: list[str] = []

    error_type = str(sentry_error.get("error_type", ""))
    snippet_lower = code_snippet.lower()

    # If this is a timeout error and the code uses an explicit timeout parameter.
    if error_type == "TimeoutError" and "timeout=" in code_snippet:
        observations.append(
            "The incident is a TimeoutError and the code sets an explicit timeout; "
            "that timeout is probably too low for real-world LLM latency."
        )

    # If Galileo reports very high latency for this call.
    latency_value = galileo_trace.get("latency_seconds")
    try:
        if latency_value is not None and float(latency_value) > 10:
            observations.append(
                "The Galileo trace shows latency above 10 seconds; calls are slow "
                "and should be treated as retriable."
            )
    except (TypeError, ValueError):
        pass

    # If there is no mention of retry/backoff logic in the code.
    if "retry" not in snippet_lower and "backoff" not in snippet_lower:
        observations.append(
            "The code does not mention retries or backoff; consider adding retries "
            "with backoff around the external LLM call."
        )

    if not observations:
        observations.append(
            "No obvious issues detected in this short snippet, but double-check "
            "timeouts, retries, and latency handling."
        )

    return " ".join(observations)


def run_llm_911(sentry_incident: dict, galileo_trace: dict, broken_code: str) -> str:
    """Call Anthropic Claude to analyze an incident.

    Args:
        sentry_incident: Parsed JSON from Sentry describing the incident.
        galileo_trace: Parsed JSON from Galileo describing the model trace.
        broken_code: The related source code snippet (e.g., from broken_code.py).

    Returns:
        A plain-text report string with:
            - Root cause
            - Fix plan
            - Infra / latency / timeout observations

    Any errors are caught and turned into a human-readable error message string
    instead of throwing, so the Streamlit app doesn't crash.
    """
    # First, run a simple CodeRabbit-style review of the related code.
    code_review_summary = run_code_review(
        code_snippet=broken_code,
        sentry_error=sentry_incident,
        galileo_trace=galileo_trace,
    )

    try:
        client = _get_anthropic_client()
    except Exception as e:  # environment / config problems
        return (
            "[LLM 911 ERROR] Could not initialize Anthropic client. "
            f"Details: {e}"
        )

    # Build a clear, structured prompt for Claude.
    system_prompt = dedent(
        """
        You are LLM 911, an expert AI incident responder.

        You will be given two JSON objects:
        - One from Sentry describing an application or infrastructure incident.
        - One from Galileo describing an LLM/model trace or monitoring context.

        Your job is to carefully read both, correlate the information, and then
        produce a concise but thorough incident report aimed at an on-call
        engineer who is familiar with LLM systems.

        The report MUST be plain text and structured with clear headings:
        1) Root Cause
        2) Fix Plan
        3) Infra / Latency / Timeout Observations

        Be specific and actionable. If some information is missing, call that
        out explicitly and state reasonable assumptions.
        """
    ).strip()

    # We send the raw JSON objects as pretty-printed strings so Claude can see
    # the full context but still stay within a simple, text-only prompt.
    sentry_str = json.dumps(sentry_incident, indent=2, sort_keys=True)
    galileo_str = json.dumps(galileo_trace, indent=2, sort_keys=True)

    provider_status_summary = check_provider_status()

    user_prompt = dedent(
        f"""
        Provider status summary:
        {provider_status_summary}

        Here is a CodeRabbit-style review of the related source code:
        {code_review_summary}

        Here is the Sentry incident JSON:
        ```json
        {sentry_str}
        ```

        Here is the Galileo model trace JSON:
        ```json
        {galileo_str}
        ```

        Using ONLY the information above and reasonable engineering judgment,
        write the incident report now.
        """
    ).strip()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
        )
    except APIStatusError as e:
        # Specific Anthropic HTTP/API errors
        return (
            "[LLM 911 ERROR] Anthropic API error while generating the report. "
            f"Status: {e.status_code}, Details: {e}"
        )
    except Exception as e:  # network errors, timeouts, etc.
        return (
            "[LLM 911 ERROR] Unexpected error while calling the LLM. "
            f"Details: {e}"
        )

    # Anthropic's Python client returns a Message object.
    # We extract the text from the content blocks. For this simple use case,
    # we expect a single text block.
    try:
        # response.content is a list of blocks, usually one TextBlock
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        report_text = "\n".join(parts).strip()
        if not report_text:
            return "[LLM 911 ERROR] LLM returned an empty response."
        return report_text
    except Exception as e:
        return (
            "[LLM 911 ERROR] Could not parse LLM response. "
            f"Details: {e}"
        )
