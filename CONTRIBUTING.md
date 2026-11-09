# Contributing

This document defines the development and change-control rules for this repository.

## 1. Source-of-truth branches

- `main` is the stable branch. It contains only tested, reviewed, human-approved changes.
- Work must happen on a separate branch; do not develop directly on `main`.
- Use these prefixes:
  - `feature/<short-description>` for product functionality.
  - `fix/<short-description>` for bug fixes.
  - `research/<short-description>` for research work.
  - `experiment/<short-description>` for exploratory work.
  - `docs/<short-description>` for documentation.
  - `test/<short-description>` for test-only changes.
  - `chore/<short-description>` for maintenance and governance.

Create branches from an up-to-date `main` unless the task explicitly depends on another branch. Keep branches focused and short-lived.

## 2. Commit standards

Use Conventional Commit-style messages:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `test: ...`
- `refactor: ...`
- `chore: ...`

Each commit should represent one coherent change. Do not commit generated output, credentials, API keys, tokens, private data, local databases, caches, virtual environments, or unrelated files.

Review `git status` and `git diff --cached` before every commit. Stage explicit paths rather than blindly staging everything.

## 3. Required validation

Before proposing a change for integration:

1. Run the relevant automated tests.
2. Run `git diff --check`.
3. Review the complete diff for correctness, scope, secrets, and accidental files.
4. Confirm the working tree contains only intended changes.
5. Report commands run and their actual results.

A passing test suite does not replace code review. Never claim a test or check passed unless its output confirms it.

## 4. Human approval and merge policy

- A plan, recommendation, generated patch, or passing test is not authorization to merge.
- A human must explicitly approve integration into `main`.
- Prefer pull requests and reviewable diffs when a remote host is configured.
- For local integration, use `git merge --ff-only` when possible.
- Never force-push, rewrite shared history, delete branches, or publish repository contents without explicit authorization.
- Do not configure a remote, change hosting settings, or make a repository public without explicit authorization.

## 5. AI contributor permissions

AI tools may, within the task scope:

- Inspect repository files and Git history.
- Research, propose designs, edit code, write tests, and prepare documentation.
- Run local tests and static checks.
- Create or work on an isolated task branch when authorized.

AI tools must not, without explicit human authorization:

- Merge into `main`.
- Push or publish commits.
- Change remotes, access controls, branch protections, or repository visibility.
- Delete branches, discard user changes, reset hard, rebase shared history, or force-push.
- Access, expose, or commit secrets or private information.

When scope or authorization is unclear, stop before the consequential action and ask.

## 6. Safe recovery

- Inspect `git status`, `git diff`, and `git log` before recovery operations.
- Prefer reversible actions and preserve uncommitted work.
- Do not use `git reset --hard`, `git clean`, history rewriting, or destructive checkout commands as routine cleanup.
- Before any potentially destructive recovery, explain the impact and obtain explicit approval.
- Use commits as recovery points; keep independent backups for important work.

## 7. Suggested task workflow

1. Confirm the objective, scope, and acceptance criteria.
2. Inspect the current branch and working tree.
3. Create a focused branch from `main`.
4. Make the smallest coherent change.
5. Add or update tests and documentation.
6. Run validation and inspect the final diff.
7. Present an evidence-based summary, limitations, and proposed commit.
8. Obtain human approval before committing when required, merging, or publishing.
9. Verify the resulting commit and clean working tree.

## 8. Scope of enforcement

These rules document repository policy. Local Git settings and documentation are safeguards, not hard security boundaries. Once a remote host is selected, configure server-side branch protection, required reviews, and required CI checks to enforce the policy centrally.
