# Maintainer and AI guidance for audit workflow

Source context:

- Upstream repository: `Memuro-Town/MADO-queue`
- Fork repository: `to4kawa/MADO-queue`
- Audit baseline branch: `audit/mado-queue-baseline`

This note explains who the audit workflow is written for and how AI assistance should behave when supporting MADO-queue audit work.

## Intended readers

This audit workflow is not only for people who are already experienced with OSS maintenance or GitHub operations.

MADO-queue was created from the practical needs of municipal counter operations. Therefore, maintainers and related stakeholders may not be familiar with daily OSS tasks such as Issue triage, Pull Requests, Releases, SemVer, CI, review procedures, or long-term maintenance planning.

Audit notes should be written with that situation in mind.

The goal is not to make the maintainer read expert-only OSS terminology. The goal is to help the maintainer understand:

- what was observed
- what was verified
- what is still unknown
- what decision is needed now
- what can be postponed
- what would be a small change
- what would be a larger operational or compatibility change

## Basic stance

The audit fork is not a place to rush upstream changes.

The audit fork is a place to separate observation, verification, classification, and proposal before asking the upstream maintainer to make a decision.

Therefore, audit work should follow this stance:

- Do not create upstream Pull Requests without an explicit decision to do so.
- Do not post upstream Issue comments automatically.
- First reproduce or inspect the behavior in the fork when possible.
- Separate confirmed facts from assumptions and suggestions.
- Present the smallest practical next step first.
- Present larger design options as future considerations, not as immediate requirements.
- Use concrete examples from MADO-queue Issues instead of only abstract OSS terminology.

This keeps the upstream maintainer from being forced to review large or unclear changes before the problem is understood.

## Why concrete examples matter

Terms such as PATCH, MINOR, MAJOR, Release, tag, CI, or migration may be familiar to software engineers but unclear to civic-tech stakeholders or municipal maintainers.

When using those terms, audit notes should connect them to actual MADO-queue work.

For example:

- Making `TZ=Asia/Tokyo` explicit in startup documentation is a small documentation and operation clarification. It can be treated as PATCH-level.
- Adding a configurable business-date timezone setting would create a new configuration surface. It is closer to MINOR-level.
- Changing timestamp storage semantics, database compatibility, or API response compatibility may require MAJOR-level consideration.

This style lets the maintainer judge the work by its practical impact, not only by terminology.

## Recommended audit memo structure

Each audit memo should be written so that a maintainer can read it without reconstructing the investigation from scratch.

Use this structure where possible:

1. Confirmed facts
2. Reproduction or inspection steps
3. Observed result
4. Impact on operation
5. Small practical response
6. Future or larger response option
7. What remains unknown
8. Short upstream summary, if sharing upstream is later approved

The important distinction is between "what is confirmed" and "what is proposed".

## Role of AI assistance

AI may be used to support audit work, but it should not behave as an autonomous upstream contributor.

AI can help with:

- reading code and documentation
- finding relevant routes, SQL, configuration, and scripts
- drafting reproduction steps
- drafting audit notes
- organizing evidence
- classifying changes as PATCH / MINOR / MAJOR candidates
- rewriting technical notes into language that non-specialists can understand
- preparing candidate Issue comments for human review

AI must not do the following without explicit human instruction:

- create Pull Requests to the upstream repository
- comment on upstream Issues
- state unverified assumptions as facts
- recommend large design changes before the current behavior is understood
- pressure the maintainer for immediate action
- hide verification limitations
- treat Docker, printer hardware, deployment, or municipal workflow behavior as verified when they were not tested
- replace the maintainer's operational judgment with an AI-generated conclusion

For this audit workflow, AI output is only a draft or support artifact until a human checks it.

## Writing for the maintainer

Audit notes should avoid forcing the maintainer to choose between vague extremes such as "fix everything now" or "do nothing".

Instead, write in a way that separates levels of action.

Example pattern:

```text
Confirmed:
- The current behavior depends on the runtime timezone.

Small response:
- Document `TZ=Asia/Tokyo` for Japan operation.

Larger future option:
- Add an application-level business timezone setting if multi-timezone operation becomes necessary.

Not yet confirmed:
- Docker runtime behavior in a Docker-enabled environment.
```

This format lets the maintainer act on the small response without being forced to solve the larger design question immediately.

## Relationship with the upstream project

The audit fork should respect the upstream maintainer's ownership.

The purpose is to make upstream decisions easier, not to take over the project.

When upstream sharing is appropriate, the audit result should be shortened before posting. The upstream comment should usually contain:

- the confirmed observation
- the practical impact
- the smallest recommended next step
- a link or reference to the longer audit note if needed

Long internal reasoning, failed experiments, and speculative design options should remain in the audit fork unless they are necessary for the upstream decision.

## Summary

The audit workflow exists to reduce maintainer burden.

For MADO-queue, a good audit note should be:

- evidence-based
- small-step oriented
- understandable to non-specialists
- clear about verification limits
- respectful of the upstream maintainer's decision role
- careful about AI-generated assumptions

The audit fork is therefore a workspace for preparing reliable, understandable decision material before anything is sent upstream.