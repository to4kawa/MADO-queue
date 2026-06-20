# Verification workflow

This repository uses a verification-first workflow for audit findings.

The purpose is to separate observation from remediation and to avoid opening upstream issues for problems that are not reproducible or not actionable.

## Workflow

1. Create a verification issue in the fork.
   - Describe the suspected problem.
   - Define the target routes, files, or data paths.
   - State the verification method, expected evidence, and stopping conditions.
   - Do not assume the problem is real before testing.

2. Create a dedicated verification branch from `main`.
   - Use a branch name such as `verify/<topic>`.
   - Do not modify `main`.
   - Do not modify `audit/mado-queue-baseline`.
   - Do not modify production code unless the verification itself strictly requires an isolated experimental change.

3. Run the verification.
   - Add only test scripts, fixtures, and result documents needed to reproduce the observation.
   - Record the base commit SHA, environment, commands, inputs, outputs, and limitations.
   - Distinguish confirmed behavior from inference.
   - Record negative results as valid outcomes.

4. Open a verification pull request in the fork.
   - The PR is a review surface for evidence, not a merge target.
   - Link the fork issue.
   - State that production code is unchanged.
   - Include AI-assistance disclosure when applicable.

5. Review and record the result.
   - Copy the final conclusion into `docs/audit/` on `audit/mado-queue-baseline`.
   - Keep links to the fork issue and verification PR.
   - Do not copy experimental code into the audit branch.

6. Decide whether to create an upstream issue.

   Create an upstream issue only when:

   - The behavior is reproducible.
   - The impact is relevant to the upstream project.
   - The finding is not already covered by an existing issue or PR.
   - The result can be explained with concrete evidence.

   Do not create an upstream issue when:

   - The suspected problem cannot be reproduced.
   - The behavior is intentional or already documented.
   - The effect is limited to the fork or test harness.
   - The operational impact is too speculative.
   - The finding is already covered upstream.

7. Close the verification PR without merging.
   - Add the final upstream-issue link, or record that no upstream issue was created.
   - Close the PR after the result has been recorded in the audit branch.
   - Keep the branch temporarily if the public links are still needed.

8. Close the fork issue when the verification cycle is complete.
   - State one of the following outcomes:
     - Confirmed and reported upstream.
     - Confirmed but not reported upstream, with reason.
     - Not reproduced.
     - Expected behavior.
     - Inconclusive.

## Decision principle

A verification task is successful even when the result is that no upstream issue should be created.

The workflow is intended to produce reliable evidence, not to maximize the number of issues, pull requests, or fixes.

## Branch roles

- `main`: fork baseline; do not use for audit experiments.
- `audit/mado-queue-baseline`: evidence and conclusions only; not a merge target.
- `verify/*`: disposable verification work.

## Pull request roles

Verification PRs in the fork are temporary review records. They are normally closed without merge after:

1. the evidence is reviewed,
2. the audit branch is updated, and
3. the upstream-reporting decision is recorded.
