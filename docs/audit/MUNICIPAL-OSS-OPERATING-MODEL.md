# Municipal OSS Operating Model Draft

## Purpose

This document is a draft working note for examining how a staff-built municipal OSS project can move from individual creation to organizational acceptance, external contribution, and municipal information asset management.

This document is not an upstream policy proposal. It is an external audit and project-management note used to organize observations, hypotheses, and future proposal ideas.

## Background

MADO-queue began as a system created by municipal staff to solve a concrete workplace problem. It was then accepted in actual workplace operation and later published as OSS.

Once a staff-built system becomes used in real municipal work, the issue is no longer only whether the code works. The municipality must also consider maintenance, handover, auditability, responsibility boundaries, and how external contributions can be accepted safely.

## Working Model

The current working model is:

```text
individual workplace creation
-> workplace acceptance
-> maintenance problem recognition
-> public visibility through article / SNS
-> GitHub issues, reviews, and contributions
-> municipal decision process
-> municipal information asset management
-> continuous maintenance and handover
```

This model treats public attention as an entry point, not as the final result. A note article or SNS discussion may make the project visible, but sustainable value appears only when that attention is converted into review, issue clarification, documentation, contribution, municipal decision-making, and operational records.

## Two Management Tracks

This model separates two different management tracks.

### 1. OSS management on GitHub

This track concerns how the project is managed as an open-source repository.

Main concerns include:

- Issue handling
- Pull request handling
- contributor guidance
- release management
- versioning
- PATCH / MINOR / MAJOR classification
- development environment
- security reporting
- SBOM and dependency visibility
- release notes
- maintainer decision scope

### 2. Municipal information asset management

This track concerns how the system is managed as a municipal business system or information asset.

Main concerns include:

- responsible department
- responsible owner
- operation department
- data handled by the system
- personal information status
- database location
- backup and recovery
- operational continuity
- incident response
- handover after staff transfers
- auditability
- legal and business fitness confirmation by each adopting municipality

These two tracks should be connected, but not confused. GitHub operations help external contributors participate. Municipal information asset management helps the municipality remain accountable for real-world operation.

## Proposal Conversion Process

External OSS proposals should not be accepted blindly.

A GitHub Issue or Pull Request may begin as a technical proposal, but before adoption it should be translated into a municipal decision form.

The conversion should clarify:

- what is confirmed
- what is unconfirmed
- affected package or function
- affected business operation
- production impact
- data impact
- security impact
- whether internal approval is required
- whether information asset records must be updated
- whether the change is PATCH, MINOR, or MAJOR
- what should be recorded in the release note

The purpose of this conversion is not to slow down contribution. The purpose is to make contribution adoptable without blind approval.

## PATCH-Level Decision Model

For PATCH-level changes, the project may be able to reduce maintainer and internal decision burden by defining a lightweight acceptance route.

A PATCH-level change should generally satisfy the following conditions:

- it does not change the existing business workflow
- it does not break existing usage
- it does not change the DB schema
- it does not break API compatibility
- it does not significantly change production operation procedures
- the reason for the change is recorded in an Issue or PR
- two or more contributors have reached the same view, where possible
- the change is recorded in the release note

The goal is not to increase the personal responsibility of the maintainer. The goal is to make it easier for the maintainer to judge adoption, deferral, or additional confirmation without blind approval.

In this model, two or more matching contributor views are not an automatic approval rule. They are decision-support evidence that can reduce the maintainer's review burden and make the basis for adoption more readable.

## Role of External Contributors

External contributors do not only provide code.

They can also act as:

- issue reporters
- second verifiers
- documentation contributors
- operational translators
- risk identifiers
- proposal reviewers
- audit-support contributors

A contributor who does not submit a PR may still provide significant value by clarifying a technical issue, translating it into operational impact, and making it easier for the municipality to decide responsibly.

## Maintainer Role in Small Municipal OSS

In a small municipal OSS project, the GitHub maintainer does not necessarily have to be the person who fully understands every technical detail or implements every fix.

The maintainer can instead act as a process manager for the repository, if the project has enough supporting structure.

Such structure may include:

- clear Issue templates
- clear contribution guidance
- contributor verification records
- PATCH / MINOR / MAJOR decision criteria
- release notes
- escalation criteria for internal approval
- separation between GitHub OSS management and municipal asset management

This makes it possible for a maintainer to manage the repository responsibly without becoming the sole technical authority or the sole risk owner.

## Responsibility Readability

For municipal OSS, technical readability is not sufficient.

The project should also improve responsibility readability: the degree to which roles, decision rights, review responsibilities, approval boundaries, and handover responsibilities can be understood by maintainers, contributors, and municipal stakeholders.

This is especially important when a project starts as staff-built software but becomes used as a municipal operational system.

## Audit and Supervision

Public OSS contribution and municipal auditability should be compatible.

The desired state is not uncontrolled openness, and it is also not closed internal control. The desired state is a process in which external findings and proposals can be received openly, translated into municipal decision material, reviewed with sufficient evidence, and recorded for later explanation.

This requires avoiding blind acceptance. For each accepted change, the project should be able to explain:

- why the change was needed
- who reviewed or verified it
- what impact it has
- why it was considered safe to adopt
- whether internal approval was required
- where the decision and verification were recorded

## Long-Term Question

The long-term question is:

How can a small municipality safely receive external OSS contributions, operate a staff-built system as a public information asset, and continue maintenance after personnel changes without relying on a single highly capable individual?

This document collects working hypotheses toward that question.
