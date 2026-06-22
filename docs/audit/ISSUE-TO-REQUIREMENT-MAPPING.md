# MADO-queue Issue to Requirement Mapping

## 1. Purpose

This document maps upstream MADO-queue issues and pull requests into requirement, operation, UX, documentation, and governance categories.

The purpose is to avoid treating every issue as an immediate implementation task. Some issues should become requirements, some should become operational procedures, some should become governance rules, and some should remain observations until more evidence is available.

This is a fork-side audit note, not an upstream issue tracker replacement.

## 2. Mapping Categories

| Category | Meaning |
|---|---|
| Requirement | Business or system behavior needs clarification |
| Patch maintenance | Existing behavior likely needs a small fix or test |
| Stable operation | DB, logs, backup, restore, retention, deletion, or operations |
| UX / screen design | Visitor, staff, display, or operator experience |
| Documentation | Existing behavior or assumptions need clearer documentation |
| Governance | Decision scope, maintainer responsibility, versioning, or contribution process |
| Major-version proposal | Baseline-changing proposal that may need versioned planning |
| Observation | Useful finding, but not yet ready as requirement or implementation |

## 3. Mapping Table

| Upstream item | Title / topic | Primary category | Secondary category | Current audit interpretation | Suggested handling |
|---|---|---|---|---|---|
| #6 | Runtime timezone / JST / same-day filtering | Patch maintenance | Stable operation | Same-day behavior is operationally important and should be tested against JST assumptions | Keep as baseline bug/behavior verification; document test evidence |
| #14 | DB persistence / backup | Stable operation | Requirement | DB backup is not just implementation; it defines recoverability and operational responsibility | Treat as Stable Operation Phase 2 requirement before scripts |
| #16 | PATCH-equivalent maintainer judgment and version-up operation | Governance | Change classification | Central issue for deciding what maintainers can accept after v1.0.0 | Use Change Classification Model and Maintainer Checklist |
| #17 | Periodic log data deletion | Stable operation | Governance | Log deletion should not precede retention, backup, archive, and accountability decisions | Map to Stable Operation Phase 2; avoid immediate purge-only implementation |
| #18 | Developer experience improvement | Governance | Major-version proposal | Useful intent, but proposed scope includes structure, runtime, config, startup, dependencies, and docs | Split developer-only improvements from baseline-changing changes |
| #19 PR | Improve Developer Experience: project setup | Major-version proposal | Contribution process | The PR appears too broad for routine maintainer review and likely exceeds patch/minor scope | Do not treat as simple DX PR; require scope split and municipal explanation if pursued |
| to4kawa PR #9 | Flask screen & button inventory audit document | Documentation | UX / screen design | Fork-side audit inventory of actual Flask UI/API behavior | Merge into audit branch; use as evidence for UX and screen review |

## 4. Detailed Notes

### 4.1 #6 Runtime timezone / JST / same-day filtering

This topic affects daily reset, same-day query filters, and operational trust.

Mapping:

- Primary: Patch maintenance
- Secondary: Stable operation

Audit handling:

- Preserve evidence from UTC vs Asia/Tokyo verification
- Treat behavior as operationally significant, not just a technical date bug
- Add tests or documentation if upstream scope allows

### 4.2 #14 DB persistence / backup

This topic affects whether the system can recover after failure.

Mapping:

- Primary: Stable operation
- Secondary: Requirement

Audit handling:

- Define backup target
- Define timing
- Define restore procedure
- Define verification
- Avoid pretending that copying `numbers.db` alone is a complete operations policy

### 4.3 #16 PATCH-equivalent maintainer judgment

This topic affects how the project accepts post-v1.0.0 changes.

Mapping:

- Primary: Governance
- Secondary: Change classification

Audit handling:

- Use `CHANGE-CLASSIFICATION-MODEL.md`
- Define baseline-preserving changes
- Define major-version-level changes
- Keep non-engineer maintainer review capacity visible

### 4.4 #17 Periodic log deletion

This topic affects logs, DB size, auditability, and operational responsibility.

Mapping:

- Primary: Stable operation
- Secondary: Governance

Audit handling:

- Do not start from purge implementation
- Start from retention policy
- Decide archive-before-delete
- Decide backup-before-delete
- Clarify who owns deletion operation

### 4.5 #18 Developer experience improvement

This topic includes legitimate contributor experience concerns.

However, the proposed content may go beyond DX and into structural change.

Mapping:

- Primary: Governance
- Secondary: Major-version proposal

Audit handling:

- Separate local developer convenience from production-affecting changes
- Avoid bundling project layout, config format, Python baseline, dependency locking, and startup commands
- Ask whether each change preserves `v1.0.0` baseline

### 4.6 #19 Improve Developer Experience PR

This PR is related to #18.

Mapping:

- Primary: Major-version proposal
- Secondary: Contribution process

Audit handling:

- Do not review only as a code diff
- Identify maintainer decision burden
- Treat as too broad unless split
- Require operational and municipal explanation for baseline-changing pieces

## 5. Conversion Rules

### 5.1 Issue to Requirement

Convert an issue to a requirement when:

- the expected behavior is unclear
- multiple implementation options exist
- operational responsibility is unclear
- the issue affects DB, logs, backup, restore, or screen workflow
- the issue requires business rule confirmation

### 5.2 Issue to Patch

Convert an issue to patch maintenance when:

- the current behavior is clearly wrong
- the expected behavior is already documented
- the change preserves baseline
- the test scope is small
- DB/schema/startup/operations do not change

### 5.3 Issue to Governance

Convert an issue to governance when:

- it affects who can decide
- it affects contribution acceptance
- it affects versioning
- it affects maintainer review capacity
- it affects municipal explanation or internal review

### 5.4 Issue to Observation

Keep an issue as observation when:

- evidence is incomplete
- actual field behavior is unknown
- code suggests a possibility but not a confirmed problem
- manual check is required

## 6. Suggested Workflow

For each new upstream issue:

1. Read the issue body and comments.
2. Identify the affected baseline area.
3. Map to one primary category and optional secondary categories.
4. Decide whether it is implementation-ready.
5. If not implementation-ready, describe what must be clarified first.
6. Record fork-side audit interpretation here.
7. Only comment upstream when the comment helps maintainers decide.

## 7. Open Mapping Items

The following should be updated as more issues appear:

- screen-specific UX issues
- printer operation issues
- backup/restore issues
- release/versioning issues
- contributor onboarding issues
- documentation mismatches

## 8. Summary

The main audit principle is:

```text
Do not turn every issue directly into code.
First map it to requirement, operation, UX, documentation, or governance.
Then decide whether implementation is appropriate.
```
