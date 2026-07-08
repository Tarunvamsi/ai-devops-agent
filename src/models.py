"""
Data models for the AI DevOps Agent.

Step 0 goal: force the LLM to return STRUCTURED output, not a
free-text paragraph. This is the single highest-leverage thing
you can do in a project like this — structured output is what
lets "Skill 4: Generate RCA" and "Skill 5: Suggest Fix" plug
into each other later without you parsing prose with regex.
"""

from pydantic import BaseModel, Field
from typing import List


class LogAnalysis(BaseModel):
    """Structured result of analyzing a single CI/build log."""

    failure_type: str = Field(
        description=(
            "Short category of the failure, e.g. 'test_failure', "
            "'dependency_conflict', 'out_of_memory', 'missing_env_var', "
            "'timeout', 'lint_error', 'unknown'."
        )
    )
    root_cause: str = Field(
        description="A precise, technical explanation of WHY the pipeline failed. "
        "Reference the exact error, file, or line if visible in the log."
    )
    evidence: List[str] = Field(
        description="1-4 short direct excerpts from the log that support the root cause."
    )
    suggested_fix: str = Field(
        description="A concrete, actionable fix. If it's a code change, describe it "
        "precisely enough that a developer could apply it without re-reading the log."
    )
    confidence: float = Field(
        description="Confidence in this analysis, from 0.0 to 1.0.", ge=0.0, le=1.0
    )


class CommitInfo(BaseModel):
    """A single GitHub commit, trimmed to what's useful for RCA."""

    sha: str = Field(description="Short commit SHA (7 chars)")
    author: str
    message: str = Field(description="First line of the commit message")
    date: str = Field(description="ISO 8601 commit timestamp")
    url: str = Field(description="Link to the commit on GitHub")


class DocChunk(BaseModel):
    """A retrieved chunk of documentation from the RAG index."""

    text: str = Field(description="The doc chunk content")
    source: str = Field(description="Filename the chunk came from")
    score: float = Field(description="Distance score (lower = more relevant)")