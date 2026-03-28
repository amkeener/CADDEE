# Git Workflow Rules

## Pull Request Creation

> **PRs are ONLY created when the user explicitly requests it via `/pr` command**

### DO NOT automatically create PRs:
- After completing a task or feature
- After a code review passes
- After fixing issues from a review
- After any build/test succeeds

### Only create PRs when:
- User runs `/pr` command
- User explicitly says "create a PR" or "open a pull request"

### Why
The user needs control over:
- When code is ready for review
- Which changes to batch together
- PR timing relative to other team activities

## Commits

Commits ARE encouraged proactively:
- After completing a feature or fix
- After making meaningful progress
- Before switching to a different task

Use conventional commit format: `feat:`, `fix:`, `chore:`, `docs:`, etc.

## Branch Management

- Create branches when starting new work (if not already on a feature branch)
- Push commits regularly to backup work
- Do NOT push to main/master directly
