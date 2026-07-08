# JWT / Auth Token Issues

## Refresh token returns None payload
If decoding a JWT returns None instead of raising, the most common causes
are:
- The token has expired and the decode call is configured to return None
  on expiry instead of raising `ExpiredSignatureError`
- The signing key used to verify the token doesn't match the key used to
  issue it (common after a key rotation, or when test fixtures use a
  hardcoded token signed with a different secret than the app's current
  `SECRET_KEY`)
- The token was tampered with or malformed and signature verification
  silently failed

## Best practice
Never let a failed decode fall through as `None` used in later logic.
Raise a specific `InvalidTokenError` / `TokenExpiredError` immediately at
the decode site, and let the API layer translate that into a 401, not a
500. A 500 on auth failure is itself a signal the error handling is
incomplete.

## Testing tokens
When tests use a hardcoded "VALID_TOKEN" constant, check it's regenerated
whenever the app's secret key or token expiry logic changes — stale test
fixtures are a common source of this exact failure.