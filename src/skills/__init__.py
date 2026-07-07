"""
Skills package.

Each skill is a plain Python function with a clean, typed signature —
no framework magic. This is deliberate: in Step 2, when we wire an
agent loop, each of these becomes a "tool" the LLM can call. Keeping
them as normal functions now means Step 2 is just registration, not
a rewrite.
"""