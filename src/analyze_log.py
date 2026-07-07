"""
Step 0 CLI — now a thin wrapper around the `read_log` skill
(src/skills/log_analysis.py).

Usage:
    python src/analyze_log.py logs/pytest_failure.log
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from skills.log_analysis import read_log

load_dotenv()


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
    result = read_log(log_text, model=args.model)

    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()