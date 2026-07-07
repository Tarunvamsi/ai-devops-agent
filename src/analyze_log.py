"""
the core loop, with no framework, no agent, no RAG.

    log_file  ->  LLM call with a good prompt  ->  structured LogAnalysis

Usage:
    python src/analyze_log.py logs/pytest_failure.log
    python src/analyze_log.py logs/pip_conflict.log --model gemini-2.5-flash
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from google import genai

from models import LogAnalysis

load_dotenv()

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


def analyze_log(log_text: str, model: str = "gemini-2.5-flash") -> LogAnalysis:
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


def main():
    parser = argparse.ArgumentParser(description="Analyze a CI/build failure log with an LLM.")
    parser.add_argument("log_file", help="Path to the log file to analyze")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use")
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"File not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.log_file, "r") as f:
        log_text = f.read()

    print(f"Analyzing {args.log_file} with {args.model}...\n")
    result = analyze_log(log_text, model=args.model)

    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()