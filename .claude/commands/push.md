# Push

Push commits to remote repository safely.

## Variables
args: $ARGUMENTS

## Instructions

Push local commits to remote with safety checks.

## Workflow

### 1. Pre-flight Checks

```bash
git status
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log -5 --oneline
```

Verify:
- No uncommitted changes (warn if present)
- Commits to push exist
- Not pushing to protected branch without confirmation

### 2. Branch Safety

If pushing to `main` or `master`:
- Warn user: "Pushing directly to main branch"
- Require explicit confirmation
- NEVER use `--force` on main/master

### 3. Execute Push

```bash
git push origin $(git branch --show-current)
```

If upstream not set:
```bash
git push -u origin $(git branch --show-current)
```

### 4. Handle Failures

If push rejected (non-fast-forward):
- Suggest: `git pull --rebase origin <branch>`
- NEVER auto-force push
- Ask user for guidance

### 5. Post-Push

Report:
- Commits pushed
- Remote URL
- Suggest PR creation if on feature branch

## Arguments

- No args: Push current branch
- `--force`: Force push (requires confirmation, blocked on main)
- `--tags`: Push tags
- `<branch>`: Push specific branch

## Output

Return:
- Number of commits pushed
- Remote branch URL
- Suggested next action (PR if feature branch)
