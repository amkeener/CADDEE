# Commit

Create a git commit with a well-formatted message.

## Variables
message_hint: $ARGUMENTS

## Instructions

Create a git commit following project conventions. Analyze changes, generate a proper commit message.

## Workflow

### 1. Analyze Changes

Run in parallel:
```bash
git status
git diff --cached --stat  # Staged changes
git diff --stat           # Unstaged changes
git log -3 --oneline      # Recent commits for style reference
```

If no staged changes, ask user what to stage or stage all with confirmation.

### 1.5. Frontend Linting Checks (REQUIRED for frontend repos)

**Detect if this is a frontend project:**
```bash
# Check for frontend indicators
if [ -f "package.json" ] && grep -q '"lint:check"' package.json 2>/dev/null; then
  echo "Frontend project detected - running lint checks"
  FRONTEND=true
else
  FRONTEND=false
fi
```

**If frontend project, run checks BEFORE committing:**
```bash
if [ "$FRONTEND" = "true" ]; then
  # Run format check
  echo "Running format:check..."
  pnpm format:check 2>&1 | tail -10
  FORMAT_EXIT=$?

  # Run lint check
  echo "Running lint:check..."
  pnpm lint:check 2>&1 | tail -20
  LINT_EXIT=$?

  # Report results
  if [ $FORMAT_EXIT -ne 0 ]; then
    echo "Format check failed - auto-fixing..."
    pnpm format:write
  fi
fi
```

**If format:check fails:**
1. Auto-run `pnpm format:write` to fix formatting
2. Show which files were reformatted
3. Stage the reformatted files

**If lint:check has errors (not just warnings):**
1. Show the errors
2. Ask user: "Lint errors found. Would you like to:"
   - Fix the errors before committing (recommended)
   - Continue anyway with `--skip-lint` flag

**Note:** Pre-existing lint warnings (like no-console) are acceptable and don't block commits.

### 2. Categorize Changes

Identify:
- **Type**: feat, fix, chore, docs, refactor, test, style, perf
- **Scope**: Affected area
- **Breaking**: Any breaking changes?

Use `message_hint` if provided for guidance.

### 3. Generate Commit Message

Follow conventional commits format:
```
<type>(<scope>): <short summary>

<body - what and why, not how>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Rules:
- Subject line: imperative mood, no period, max 72 chars
- Body: wrap at 72 chars, explain motivation
- Reference issues if applicable

### 4. Execute Commit

```bash
git add <files>  # If needed
git commit -m "$(cat <<'EOF'
<commit message>
EOF
)"
git status  # Verify success
```

### 5. Offer Next Steps

Ask user:
- Push to remote? (`git push`)
- Continue working?

**Note:** Do NOT offer to create a PR. PRs are only created via explicit `/pr` command.

## Commit Types Reference

| Type | Description | Example |
|------|-------------|---------|
| feat | New feature | `feat(auth): add OAuth support` |
| fix | Bug fix | `fix(api): handle timeout errors` |
| chore | Maintenance | `chore: update dependencies` |
| docs | Documentation | `docs: update API reference` |
| refactor | Code restructure | `refactor(core): extract validation` |
| test | Test changes | `test(auth): add login tests` |
| style | Formatting | `style: fix linting errors` |
| perf | Performance | `perf(db): optimize queries` |

## Safety Rules

- NEVER use `--force` or `--no-verify` unless explicitly requested
- NEVER amend commits that have been pushed
- NEVER commit secrets or credentials
- ALWAYS verify staged changes before committing
- ALWAYS use HEREDOC for multi-line commit messages

## Output

Return:
- Commit hash
- Files changed summary
- Suggested next action
