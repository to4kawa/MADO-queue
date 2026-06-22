# MADO-queue UX Observation Model

## 1. Purpose

This document defines a fork-side audit model for recording UX observations around MADO-queue.

In this document, UX does not only mean screen usability. It includes the experience of visitors, counter staff, waiting-room users, operators, maintainers, and external contributors.

This is not an upstream specification. It is an external audit note for converting observations into requirements, issue triage, documentation improvements, and governance discussions.

## 2. Basic Principle

UX should first be recorded as an observed situation, not as an implementation request.

A useful UX note should describe:

- who was affected
- in what situation
- what happened
- what was confusing, risky, helpful, or burdensome
- what operational meaning it has
- whether it should become documentation, UI change, operational procedure, requirement clarification, or governance discussion

## 3. Observation Targets

UX observations may target the following actors.

| Actor | Description |
|---|---|
| Visitor | Person using the ticket issuing screen or waiting for service |
| Counter staff | Staff operating the processing screen and handling visitors |
| Waiting-room user | Person viewing the display screen |
| Operator | Person responsible for startup, backup, restoration, or daily operation |
| Maintainer | Person reviewing issues, pull requests, versions, and releases |
| External contributor | Person proposing issues, documentation, code changes, or operational ideas |

## 4. Observation Template

Use the following template when recording UX observations.

```md
## UX-YYYYMMDD-001: Short title

### Actor

Visitor / Counter staff / Waiting-room user / Operator / Maintainer / External contributor

### Situation

Describe the concrete situation.

Examples:

- issuing a ticket
- calling the next number
- completing a ticket
- viewing the waiting-room display
- backing up the DB
- reviewing a pull request
- reading an issue

### What happened

Record facts. Avoid immediately jumping to a solution.

### Friction / risk / value

Describe confusion, anxiety, delay, rework, operational risk, maintenance burden, or observed value.

### Expected state

Describe what would feel natural, safe, understandable, or operationally sustainable.

### Operational meaning

Explain the relationship to municipal counter service, staff workload, auditability, explanation responsibility, maintenance, handover, or safety.

### Related screen / function / document

Examples:

- `/`
- `/processing`
- `/display`
- DB
- logs
- README
- REQUIREMENTS
- ARCHITECTURE
- CONTRIBUTING
- GOVERNANCE

### Related Issue / PR

List related upstream or fork-side issues and pull requests.

### Possible next actions

List candidate next actions, not immediate implementation commands.

### Classification

Choose one or more:

- wording improvement
- screen design issue
- operational procedure issue
- documentation issue
- requirement clarification
- stable operation requirement
- governance issue
- contribution process issue
```

## 5. Classification Guide

### 5.1 Wording Improvement

Use this when the main problem is terminology, button labels, user-facing text, or documentation wording.

### 5.2 Screen Design Issue

Use this when the main problem is layout, visibility, button placement, state display, screen flow, or operation clarity.

### 5.3 Operational Procedure Issue

Use this when the main problem is startup, shutdown, backup, restore, printer handling, manual workaround, or daily operation.

### 5.4 Documentation Issue

Use this when the problem can be reduced by documenting existing behavior or existing operation.

### 5.5 Requirement Clarification

Use this when the expected behavior is unclear or when the issue depends on a business rule.

### 5.6 Stable Operation Requirement

Use this when the issue affects DB persistence, logs, backups, restore procedures, retention, deletion, versioning, or long-term operation.

### 5.7 Governance Issue

Use this when the issue affects who can decide, whether municipal review is required, or whether the change is within maintainer judgment.

### 5.8 Contribution Process Issue

Use this when the issue affects how external contributors should propose, split, explain, test, or disclose changes.

## 6. Example Observation: Log Deletion Proposal

## UX-20260623-001: Log deletion proposal moves toward implementation before retention policy is clear

### Actor

Maintainer / Operator / External contributor

### Situation

A proposal was made to periodically delete log data in order to avoid long-term DB growth.

### What happened

The issue discussed deleting old rows from `event_logs` and `processing_logs`, running `VACUUM`, and scheduling the purge process.

However, DB backup policy, log retention period, inquiry response needs, auditability, and deletion responsibility were not yet fully separated from the implementation proposal.

### Friction / risk / value

The proposal has operational value because uncontrolled DB growth can become a long-term problem.

At the same time, logs may be useful for troubleshooting, inquiry response, operational review, auditability, and security evidence. If deletion is implemented before the retention policy is clear, the project may lose information that later becomes necessary.

### Expected state

Before implementing automatic deletion, the project should clarify:

- what logs are operationally necessary
- how long each log should be retained
- whether logs should be archived before deletion
- whether DB backup should run before deletion
- who is responsible for operating and reviewing deletion

### Operational meaning

This is not only a storage cleanup issue. It belongs to stable operation Phase 2, together with DB backup, restoration, log retention, and operational responsibility.

### Related screen / function / document

- DB
- `event_logs`
- `processing_logs`
- backup procedure
- restore procedure
- stable operation documentation

### Related Issue / PR

- Memuro-Town/MADO-queue#14
- Memuro-Town/MADO-queue#17

### Possible next actions

- Record the log retention policy as a stable operation requirement
- Clarify DB backup and restore expectations
- Decide whether deletion should be preceded by archive/export
- Only then consider a purge implementation

### Classification

- stable operation requirement
- operational procedure issue
- governance issue

## 7. Example Observation: Large Developer Experience Pull Request

## UX-20260623-002: Developer-experience proposal exceeds non-engineer maintainer review capacity

### Actor

Maintainer / External contributor / Operator

### Situation

A pull request proposed developer-experience improvements, including project structure changes, configuration format changes, startup command changes, Python version changes, dependency locking, and Dev Container setup.

### What happened

The proposal was framed as developer-experience improvement, but the change set affected execution structure, configuration, startup method, dependency management, and documentation at the same time.

### Friction / risk / value

The proposal may have value for developers, but it is difficult for a non-engineer maintainer to judge as a routine change.

If merged without separating the concerns, it may shift the baseline from the current `v1.0.0` operational model to a new major-version-level structure without enough municipal explanation material.

### Expected state

Developer-experience improvements should be separated from production startup changes, project structure changes, configuration changes, and major version decisions.

Each proposal should explain:

- who benefits
- whether the current operation changes
- whether the documented startup procedure changes
- whether municipal review may be required
- whether the change can be reviewed by maintainers

### Operational meaning

This is not only a code review issue. It affects contribution process design, maintainer decision scope, and municipal OSS governance.

### Related screen / function / document

- README
- ARCHITECTURE
- CONTRIBUTING
- versioning policy
- development environment documentation

### Related Issue / PR

- Memuro-Town/MADO-queue#18
- Memuro-Town/MADO-queue#19

### Possible next actions

- Keep the issue-level governance discussion separate from PR code review
- Split developer-environment improvements into smaller proposals
- Treat baseline-changing structure changes as major-version-level proposals
- Document how external contributors should scope PRs

### Classification

- contribution process issue
- governance issue
- documentation issue

## 8. Relationship to Screen Design

This UX observation model is paired with `SCREEN-DESIGN-BASELINE.md`.

Screen design records what each screen is intended to do and how screen changes should be reviewed.

UX observations record what happens in use, operation, maintenance, and contribution.

The two should remain separate:

- UX observation: records situation and meaning
- screen design: records screen role and design baseline
