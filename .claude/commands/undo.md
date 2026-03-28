# Undo Last Commit

Safely undo the last commit while preserving changes.

## Variables
args: $ARGUMENTS

## Instructions

Undo the most recent commit with safety checks. Changes are preserved in working directory by default.

## Workflow

### 1. Safety Checks

```bash
git log -1 --oneline
git status
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null
```

Check:
- What commit will be undone
- Whether commit has been pushed (WARN if yes)
- Any uncommitted changes (WARN - will be mixed with undone changes)

### 2. Confirm with User

Show:
- Commit to undo: `<hash> <message>`
- Pushed status: Yes/No
- Recommendation

If pushed:
- WARN: "This commit has been pushed. Undoing will require force push."
- Suggest alternatives: revert commit instead
- Require explicit confirmation

### 3. Execute Undo

**Default (soft reset - keeps changes staged):**
```bash
git reset --soft HEAD~1
```

**With `--unstage` (keeps changes but unstaged):**
```bash
git reset HEAD~1
```

**With `--hard` (discards changes - DANGEROUS):**
```bash
git reset --hard HEAD~1
```

### 4. Post-Undo

```bash
git status
git log -1 --oneline
```

Report:
- New HEAD commit
- Status of undone changes
- Next steps

## Arguments

- No args: Soft reset (changes stay staged)
- `--unstage`: Mixed reset (changes unstaged)
- `--hard`: Hard reset (DISCARDS changes - requires confirmation)
- `--revert`: Create revert commit instead of reset (safe for pushed commits)

## Safety Rules

- NEVER hard reset without explicit `--hard` flag AND user confirmation
- WARN loudly if commit was pushed
- Suggest `--revert` for pushed commits
- Show exactly what will happen before doing it

## Output

Return:
- What was undone
- Current HEAD
- Status of changes
