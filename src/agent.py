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

Two robustness additions in this version:
1. Simple in-memory caching per tool call — if the model calls the same
   tool with the same arguments twice (it sometimes does), we return the
   cached result instead of burning another API call.
2. Retry with backoff on transient 503 (model overloaded) errors from
   Gemini's side — these are common on the free tier and not your bug.

Usage:
    python src/agent.py logs/pytest_failure.log --repo tarunvamsi/ai-devops-agent
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from skills.log_analysis import read_log
from skills.github_commits import search_github_commits
from rag.search_docs import search_docs

load_dotenv()

# Simple per-run cache, keyed by (tool_name, args) -> result.
# Prevents wasted duplicate calls when the model repeats itself.
_CACHE = {}
_AGENT_MODEL = "gemini-2.5-flash-lite" 


def tool_read_log(log_path: str) -> dict:
    """Reads a CI/build log file from disk and returns a structured root-cause analysis.

    Args:
        log_path: path to the log file, e.g. "logs/pytest_failure.log"
    """
    cache_key = ("tool_read_log", log_path)
    if cache_key in _CACHE:
        print(f"    [tool call] tool_read_log(log_path={log_path!r}) -> cached, skipping")
        return _CACHE[cache_key]

    print(f"    [tool call] tool_read_log(log_path={log_path!r})")
    with open(log_path, "r") as f:
        log_text = f.read()
    analysis = read_log(log_text, model=_AGENT_MODEL)
    result = analysis.model_dump()
    _CACHE[cache_key] = result
    return result


def tool_search_commits(repo: str, path_filter: str = "") -> dict:
    """Searches recent commits in a GitHub repo, optionally filtered to one file path.

    Args:
        repo: GitHub repo as "owner/repo", e.g. "tarunvamsi/ai-devops-agent"
        path_filter: only return commits touching this file path. Pass an empty
            string if you don't want to filter by path.
    """
    cache_key = ("tool_search_commits", repo, path_filter)
    if cache_key in _CACHE:
        print(f"    [tool call] tool_search_commits(repo={repo!r}, path_filter={path_filter!r}) -> cached, skipping")
        return _CACHE[cache_key]

    print(f"    [tool call] tool_search_commits(repo={repo!r}, path_filter={path_filter!r})")
    commits = search_github_commits(repo, path_filter=path_filter or None)
    result = {"commits": [c.model_dump() for c in commits]}
    _CACHE[cache_key] = result
    return result


def tool_search_docs(query: str) -> dict:
    """Searches internal documentation for known-issue patterns relevant to a query.
    Use this to check if the failure matches a known, previously-documented pattern
    (e.g. common pytest errors, pip conflicts, Docker OOM, JWT issues, timeouts).

    Args:
        query: a short natural-language description of the error or symptom,
            e.g. "AttributeError NoneType has no attribute get in JWT refresh"
    """
    cache_key = ("tool_search_docs", query)
    if cache_key in _CACHE:
        print(f"    [tool call] tool_search_docs(query={query!r}) -> cached, skipping")
        return _CACHE[cache_key]

    print(f"    [tool call] tool_search_docs(query={query!r})")
    chunks = search_docs(query, n_results=3)
    result = {"results": [c.model_dump() for c in chunks]}
    _CACHE[cache_key] = result
    return result


SYSTEM_INSTRUCTION = """You are an AI DevOps agent investigating a CI/CD pipeline failure.

You have three tools:
- tool_read_log: reads and analyzes a build log file, returns root cause + suggested fix
- tool_search_commits: searches recent GitHub commits, optionally filtered to a file path
- tool_search_docs: searches internal documentation for known-issue patterns matching
  the failure (e.g. common pytest errors, pip conflicts, Docker OOM, JWT issues, timeouts)

Your job, step by step:
1. Call tool_read_log EXACTLY ONCE on the given log file to find the root cause.
2. Call tool_search_docs EXACTLY ONCE with a short description of the error/symptom
   from the root cause, to check if this matches a documented known-issue pattern.
3. Look at the root cause. If it names a specific file (e.g. "app/auth.py"), call
   tool_search_commits ONCE with that file as path_filter. If no specific file is
   named, you may skip this step or search once with no path_filter.
4. Never call any tool with arguments you've already used. Each tool should be
   called at most once per investigation.
5. Once you have enough information, STOP calling tools and write a final report
   in this exact Markdown format:

## Root Cause
<from tool_read_log>

## Known Issue Match
<summarize the most relevant doc chunk from tool_search_docs, citing its source
filename, or say "No closely matching documented pattern found">

## Relevant Commits
<list commits that plausibly relate, or say "No clearly related commits found">

## Suggested Fix
<from tool_read_log, refined with doc and commit context if relevant>

## Confidence
<low / medium / high, with a one-sentence reason>
"""


def investigate(log_path: str, repo: str, model: str = "gemini-2.5-flash-lite", max_retries: int = 4) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        sys.exit(1)

    global _AGENT_MODEL
    _AGENT_MODEL = model

    client = genai.Client(api_key=api_key)

    prompt = f"Investigate the failure in log file '{log_path}'. The related GitHub repo is '{repo}'."

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[tool_read_log, tool_search_commits, tool_search_docs],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        maximum_remote_calls=10
                    ),
                ),
            )

            if response.text:
                return response.text

            # response.text was None — the model's final turn wasn't plain text.
            # Try to salvage any text parts directly, and otherwise report why.
            return _extract_text_or_explain(response)

        except genai_errors.ServerError as e:
            last_error = e
            wait = 2 ** attempt
            print(f"    [warning] Gemini server error (attempt {attempt}/{max_retries}): {e}")
            print(f"    Retrying in {wait}s...")
            time.sleep(wait)

    print(f"Failed after {max_retries} attempts. Last error: {last_error}", file=sys.stderr)
    sys.exit(1)


def _extract_text_or_explain(response) -> str:
    """Fallback for when response.text is None: pull any text parts we can find,
    or explain why the model didn't produce a final answer."""
    texts = []
    finish_reason = "unknown"
    try:
        for candidate in response.candidates:
            finish_reason = candidate.finish_reason
            for part in candidate.content.parts:
                if getattr(part, "text", None):
                    texts.append(part.text)
    except Exception:
        pass

    if texts:
        return "\n".join(texts)

    return (
        f"[No final text response from the model. finish_reason={finish_reason}.\n"
        f"This usually means the model stopped mid tool-call-sequence without writing "
        f"the final report, or hit an internal limit. Try re-running — this is often "
        f"transient, especially during a demand spike.]"
    )


def main():
    parser = argparse.ArgumentParser(description="Run the AI DevOps agent on a log file.")
    parser.add_argument("log_file", help="Path to the log file to investigate")
    parser.add_argument("--repo", required=True, help="GitHub repo as owner/repo")
    parser.add_argument("--model", default="gemini-2.5-flash-lite")
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"File not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Agent investigating {args.log_file} (repo: {args.repo})...\n")
    report = investigate(args.log_file, args.repo, model=args.model)
    print("\n" + report)


if __name__ == "__main__":
    main()