# MADO-queue Operational Risk Register

## 1. Purpose

This document records operational risks observed or inferred during external audit of MADO-queue.

The purpose is not to claim that the current system is unsafe. The purpose is to keep operational risks visible so that issues, documentation, tests, and future requirements can be prioritized.

This is a fork-side audit note, not an upstream official risk register.

## 2. Risk Rating

Use the following simple rating model.

| Rating | Meaning |
|---|---|
| Low | Limited impact or easy recovery |
| Medium | Operational confusion, partial data loss, or maintainability concern possible |
| High | Service interruption, data loss, auditability loss, or municipal decision risk possible |
| Unknown | More observation or operational information needed |

## 3. Risk Register

| ID | Risk | Area | Rating | Current concern | Possible mitigation | Related docs/issues |
|---|---|---|---|---|---|---|
| OR-001 | DB file loss or corruption | DB / backup | High | `numbers.db` is operationally central; README says backup is file copy, but complete backup/restore procedure is not yet formalized | Document backup and restore procedure; test restore; define backup timing | #14, Stable Operation Phase 2 |
| OR-002 | Log deletion before retention policy | Logs / auditability | High | Automatic deletion can remove records needed for inquiry, troubleshooting, audit, or security evidence | Define retention policy, archive-before-delete, backup-before-delete | #17, Stable Operation Phase 2 |
| OR-003 | DELETE without file-size recovery expectation | SQLite operation | Medium | SQLite DELETE may not reduce file size unless VACUUM is used; VACUUM itself may affect operation | Document VACUUM behavior; schedule outside opening hours; backup first | #17 |
| OR-004 | Printer failure after DB commit | Printer / UX / operation | Medium | Ticket number may be issued and logged even if printing fails; visitor/staff may not notice from screen | Record print-failure handling; consider visible error or manual recovery procedure | Flask inventory, Screen design baseline |
| OR-005 | Repeated ticket issuing by rapid taps | UI / DB | Medium | Ticket buttons on `/` are not disabled during `/get_next_number` request | Consider in-flight guard or operational note; verify actual frequency | Flask inventory |
| OR-006 | Timezone / same-day filtering ambiguity | Date handling / logs | High | Same-day filtering and reset behavior depend on correct JST interpretation | Document JST assumption; test UTC/JST behavior; keep issue evidence | Issue #6 audit work |
| OR-007 | Processing operations matching by ticket number only | DB / workflow | Medium | Some UI calls identify processing records only by `ticket_number`; ambiguity may occur if not constrained by same-day/category/event linkage | Confirm current SQL constraints; document assumptions; add tests if needed | Flask inventory |
| OR-008 | URL separation only for visitor/staff screens | Access model | Unknown | Requirements mention URL separation; actual operational network/access controls need confirmation | Document operational access assumptions; avoid overclaiming security | v1.0.0 baseline |
| OR-009 | Display chime depends on browser audio unlock | Waiting-room UX | Medium | Public display audio requires user interaction before sound can play | Document display startup checklist; verify at actual device | Screen design baseline, Flask inventory |
| OR-010 | Display hides calls older than 60 seconds | Waiting-room UX | Unknown | `/display` filters calls by `seconds_since < 60`; actual field behavior may need confirmation | Verify operational expectation; document behavior | Flask inventory |
| OR-011 | Auto-refresh interfering with staff operation | Staff UX | Unknown | `/processing` reloads periodically, with some interaction guard; actual PC use should be checked | Manual observation; adjust only after evidence | UX observation model |
| OR-012 | Oversized external PR beyond maintainer review capacity | Governance / contribution | High | Large PRs can bundle DX, structure, runtime, config, and docs changes beyond non-engineer maintainer judgment | Change classification; maintainer checklist; ask for split | #18, #19 |
| OR-013 | Baseline drift without version decision | Versioning / governance | High | Structural changes may shift from v1.0.0 baseline without explicit major-version discussion | Use v1.0.0 baseline and change classification | #16, #18, #19 |
| OR-014 | Documentation/code mismatch | Documentation / operation | Medium | Architecture examples and current implementation may differ; UI labels and submitted button text may differ | Inventory mismatches; correct docs after confirmation | Flask inventory |
| OR-015 | Category D operational meaning unclear | UX / workflow / logs | Unknown | Category D records non-printing visitor count and does not appear in normal waiting flow; business meaning should be confirmed | Manual check with operator; document expected handling | Requirements, Flask inventory |

## 4. Priority Risks

### 4.1 Highest Priority

The highest-priority risks are:

1. DB backup and restore ambiguity
2. Log deletion before retention policy
3. Timezone / same-day filtering ambiguity
4. Oversized PRs beyond maintainer review capacity
5. Baseline drift without version decision

These risks are not only technical. They affect operational continuity, auditability, and municipal decision-making.

### 4.2 Medium Priority

Medium-priority risks include:

- printer failure after DB commit
- repeated ticket issuing
- documentation/code mismatch
- display audio unlock behavior
- SQLite VACUUM expectation

These may become higher priority if confirmed in actual operation.

## 5. How to Use This Register

When a new issue or PR appears:

1. Identify whether it touches any listed risk.
2. Add a new risk if needed.
3. Update the rating only when new evidence is available.
4. Link the issue or PR to the relevant risk ID.
5. Decide whether the topic belongs to bug fix, stable operation, UX observation, documentation, or governance.

## 6. Non-goals

This register does not:

- certify security posture
- replace municipal risk management
- define official production operation
- prove that listed risks occur in current field use

It is an audit planning document.

## 7. Summary

The current audit focus is not to increase implementation complexity.

The focus is to make operational risks explicit, so that future changes can be reviewed against the current baseline and municipal operating context.
