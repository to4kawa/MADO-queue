# Issue #11 versioning and release process audit note

Source issue: https://github.com/Memuro-Town/MADO-queue/issues/11

Recorded in fork for audit and discussion traceability.

## Context

Issue #11 proposes that MADO queue should use GitHub Tags and GitHub Releases to identify versions such as `v1.0.0`.

The original issue is directionally correct, but it assumes the reader already understands common OSS release practices. For non-engineer maintainers or civic-tech stakeholders, the proposal needs to be decomposed into concrete operational layers.

The practical scope is not only "use version numbers". It spans three areas:

1. Code-change classification
2. Contribution process
3. Maintainer release process

## Recommendation

Start with a lightweight release process:

- Select the current stable state as the first release.
- Create a Git tag such as `v1.0.0` for that stable state.
- Create a GitHub Release for the same version.
- Record what changed, what was fixed, and any deployment notes.

For later changes, increment the version based on the size and compatibility impact of the change.

## Versioning model

Use a SemVer-like format:

```text
vMAJOR.MINOR.PATCH
```

Examples:

```text
v1.0.0
v1.0.1
v1.1.0
v2.0.0
```

### PATCH

Use PATCH for changes that do not change existing usage patterns.

Examples:

- Bug fixes
- Documentation fixes
- Docker or startup procedure fixes
- Small display fixes
- Safe fixes that do not break existing behavior

Example:

```text
v1.0.0 -> v1.0.1
```

### MINOR

Use MINOR for compatible feature additions.

Examples:

- New screen
- New setting
- New API
- Feature addition that preserves DB compatibility

Example:

```text
v1.0.1 -> v1.1.0
```

### MAJOR

Use MAJOR for changes that may affect existing deployments or operational compatibility.

Examples:

- Breaking DB schema change
- Breaking API response change
- Configuration file format change
- Major change in operation procedure
- Change that prevents direct upgrade from an older version

Example:

```text
v1.1.0 -> v2.0.0
```

## Concrete example: Issue #6

Issue #6 discussed the risk that runtime timezone differences could affect same-day queue filtering.

A lightweight fix that only makes `TZ=Asia/Tokyo` explicit in Docker and non-Docker startup documentation should be treated as PATCH:

```text
v1.0.0 -> v1.0.1
```

Reason:

- It does not add a new application feature.
- It does not change the DB schema.
- It does not change API responses.
- It clarifies and stabilizes the existing runtime assumption.

If the application later adds a new configurable business-date timezone setting, that would be MINOR because it adds a new setting and user-visible configuration surface:

```text
v1.0.1 -> v1.1.0
```

If a future change alters stored timestamp semantics, DB schema, or API response compatibility, it may require MAJOR consideration:

```text
v1.1.0 -> v2.0.0
```

## Relationship with CONTRIBUTING.md

The current `CONTRIBUTING.md` already defines the contribution workflow:

- Start with an Issue.
- Do not push directly to `main`.
- Create a branch that includes the Issue number.
- Submit changes through a PR.
- Link the PR to the Issue where appropriate.
- If AI assistance is used, document the tool, scope, and human verification.

The versioning proposal should align with that existing process.

Recommended release flow:

```text
1. Create an Issue.
2. Create a branch that includes the Issue number.
3. Make the change through a PR.
4. Mention the related Issue in the PR body.
5. Review and merge the PR into main.
6. After main is stable, create a Git tag such as v1.0.1.
7. Create a GitHub Release for that tag.
8. Write the release notes.
```

## GitHub Release note template

A minimal release note template is enough at first:

```markdown
## Added
- Added features

## Changed
- Changed behavior, configuration, or procedures

## Fixed
- Fixed bugs

## Notes
- Deployment or operational notes
```

For AI-assisted PRs, the PR body should keep the `AI Assistance` details required by `CONTRIBUTING.md`.

The Release note may additionally include verification notes when they matter for deployment or later audits.

Example:

```markdown
## Fixed
- Addressed #6 by making the runtime timezone assumption clearer.

## Changed
- Added `TZ=Asia/Tokyo` to Docker startup configuration.
- Added `TZ=Asia/Tokyo` to non-Docker startup instructions.

## Notes
- Application-side timestamp logic was not changed.
- This release treats runtime localtime as the business-date basis.
```

## Issue-reporting fields

Issue templates may eventually include:

```text
Confirmed version:
Confirmed commit:
```

These fields should not be mandatory at first, because some users may not know the exact version. They should be treated as "fill in if known" fields.

## Summary

Issue #11 is best understood as a proposal for three connected practices:

1. Classify code changes by compatibility impact.
2. Keep contribution work aligned with the existing Issue / branch / PR workflow.
3. Let maintainers mark stable points by creating Git tags and GitHub Releases.

For MADO queue, the lowest-friction starting point is:

- Tag the current stable state as `v1.0.0`.
- Use GitHub Releases to explain that version.
- Use PATCH / MINOR / MAJOR only as a lightweight judgment rule.
- Keep Release notes practical and deployment-oriented.

This keeps the process understandable for non-engineers while still making bug reports, deployment support, and future audits easier to trace.
