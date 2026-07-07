# AI DevOps Agent

An agent that investigates CI/CD pipeline failures — reads the log, finds the
root cause, and suggests a fix. Built in layers, starting from a single LLM
call and growing into a full agent loop with tool calling, RAG, and GitHub
integration.

## Why this exists
This one is built around the actual skills a DevOps/RCA workflow needs:

- Read logs
- Search related GitHub commits
- Search docs (RAG)
- Generate RCA
- Suggest a fix
- Summarize as a Jira-style ticket

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

