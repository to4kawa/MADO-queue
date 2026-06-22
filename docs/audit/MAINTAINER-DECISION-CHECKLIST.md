# MADO-queue Maintainer Decision Checklist

## 1. Purpose

This document provides a fork-side audit checklist for maintainers reviewing MADO-queue issues and pull requests.

It assumes that maintainers may not always be software engineers. Therefore, the checklist focuses on decision quality, operational impact, municipal explanation, and whether the proposal is reviewable at maintainer level.

This document is not an upstream rule by itself. It is a working note that may later inform upstream contribution guidance or governance documentation.

## 2. Basic Rule

A maintainer does not need to understand every implementation detail to make a safe decision.

However, the maintainer must be able to understand:

- what changes
- who is affected
- whether current operation changes
- whether data, logs, backup, or screen workflow changes
- whether the change can be safely reverted
- whether the change needs municipal explanation or internal review

If these cannot be understood, the safe decision is usually to ask for clarification, split the proposal, or defer the change.

## 3. First-Pass Checklist

For every issue or pull request, ask:

1. What problem is being solved?
2. Who has the problem?
3. Is this problem confirmed from operation, documentation, code, or contributor assumption?
4. Is the proposal small enough to review?
5. Does it change production behavior?
6. Does it change documented behavior?
7. Does it affect DB, logs, backup, restore, startup, screen flow, or printer operation?
8. Does it need a municipal or operational decision before implementation?
9. Is the testing evidence understandable?
10. Is AI assistance disclosed if used?

## 4. Issue Review Checklist

When reviewing an issue, ask:

### 4.1 Problem Clarity

- Is the problem stated clearly?
- Is the user or operator affected by the problem identified?
- Is the current behavior described?
- Is the expected behavior described?
- Is there evidence such as logs, screenshots, code references, or operation notes?

### 4.2 Scope

- Is the issue about a bug?
- Is it about documentation?
- Is it about operations?
- Is it about UX or screen design?
- Is it about governance or contribution process?
- Is it mixing multiple topics?

### 4.3 Decision Path

Choose one:

- accept as small maintenance issue
- ask for clarification
- split into smaller issues
- move to operations requirement discussion
- move to governance discussion
- defer as future phase
- close as out of scope

## 5. Pull Request Review Checklist

When reviewing a pull request, ask:

### 5.1 Change Type

- Is it documentation-only?
- Does it change application code?
- Does it change startup commands?
- Does it change Docker behavior?
- Does it change Python version or dependencies?
- Does it change DB schema or DB location?
- Does it change logs or retention?
- Does it change screen behavior?
- Does it add external services?

### 5.2 Reviewability

- Can the PR be understood from its description?
- Does the PR explain why the change is needed?
- Does it list affected files and behavior?
- Does it describe testing?
- Does it describe rollback or reversibility when relevant?
- Is the PR small enough to review safely?

### 5.3 Operational Impact

- Does current deployment change?
- Does daily operation change?
- Does backup or restore change?
- Does printer operation change?
- Does screen operation change for visitors or staff?
- Does the change affect opening-hour availability?
- Could the change affect data loss or log loss?

### 5.4 Municipal Explanation

Would a municipal manager or responsible department need to understand this change?

If yes, the PR should explain:

- operational benefit
- operational risk
- whether existing procedure changes
- whether data handling changes
- whether internal approval may be needed
- why this change is needed now

## 6. Documentation-only PRs

Documentation-only PRs are generally lower risk, but still require review.

Check:

- Does the text match actual behavior?
- Does it avoid unsupported claims?
- Does it distinguish facts from interpretation?
- Does it make operation easier for maintainers or users?
- Does it accidentally define a new policy without agreement?

## 7. Code-changing PRs

Code-changing PRs require stronger checks.

Check:

- Is there a related issue?
- Is the change scoped to one problem?
- Are tests or manual verification described?
- Does it preserve `v1.0.0` baseline behavior?
- Does it preserve current operation unless explicitly discussed?
- Is rollback possible?

## 8. DB / Log / Backup Changes

For any change touching DB, logs, retention, deletion, backup, or restore, ask:

1. What data is affected?
2. Can data be lost?
3. Can logs be lost?
4. Is a backup required before applying the change?
5. Is a restore procedure documented?
6. Does this affect auditability or inquiry response?
7. Who operates this procedure?
8. Does this need municipal internal review?

If these are unclear, do not treat the PR as a simple implementation change.

## 9. Screen / UX Changes

For screen or UI changes, ask:

1. Which screen changes?
2. Which user is affected?
3. What operation changes?
4. Is the change visible to visitors, staff, or waiting-room users?
5. Does it affect misoperation risk?
6. Does it affect logs or state transitions?
7. Are screenshots or screen recordings provided?
8. Does the screen remain understandable to non-technical users?

## 10. Developer Experience Changes

Developer experience improvements can be useful, but they should be separated from production-impacting changes.

Ask:

- Is this only for local development?
- Does it change production startup?
- Does it change project structure?
- Does it change supported Python version?
- Does it change Docker Compose behavior?
- Does it affect documentation for operators?
- Can it be split into smaller PRs?

If a DX PR changes project structure, config format, startup commands, dependencies, and documentation together, it may be a major-version-level proposal rather than a small DX improvement.

## 11. AI-assisted Contributions

If AI assistance was used, check:

- Is the AI tool disclosed?
- Is the scope of AI use disclosed?
- Was human review performed?
- Was human testing performed?
- Are generated claims supported by code, docs, or tests?

AI assistance is not automatically a problem. The issue is whether responsibility, review, and verification are clear.

## 12. Decision Outcomes

A maintainer can choose one of the following outcomes.

| Outcome | Meaning |
|---|---|
| Accept / merge | The proposal is small, clear, tested, and within maintainer judgment |
| Request clarification | The problem may be valid, but the proposal is not yet reviewable |
| Request split | The PR mixes multiple concerns and should be divided |
| Defer | The issue is valid but belongs to a later phase |
| Move to requirements | Implementation should wait until requirements are clarified |
| Move to governance | The issue affects decision rules or contribution process |
| Close as out of scope | The proposal does not fit the current package or operating model |

## 13. Minimum Safe Comment Template

When unsure, a maintainer can say:

```md
Thank you for the proposal.

This looks useful, but the current scope appears to affect more than one decision area. Before reviewing it as an implementation change, I would like to clarify:

- what current behavior changes
- whether production operation changes
- whether DB/log/startup/screen behavior changes
- whether this can be split into smaller changes
- whether this requires operational or municipal review

For now, I think this should remain in discussion rather than being merged as-is.
```

## 14. Summary

The safest maintainer decision is not always merge or reject.

For municipal OSS, the key is to decide whether the proposal is small enough, understandable enough, and operationally safe enough to accept at the current decision level.
