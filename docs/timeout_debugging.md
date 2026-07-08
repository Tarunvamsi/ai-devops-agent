# CI Timeout Failures

## Test/step exceeds pipeline timeout
When a test or build step is killed for exceeding a timeout (rather than
failing with an error), the process didn't crash — it stalled. Common
causes:
- An external network call (API, DB, queue) with no timeout configured,
  waiting indefinitely for a response that never comes
- A deadlock or lock contention issue, often in bulk/batch processing
  code, where two operations wait on each other
- Pagination or batch-processing logic with an off-by-one bug causing an
  infinite loop over the same data

## Debugging approach
Since the process is killed rather than erroring, the log rarely contains
a traceback. Look at the last successful log line before the stall — the
gap tells you which stage got stuck. Add explicit progress logging and
per-call timeouts (e.g. `requests.get(url, timeout=10)`) so a future
stall fails fast with a clear error instead of hanging until the CI
timeout kills it.