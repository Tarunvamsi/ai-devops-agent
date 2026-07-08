# Docker Build Failures

## JavaScript heap out of memory during build
"FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out
of memory" during `npm run build` inside a Docker container almost always
means the container's memory limit is lower than what the bundler
(webpack, vite, etc.) needs for a production build.

Fixes:
- Increase Docker's memory limit (Docker Desktop: Settings > Resources)
- Or explicitly raise Node's heap limit in the build script:
  `NODE_OPTIONS=--max-old-space-size=4096 npm run build`
- For CI runners with fixed memory (e.g. GitHub Actions' 7GB default),
  reducing the build's memory footprint (code-splitting, disabling
  source maps in prod) is often more reliable than trying to raise
  limits further.

## Exit code 134
Exit code 134 corresponds to SIGABRT, frequently seen alongside OOM
kills or Node/V8 heap exhaustion — treat it as a memory problem first
before investigating application logic.