import json
from pathlib import Path

import streamlit as st

from create_daytona_sandbox import create_daytona_sandbox
from llm_investigator import run_code_review, run_llm_911 as run_llm_911_llm

# ----- Constants for data files -----
DATA_DIR = Path("data")
SENTRY_FILE = DATA_DIR / "sample_sentry.json"
GALILEO_FILE = DATA_DIR / "sample_galileo.json"
BROKEN_CODE_FILE = Path("broken_code.py")
DAYTONA_WORKSPACE_URL = "https://app.daytona.io/workspaces/daytonaio/sandbox:0.4.3"


def init_session_state() -> None:
    """Make sure the keys we need exist in st.session_state."""
    if "sentry_incident" not in st.session_state:
        st.session_state.sentry_incident = None
    if "galileo_trace" not in st.session_state:
        st.session_state.galileo_trace = None
    if "report_text" not in st.session_state:
        st.session_state.report_text = ""
    if "broken_code" not in st.session_state:
        st.session_state.broken_code = ""
    if "code_review_summary" not in st.session_state:
        st.session_state.code_review_summary = ""
    if "daytona_status" not in st.session_state:
        st.session_state.daytona_status = {}


def load_json_file(path: Path):
    """Load a JSON file from disk and return the parsed Python object.

    Shows a Streamlit error message if something goes wrong.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"File not found: {path}")
    except json.JSONDecodeError:
        st.error(f"Could not parse JSON in: {path}")
    return None


def load_sample_incident() -> None:
    """Read the sample Sentry and Galileo JSON files and store them in session_state."""
    sentry_data = load_json_file(SENTRY_FILE)
    galileo_data = load_json_file(GALILEO_FILE)

    broken_code_text = ""
    try:
        with BROKEN_CODE_FILE.open("r", encoding="utf-8") as f:
            broken_code_text = f.read()
    except FileNotFoundError:
        st.warning(f"File not found: {BROKEN_CODE_FILE}")
    except OSError:
        st.warning(f"Could not read broken code file: {BROKEN_CODE_FILE}")

    st.session_state.broken_code = broken_code_text

    if sentry_data is not None and galileo_data is not None:
        # Derive a tiny incident summary for code review while retaining raw JSON.
        error_type = "UnknownError"
        if isinstance(sentry_data, list) and sentry_data:
            first_event = sentry_data[0]
            if isinstance(first_event, dict):
                tags = first_event.get("tags", {})
                if tags.get("incident_type") == "timeout":
                    error_type = "TimeoutError"

        latency_seconds = None
        if isinstance(galileo_data, dict):
            records = galileo_data.get("records")
            if isinstance(records, list) and records:
                first_record = records[0]
                if isinstance(first_record, dict):
                    metrics = first_record.get("metrics", {})
                    latency_ms = metrics.get("latency_ms")
                    if isinstance(latency_ms, (int, float)):
                        latency_seconds = float(latency_ms) / 1000.0

        st.session_state.sentry_incident = {
            "error_type": error_type,
            "raw": sentry_data,
        }
        st.session_state.galileo_trace = {
            "latency_seconds": latency_seconds,
            "raw": galileo_data,
        }
        st.success("Loaded sample incident data from Sentry and Galileo.")


def run_llm_911() -> None:
    """Run the real LLM 911 analysis using the helper in llm_investigator.

    This function is responsible for:
    - Checking that sample data is loaded.
    - Calling the LLM helper with the Sentry + Galileo JSON.
    - Storing the returned report string into session_state.report_text.
    """
    if st.session_state.sentry_incident is None or st.session_state.galileo_trace is None:
        st.warning("Sample incident not loaded yet. Click 'Load Sample Incident' first.")
        return

    sentry_incident = st.session_state.sentry_incident
    galileo_trace = st.session_state.galileo_trace
    broken_code = st.session_state.broken_code

    # Run the simple CodeRabbit-style review first and stash it in session_state.
    code_review_summary = run_code_review(
        code_snippet=broken_code,
        sentry_error=sentry_incident,
        galileo_trace=galileo_trace,
    )
    st.session_state.code_review_summary = code_review_summary

    # Call the LLM helper. It already handles its own errors and returns a
    # human-readable string, so we just place whatever comes back into the
    # report text area.
    report = run_llm_911_llm(
        sentry_incident=sentry_incident,
        galileo_trace=galileo_trace,
        broken_code=broken_code,
    )
    st.session_state.report_text = report


def provision_daytona_sandbox() -> None:
    """Provision a Daytona sandbox via the SDK and capture status in session state."""
    try:
        sandbox = create_daytona_sandbox()
    except Exception as exc:  # noqa: BLE001 - surface exact issue to user
        st.session_state.daytona_status = {"error": str(exc)}
        return

    sandbox_id = getattr(sandbox, "id", None)
    dashboard_url = getattr(
        sandbox,
        "url",
        f"https://app.daytona.io/workspaces/daytonaio/{sandbox_id}" if sandbox_id else DAYTONA_WORKSPACE_URL,
    )

    st.session_state.daytona_status = {
        "id": sandbox_id,
        "url": dashboard_url,
    }


def main() -> None:
    # Basic page configuration
    st.set_page_config(
        page_title="LLM 911  LLM Incident Responder",
        layout="centered",
    )

    # Ensure our session_state keys exist
    init_session_state()

    # Title
    st.title("LLM 911  LLM Incident Responder")

    st.write(
        "Use the buttons below to load a sample incident, run the LLM 911 analysis, "
        "and optionally spin up a Daytona sandbox for hands-on debugging."
    )

    # Layout: three buttons side by side
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Load Sample Incident"):
            load_sample_incident()

    with col2:
        if st.button("Run LLM 911"):
            run_llm_911()

    with col3:
        if st.button("Provision Daytona Sandbox"):
            provision_daytona_sandbox()

    # Area to show the final report
    st.subheader("Incident Report")
    st.text_area(
        label="Incident Report",
        key="report_text",  # bound directly to st.session_state["report_text"]
        height=200,
    )

    # Optional section to show the simulated CodeRabbit review.
    st.subheader("CodeRabbit-style Review")
    if st.session_state.code_review_summary:
        st.text(st.session_state.code_review_summary)
    else:
        st.text("Run LLM 911 to generate a CodeRabbit-style review of the code.")

    with st.expander("View related code"):
        code_to_show = st.session_state.get("broken_code") or "# broken_code.py not loaded yet. Click 'Load Sample Incident'."
        st.code(code_to_show, language="python")

    st.subheader("Daytona Sandbox")
    daytona_status = st.session_state.get("daytona_status", {})
    if daytona_status.get("error"):
        st.error(daytona_status["error"])
    elif daytona_status.get("id"):
        st.success(f"Sandbox ready: {daytona_status['id']}")
        sandbox_url = daytona_status.get("url") or DAYTONA_WORKSPACE_URL
        if hasattr(st, "link_button"):
            st.link_button("Open Sandbox in Daytona", sandbox_url)
        else:
            st.markdown(f"[Open Sandbox in Daytona]({sandbox_url})")
    else:
        st.info("No Daytona sandbox provisioned yet.")

    st.caption(
        "Use Daytona to apply the code fixes suggested by LLM 911 in a reproducible dev environment."
    )

    # This gives the user a reproducible dev workspace.
    # We are not opening a sandbox here, just giving the reproducible CLI command.
    st.subheader("🔧 Reproduce & Fix in Daytona")

    st.markdown("""
    **Want to debug this incident in a clean environment?**
    
    Use Daytona to spin up a reproducible development workspace with this codebase:
    
    ```bash
    # Install Daytona CLI
    # Windows: (Run in PowerShell as Administrator)
    md -Force "$Env:APPDATA\daytona"; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]'Tls,Tls11,Tls12'; Invoke-WebRequest -URI "https://download.daytona.io/cli/latest/daytona-windows-amd64.exe" -o $Env:APPDATA\daytona\daytona.exe; $env:Path += ";" + $Env:APPDATA + "\daytona"; [Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::User)
    
    # Create your sandbox
    daytona create https://github.com/arun3676/LLM-911.git
    ```
    
    🚀 **Benefits:**
    - Instant development environment with all dependencies
    - Apply LLM 911 fixes in a safe, isolated workspace
    - No local setup required - everything works in the cloud
    """)


if __name__ == "__main__":
    main()
