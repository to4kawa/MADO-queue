# MADO-queue Upstream Comment Log

## 1. Purpose

This document records upstream comments made from the fork-side audit perspective.

The purpose is to preserve why a comment was made, what decision problem it addressed, and how it relates to the audit model.

This is not a substitute for GitHub issue history. The upstream issue or pull request remains the authoritative public record. This file is an internal audit log for reasoning and traceability.

## 2. Commenting Policy

Upstream comments should be used only when they help maintainers or contributors decide.

Avoid comments that only express preference, repeat the issue body, or turn the discussion into a person-focused debate.

Prefer comments that:

- clarify decision scope
- identify operational or municipal implications
- suggest splitting oversized proposals
- connect implementation proposals to requirements
- help non-engineer maintainers decide safely
- preserve respect for contributors while identifying risk

## 3. Comment Log Format

Use this format.

```md
## YYYY-MM-DD: Upstream item #N

### Upstream item

- Repository: Memuro-Town/MADO-queue
- Issue / PR: #N
- Topic:

### Comment purpose

Why the comment was made.

### Main message

Short summary of the comment.

### Audit classification

- Requirement / Stable operation / UX / Documentation / Governance / Major-version proposal / Contribution process

### Expected maintainer effect

What decision the comment is intended to support.

### Risk avoided

What risk the comment helps avoid.

### Follow-up

What should be watched next.
```

## 4. Logged Comments

## 2026-06-22: Upstream issue #18

### Upstream item

- Repository: Memuro-Town/MADO-queue
- Issue: #18
- Topic: Developer experience improvement and related PR #19

### Comment purpose

The comment was made to help maintainers recognize that the related PR was not only a developer-experience improvement.

The proposal included project structure, configuration format, startup commands, Python version assumptions, dependency management, Dev Container setup, and documentation updates.

### Main message

The comment stated that the proposal may be technically useful, but the current scope looks closer to a major-version-level structural change than a simple developer-experience improvement.

It emphasized that MADO-queue is municipal OSS and that maintainers may not be engineers. Therefore, changes of this scope should provide municipal explanation material, operational impact, and a distinction between developer convenience and production-impacting changes.

### Audit classification

- Governance
- Major-version proposal
- Contribution process
- Maintainer decision support

### Expected maintainer effect

The comment is intended to give maintainers a safe reason not to merge the related PR as-is.

It does not require maintainers to perform a detailed code review. Instead, it reframes the decision as:

```text
Is this change within maintainer judgment, or does it require broader version and municipal operation discussion?
```

### Risk avoided

- baseline drift from `v1.0.0`
- oversized PR acceptance
- non-engineer maintainer being forced into technical structure review
- developer-experience rationale hiding production-impacting changes
- municipal explanation material being skipped

### Follow-up

Watch whether #18 / #19 is split into smaller issues or PRs.

If the proposal continues, evaluate each part separately:

- local development convenience
- project layout
- configuration format
- runtime version
- dependency management
- production startup
- documentation update

## 2026-06-22: Upstream issue #17

### Upstream item

- Repository: Memuro-Town/MADO-queue
- Issue: #17
- Topic: Periodic log data deletion

### Comment purpose

The comment was prepared to reframe log deletion as part of stable operation Phase 2, rather than as an isolated purge implementation.

### Main message

The comment states that log deletion is useful as a capacity measure, but municipal operation should first decide:

- DB backup policy
- restore procedure
- log retention period
- audit and inquiry needs
- archive-before-delete policy
- operational responsibility for deletion

It connects #17 to #14 and suggests that DB backup, retention, restore, and deletion should be considered together.

### Audit classification

- Stable operation
- Requirement clarification
- Governance
- Operational responsibility

### Expected maintainer effect

The intended effect is to prevent maintainers from accepting a purge implementation before retention and backup requirements are clear.

It provides a safe way to say:

```text
This issue is valid, but implementation should wait until stable-operation requirements are clarified.
```

### Risk avoided

- deleting logs before knowing whether they are needed
- losing evidence for inquiry, troubleshooting, audit, or security review
- treating log deletion as a simple storage cleanup problem
- separating log deletion from DB backup and restore policy

### Follow-up

Watch whether #17 becomes:

- immediate purge implementation
- stable operation requirement discussion
- backup/restore/log-retention documentation
- archive-before-delete design

The preferred audit direction is to keep it under Stable Operation Phase 2.

## 5. Future Comment Candidates

Potential future upstream comments may be useful for:

- #16: PATCH-equivalent maintainer decision scope
- #14: DB backup and restore requirements
- PR #19: only if PR-side comment becomes necessary as a pointer to #18
- Any future UI/UX issue that requires separating observation from implementation
- Any future PR that bundles multiple decision categories

## 6. Non-goals

This log should not be used to:

- build a case against a contributor personally
- record private speculation
- duplicate the full upstream discussion
- convert every audit thought into upstream commentary

The goal is to keep public comments purposeful, limited, and decision-oriented.

## 7. Summary

Upstream comments should be rare, precise, and useful.

The fork-side audit branch can hold the heavier reasoning. Upstream should receive only the part that helps maintainers and contributors make a safer decision.
