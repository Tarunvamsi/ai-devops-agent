"""
Skill: read_log

Analyzes a CI/build failure log and returns a structured root-cause
analysis. This is the exact logic from Step 0, just relocated so it
has a clean importable function signature — this is what makes it a
"skill" instead of a script.
"""

import os
import sys

from google import genai

from models import LogAnalysis

SYSTEM_PROMPT = """You are a senior DevOps / SRE engineer performing Root Cause \
Analysis on a CI/CD pipeline failure log.

Rules:
- Base your analysis ONLY on evidence present in the log. Do not invent stack traces \
or files that are not shown.
- Be specific: name the exact library, test, file, or line if it appears in the log.
- If multiple issues appear, focus on the one that actually caused the pipeline \
to fail (the terminal error), not incidental warnings.
- The suggested_fix must be concrete and actionable — not "check your configuration" \
but "pin numpy to >=1.26.0 in requirements.txt" or equivalent.
- If the log is ambiguous or you're not sure, say so honestly in root_cause and \
lower your confidence score accordingly. Do not bluff.
"""


def read_log(log_text: str, model: str = "gemini-2.5-flash") -> LogAnalysis:
    """
    Skill: analyze a raw CI log and return a structured LogAnalysis.

    Args:
        log_text: full text content of the log file
        model: Gemini model name

    Returns:
        LogAnalysis (see models.py)
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=f"{SYSTEM_PROMPT}\n\nAnalyze this CI pipeline log and return the RCA:\n\n{log_text}",
        config={
            "response_mime_type": "application/json",
            "response_schema": LogAnalysis,
        },
    )

    return response.parsed