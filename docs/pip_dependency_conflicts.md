# Pip Dependency Conflicts

## ResolutionImpossible errors
Pip's resolver fails when two packages in requirements.txt require
incompatible versions of the same dependency (e.g. package A needs
numpy>=1.26 and you've pinned numpy==1.21). Pip will print exactly which
packages are in conflict and what version ranges they need — read this
carefully, it names the actual constraint.

## Fix strategies, in order of preference
1. Remove the overly-strict pin and let pip resolve to a compatible
   version automatically.
2. If you pinned a version for a reason (a known regression), check
   whether a newer patch version fixes that regression instead of
   pinning to an old major version.
3. Use `pip install --upgrade-strategy eager` to force all dependencies
   to their latest compatible versions.
4. As a last resort, use separate virtual environments for tools with
   truly incompatible dependency trees.

## Prevention
Pin only top-level dependencies you directly import; let pip resolve
transitive dependencies (numpy, urllib3, etc.) itself. Over-pinning
transitive deps is the most common cause of these conflicts.