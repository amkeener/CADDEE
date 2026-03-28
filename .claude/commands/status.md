# Git Status Overview

Quick overview of repository state.

## Instructions

Provide a comprehensive but concise git status summary.

## Workflow

Run in parallel:
```bash
git branch --show-current
git status --short
git log -3 --oneline
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo "No upstream"
git stash list
```

## Output Format

```
Branch: <branch_name>
Upstream: <ahead/behind status or "not set">

Changes:
  Staged: <count> files
  Modified: <count> files
  Untracked: <count> files

Recent commits:
  <hash> <message>
  <hash> <message>
  <hash> <message>

Unpushed: <count> commits
Stashes: <count>
```

Keep it brief - just the essentials.
