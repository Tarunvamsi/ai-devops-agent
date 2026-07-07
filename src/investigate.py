"""
Step 1 — run two skills manually, side by side.

This is deliberately NOT an agent yet. You (the human) decide which
skills to call and in what order. In Step 2, an LLM planner will make
that decision instead.

Usage:
    python src/investigate.py logs/pytest_failure.log \
        --repo your-username/your-repo \
        --path app/auth.py
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from skills.log_analysis import read_log
from skills.github_commits import search_github_commits, format_commits_for_report

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Investigate a CI failure: log RCA + recent commits.")
    parser.add_argument("log_file", help="Path to the log file to analyze")
    parser.add_argument("--repo", required=True, help="GitHub repo as owner/repo")
    parser.add_argument("--path", default=None, help="Filter commits to this file path (optional)")
    parser.add_argument("--max-commits", type=int, default=5)
    parser.add_argument("--model", default="gemini-2.5-flash")
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"File not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.log_file, "r") as f:
        log_text = f.read()

    print(f"[1/2] Reading log: {args.log_file}")
    analysis = read_log(log_text, model=args.model)
    print(json.dumps(analysis.model_dump(), indent=2))

    print(f"\n[2/2] Searching recent commits in {args.repo}"
          f"{f' touching {args.path}' if args.path else ''}...")
    commits = search_github_commits(args.repo, path_filter=args.path, max_commits=args.max_commits)
    print(format_commits_for_report(commits))

    print("\n--- Correlate manually for now ---")
    print("Does a recent commit's message/timing line up with the root cause above?")
    print("(In Step 2, the agent will do this correlation itself.)")


if __name__ == "__main__":
    main()