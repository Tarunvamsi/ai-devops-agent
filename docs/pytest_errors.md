# Common Pytest / Test Failures

## AssertionError on status codes
When a test asserts `response.status_code == 200` but gets 500, the real
bug is almost never in the test — it's an unhandled exception in the
application code that FastAPI/Flask converted into a 500. Always check
the captured stdout/stderr in the pytest output for the actual traceback;
it's usually printed right below the assertion failure.

## NoneType has no attribute 'get'
This is one of the most common Python runtime errors. It means a function
expected a dict-like object but received `None`. Common causes:
- A JWT decode/verify call failed silently and returned None instead of
  raising
- A database query (`.get()`, `.first()`) returned no row
- A dict lookup with `.get()` on a missing key returned None, and that
  None was then used as if it were itself a dict

Fix pattern: add an explicit None-check immediately after the call that
produces the value, and raise a clear, typed exception (e.g.
`AuthenticationError`) instead of letting the AttributeError propagate.

## Flaky tests due to shared state
If a test passes in isolation but fails in the full suite, suspect shared
global state (module-level variables, unclosed DB sessions, or test
fixtures with the wrong scope).