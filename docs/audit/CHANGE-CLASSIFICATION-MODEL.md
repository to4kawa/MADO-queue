# MADO-queue Change Classification Model

## 1. Purpose

This document defines a fork-side audit model for classifying proposed changes to MADO-queue.

The goal is to help reviewers, maintainers, and external contributors distinguish between small maintenance changes, baseline-preserving patch changes, stable-operation requirements, major-version-level structural changes, and municipal governance decisions.

This document is not an upstream policy by itself. It is a working note that may later inform `GOVERNANCE.md`, `CONTRIBUTING.md`, release policy, or issue templates.

## 2. Baseline Principle

The current reference point is `v1.0.0`.

A proposed change should first be evaluated against the `v1.0.0` baseline:

1. Does it preserve documented behavior?
2. Does it preserve documented startup commands?
3. Does it preserve documented DB location and schema?
4. Does it preserve screen roles and workflows?
5. Does it preserve the lightweight Docker Compose operating model?
6. Does it preserve reception-network independence and no-resident-personal-information assumptions?

If the answer is unclear, the change should not be treated as a simple patch until clarified.

## 3. Classification Overview

| Class | Meaning | Typical reviewer | Upstream handling |
|---|---|---|---|
| Documentation correction | Clarifies or fixes existing text | Maintainer | Can be small PR |
| Audit/documentation note | Records external review or analysis | Fork-side reviewer | Keep in fork unless accepted upstream |
| Patch-level maintenance | Fixes behavior without changing baseline | Maintainer + tester | Small PR after Issue |
| Minor feature / enhancement | Adds limited capability without changing core operation | Maintainer + operator | Issue discussion first |
| Stable operation Phase 2 | Affects DB, logs, backup, restore, retention, or operation | Maintainer + municipal/operator review | Requirements before implementation |
| Major-version-level change | Changes structure, startup, config, persistence, or baseline assumptions | Maintainer + municipal decision | Proposal first, likely versioned |
| Governance / contribution process | Affects how decisions and contributions are handled | Maintainer + project owner | Policy/documentation discussion |
| Out-of-scope / not planned | Does not fit current package or operating model | Maintainer | Close or defer with reason |

## 4. Documentation Correction

### Definition

A documentation correction fixes or clarifies existing documented behavior without changing code or operation.

### Examples

- typo correction
- broken link fix
- command clarification when the command already reflects actual behavior
- adding explanation for an already-existing screen
- correcting terminology while preserving meaning

### Review Requirements

- Confirm that no production behavior is changed
- Confirm that the new text does not introduce unsupported claims
- Confirm that the change is understandable to non-engineer readers when relevant

## 5. Audit / Documentation Note

### Definition

An audit or documentation note records external observations, analysis, checklists, inventories, or future proposal material.

### Examples

- baseline audit note
- UX observation model
- screen design baseline
- Flask screen/button inventory
- operational risk register
- change classification model

### Review Requirements

- Keep the note clearly marked as fork-side audit material unless upstream acceptance is intended
- Separate facts from inferences
- Avoid presenting audit interpretation as upstream policy
- Avoid production code changes in the same PR

## 6. Patch-level Maintenance

### Definition

A patch-level maintenance change fixes a bug or clarifies behavior while preserving the `v1.0.0` baseline.

### Examples

- same-day filtering bug fix that preserves documented daily operation
- timezone handling fix that preserves JST business behavior
- small error handling fix
- dependency patch update that does not change supported runtime assumptions
- test addition for existing behavior

### Review Requirements

A patch-level change should explain:

- the bug or ambiguity
- the current behavior
- the expected behavior
- the impact on existing operation
- how it was tested
- whether DB schema, startup, API, logs, or screens change

If DB schema, startup command, or documented operating model changes, it is probably not patch-level.

## 7. Minor Feature / Enhancement

### Definition

A minor feature or enhancement adds limited capability without changing the fundamental operating model.

### Examples

- adding a small display option
- improving existing documentation for an optional workflow
- adding a non-breaking operator note
- adding a new optional test helper

### Review Requirements

A minor enhancement should explain:

- who benefits
- whether the current workflow changes
- whether existing screens change
- whether DB/log behavior changes
- whether the feature is optional
- whether non-engineer maintainers can verify it

## 8. Stable Operation Phase 2

### Definition

Stable Operation Phase 2 changes affect long-term operation, including DB persistence, backups, restore procedures, log retention, deletion, and operational responsibility.

### Examples

- DB backup script
- restore procedure
- log retention policy
- log export or archive
- automatic log deletion
- VACUUM scheduling
- operations manual
- production data location changes

### Review Requirements

Implementation should not come first.

Before implementation, the project should clarify:

- what data must be protected
- what logs must be retained
- how long records should remain
- whether logs should be archived before deletion
- how backup and restore are performed
- who is responsible for running and checking the procedure
- whether municipal internal rules apply

## 9. Major-version-level Change

### Definition

A major-version-level change changes the structure, runtime assumptions, data handling, configuration model, startup model, or operational baseline.

### Examples

- moving `app.py` and related files into a new `src/` package if startup commands change
- changing configuration file format
- changing production WSGI target
- changing required Python baseline
- changing persistence model
- changing DB schema in a non-backward-compatible way
- making external infrastructure mandatory
- changing Docker Compose assumptions
- changing how logs are retained or deleted by default

### Review Requirements

A major-version-level change should not be reviewed only as a code improvement.

It should explain:

- why the change is needed now
- why smaller changes are insufficient
- operational impact
- migration path
- rollback path
- documentation changes
- maintainer review burden
- municipal explanation material
- whether a version bump or release plan is needed

## 10. Governance / Contribution Process Change

### Definition

A governance or contribution process change affects how the project accepts contributions, reviews issues, classifies changes, documents AI assistance, or decides version-level scope.

### Examples

- contribution checklist update
- pull request template update
- AI-assisted contribution disclosure requirements
- maintainer decision checklist
- release/version policy
- issue classification labels
- upstream comment policy

### Review Requirements

These changes should be evaluated for:

- clarity for non-engineer maintainers
- clarity for external contributors
- consistency with existing `CONTRIBUTING.md`
- whether the change reduces or increases maintainer burden
- whether it helps avoid oversized PRs

## 11. Out-of-scope / Not Planned

### Definition

A proposal may be out of scope when it conflicts with the documented lightweight municipal package model or depends on assumptions not yet accepted by the project.

### Examples

- mandatory cloud service integration
- large SaaS-style architecture change
- features belonging to future `hub`, `form`, `care`, or `move` packages
- changes requiring municipal process redesign without prior agreement

### Review Requirements

When closing or deferring, explain:

- why it is outside the current package scope
- what would need to be true before reconsidering
- whether it belongs to another package, future phase, or separate proposal

## 12. Classification Checklist

For each issue or PR, answer:

1. Is this documentation-only?
2. Does it change production code?
3. Does it change startup commands?
4. Does it change DB schema or data location?
5. Does it change logging, retention, deletion, or backup behavior?
6. Does it change screen workflow?
7. Does it require a new operational procedure?
8. Can a non-engineer maintainer review the effect?
9. Does it require municipal explanation or internal decision?
10. Should it be split into smaller changes?

## 13. Current Use Cases

### 13.1 PATCH-equivalent discussion

Use this model when discussing what can be handled as maintainer-level PATCH changes after `v1.0.0`.

### 13.2 Developer-experience proposals

Use this model when a DX proposal also changes project structure, startup, runtime version, configuration, or production assumptions.

### 13.3 Stable operation proposals

Use this model when a proposal involves DB backup, log deletion, restore procedures, data retention, or operational responsibility.

## 14. Summary

A change should not be judged only by whether the code works.

For municipal OSS, review must also consider whether the change is within maintainer judgment, whether it affects municipal operation, and whether it preserves or changes the current baseline.
