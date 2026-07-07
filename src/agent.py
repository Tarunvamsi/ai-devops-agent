"""
Step 2 — the actual agent loop.

Instead of YOU calling read_log() then search_github_commits() in a
fixed order (Step 1), the LLM now decides which tools to call, with
what arguments, and in what order — based on what it finds.

This uses Gemini's automatic function calling: pass plain Python
functions as `tools`, and the SDK handles the call/respond loop for
you. Each tool function below has a print() at the top so you can
watch, in your terminal, exactly which skill the agent chose to
invoke and with what arguments -- this is your window into the
"agent loop" instead of an opaque black box.

Usage:
    python src/agent.py logs/pytest_failure.log --repo tarunvamsi/ai-devops-agent
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from skills.log_analysis import read_log
from skills.github_commits import search_github_commits

load_dotenv()


def tool_read_log(log_path: str) -> dict:
    """Reads a CI/build log file from disk and returns a structured root-cause analysis.

    Args:
        log_path: path to the log file, e.g. "logs/pytest_failure.log"
    """
    print(f"    [tool call] tool_read_log(log_path={log_path!r})")
    with open(log_path, "r") as f:
        log_text = f.read()
    analysis = read_log(log_text)
    return analysis.model_dump()


def tool_search_commits(repo: str, path_filter: str = "") -> dict:
    """Searches recent commits in a GitHub repo, optionally filtered to one file path.

    Args:
        repo: GitHub repo as "owner/repo", e.g. "tarunvamsi/ai-devops-agent"
        path_filter: only return commits touching this file path. Pass an empty
            string if you don't want to filter by path.
    """
    print(f"    [tool call] tool_search_commits(repo={repo!r}, path_filter={path_filter!r})")
    commits = search_github_commits(repo, path_filter=path_filter or None)
    return {"commits": [c.model_dump() for c in commits]}


SYSTEM_INSTRUCTION = """You are an AI DevOps agent investigating a CI/CD pipeline failure.

You have two tools:
- tool_read_log: reads and analyzes a build log file, returns root cause + suggested fix
- tool_search_commits: searches recent GitHub commits, optionally filtered to a file path

Your job, step by step:
1. Call tool_read_log on the given log file to find the root cause.
2. Look at the root cause. If it names a specific file (e.g. "app/auth.py"), call
   tool_search_commits with that file as path_filter, to see if a recent commit
   touching that exact file might explain the failure. If no specific file is
   named, you may skip this step or search with no path_filter.
3. Do not call the same tool with the same arguments twice.
4. Once you have enough information, STOP calling tools and write a final report
   in this exact Markdown format:

## Root Cause
<from tool_read_log>

## Relevant Commits
<list commits that plausibly relate, or say "No clearly related commits found">

## Suggested Fix
<from tool_read_log, refined with commit context if relevant>

## Confidence
<low / medium / high, with a one-sentence reason>
"""


def investigate(log_path: str, repo: str, model: str = "gemini-2.5-flash") -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    prompt = f"Investigate the failure in log file '{log_path}'. The related GitHub repo is '{repo}'."

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[tool_read_log, tool_search_commits],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=6
            ),
        ),
    )
    return response.text


def main():
    parser = argparse.ArgumentParser(description="Run the AI DevOps agent on a log file.")
    parser.add_argument("log_file", help="Path to the log file to investigate")
    parser.add_argument("--repo", required=True, help="GitHub repo as owner/repo")
    parser.add_argument("--model", default="gemini-2.5-flash")
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"File not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Agent investigating {args.log_file} (repo: {args.repo})...\n")
    report = investigate(args.log_file, args.repo, model=args.model)
    print("\n" + report)


if __name__ == "__main__":
    main()