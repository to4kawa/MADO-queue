# MADO-queue Audit Documentation Index

## 1. Purpose

This document is the index for fork-side audit notes under `docs/audit/`.

The audit notes are not upstream policy proposals by themselves. They are working documents for organizing observations, issue triage, version baseline understanding, operational requirements, UX observations, screen design, and future governance or contribution proposals.

## 2. Current Audit Documents

| Document | Role | Main use |
|---|---|---|
| `MUNICIPAL-OSS-OPERATING-MODEL.md` | Municipal OSS operating model | Understand how staff-built municipal OSS moves from individual creation to public contribution and municipal information asset management |
| `V1.0.0-BASELINE-DOCUMENTATION.md` | v1.0.0 baseline note | Treat `v1.0.0` as the current formal reference point for future change review |
| `STABLE-OPERATIONS-PHASE2-REQUIREMENTS.md` | Stable operation Phase 2 requirements | Organize DB backup, restore, log retention, deletion, and operational responsibility |
| `UX-OBSERVATION-MODEL.md` | UX observation model | Record visitor, staff, operator, maintainer, and contributor experience as observations before turning them into issues |
| `SCREEN-DESIGN-BASELINE.md` | Screen design baseline | Record the role and review points of `/`, `/processing`, and `/display` |
| `FLASK-SCREEN-BUTTON-INVENTORY.md` | Flask implementation inventory | Record actual routes, buttons, JavaScript handlers, API calls, and code-visible state transitions when merged from its PR branch |
| `CHANGE-CLASSIFICATION-MODEL.md` | Change classification model | Classify changes as maintenance, patch-level, minor, major, operational, governance, or contribution-process items |
| `MAINTAINER-DECISION-CHECKLIST.md` | Maintainer decision checklist | Help non-engineer maintainers review issues and pull requests without relying only on code-level judgment |
| `OPERATIONAL-RISK-REGISTER.md` | Operational risk register | Track operational risks such as DB loss, log deletion, printer failure, timezone behavior, and screen misoperation |
| `ISSUE-TO-REQUIREMENT-MAPPING.md` | Issue-to-requirement mapping | Convert upstream issues into requirements, operations, UX, governance, and documentation categories |
| `UPSTREAM-COMMENT-LOG.md` | Upstream comment log | Record upstream comments made from this audit perspective and the reasoning behind them |

## 3. Reading Order

### 3.1 For Understanding the Project Position

1. `MUNICIPAL-OSS-OPERATING-MODEL.md`
2. `V1.0.0-BASELINE-DOCUMENTATION.md`

### 3.2 For Reviewing Operations and Stability

1. `STABLE-OPERATIONS-PHASE2-REQUIREMENTS.md`
2. `OPERATIONAL-RISK-REGISTER.md`
3. `ISSUE-TO-REQUIREMENT-MAPPING.md`

### 3.3 For Reviewing UX and Screens

1. `UX-OBSERVATION-MODEL.md`
2. `SCREEN-DESIGN-BASELINE.md`
3. `FLASK-SCREEN-BUTTON-INVENTORY.md`

### 3.4 For Reviewing Contributions and Change Scope

1. `CHANGE-CLASSIFICATION-MODEL.md`
2. `MAINTAINER-DECISION-CHECKLIST.md`
3. `UPSTREAM-COMMENT-LOG.md`

## 4. Audit Workflow

Use the audit notes in this order when a new upstream issue or pull request appears.

```text
1. Identify the issue or pull request scope
2. Check whether it preserves the v1.0.0 baseline
3. Classify the change type
4. Check operational risk
5. Check UX or screen impact if relevant
6. Decide whether the issue needs requirement clarification
7. Decide whether the proposal can be reviewed by maintainers
8. Record upstream comments or fork-side observations
```

## 5. Core Review Questions

For each issue or pull request, ask:

1. Is this a code issue, documentation issue, operational issue, UX issue, or governance issue?
2. Does it preserve the current `v1.0.0` baseline?
3. Does it affect DB, logs, startup, backup, restoration, or screen workflow?
4. Can a non-engineer maintainer understand the operational meaning?
5. Should it be split into smaller proposals?
6. Does it require municipal explanation or internal decision-making?
7. Is the proposed change safe as a maintenance change, or is it a larger versioned change?

## 6. Status

This index is a living fork-side audit document.

It should be updated when new audit notes are added, renamed, merged, or promoted into upstream-facing proposals.
