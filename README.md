# AI DevOps Agent

An agent that investigates CI/CD pipeline failures — reads the log, finds the
root cause, and suggests a fix. Built in layers, starting from a single LLM
call and growing into a full agent loop with tool calling, RAG, and GitHub
integration.

## Why this exists

Most "AI agent" side projects are just chatbots with extra steps. This one
is built around the actual skills a DevOps/RCA workflow needs:

- Read logs
- Search related GitHub commits
- Search docs (RAG)
- Generate RCA
- Suggest a fix
- Summarize as a Jira-style ticket

## Progress

- [x] **Step 0** — single LLM call: log in, structured RCA out. No framework.
- [ ] Step 1 — turn it into a callable "skill" + add GitHub commit search
- [ ] Step 2 — real agent loop (planner/executor) deciding which skills to call
- [ ] Step 3 — RAG over a small doc set
- [ ] Step 4 — FastAPI wrapper + SQLite run logs + Jira-summary skill

## Step 0 — Setup

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
```

## Step 0 — Run it

```bash
python src/analyze_log.py logs/pytest_failure.log
python src/analyze_log.py logs/pip_conflict.log
python src/analyze_log.py logs/docker_oom.log
python src/analyze_log.py logs/missing_env_var.log
python src/analyze_log.py logs/timeout_failure.log
```

Each run prints structured JSON:

```json
{
  "failure_type": "test_failure",
  "root_cause": "...",
  "evidence": ["..."],
  "suggested_fix": "...",
  "confidence": 0.9
}
```

## Sample logs

`logs/` contains 5 synthetic but realistic CI failure logs, standing in for
Jenkins output until a real CI is wired up: a pytest failure, a pip
dependency conflict, a Docker OOM, a missing env var, and a test timeout.
Each has a clear, single terminal error, so you can eyeball whether the
model's RCA is actually correct — this is your test set for prompt quality.

## Next steps

See the roadmap above. Step 1 turns `analyze_log.py` into a tool the LLM can
call, and adds a second skill for searching GitHub commits.
