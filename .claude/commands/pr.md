# Create Pull Request

Create a GitHub pull request for the current branch.

## Variables
args: $ARGUMENTS

## Pre-Submission Requirements

> **All PRs must be code reviewed, built, tested, and checked for linting errors before being submitted.**

Before creating a PR, verify:
1. ✅ **Code Review** - `/code_review_adw` passed with APPROVE verdict
2. ✅ **Build** - `npm run build` (or equivalent) completes without errors
3. ✅ **Tests** - `npm run test` passes (or document skipped tests with reason)
4. ✅ **Lint** - `npm run lint` has no new errors (pre-existing warnings acceptable)

## Instructions

Create a well-formatted PR using GitHub CLI after validating code reviews are complete.

## Workflow

### 1. Check Code Reviews & Fixes

**Find recent code reviews for this branch:**
```bash
ls -la project/code_reviews/*.md 2>/dev/null | tail -5
```

**Check review verdicts:**
- Read any code reviews from today or matching the feature name
- Look for `## Verdict:` line in each review
- **Extract key findings for PR body** (security summary, issues found, issues addressed)

**Blocking conditions** (do NOT create PR):
- Verdict is `REQUEST CHANGES` - must fix issues first
- Review has `### Critical Issues` that are not empty
- Review has unchecked items in `## Testing Recommendations`

**If blocked:**
1. Show the blocking issues from the code review
2. Suggest running `/fix_adw <review-file>` to address them
3. Do NOT proceed with PR creation

**If no code review exists:**
- Warn user: "No code review found. Consider running `/code_review_adw` first."
- Allow PR creation if user confirms (via args `--skip-review`)

**Extract from code review for PR embedding:**
1. **Verdict** - APPROVE or REQUEST CHANGES
2. **Security Summary** - Key security findings or "No concerns"
3. **Key Findings** - Important observations (2-4 bullet points)
4. **Issues Addressed** - If `/fix_adw` was run, what was fixed
5. **Test Recommendations** - For the PR test plan checklist

### 2. Run Pre-Submission Checks

**Run build, test, and lint checks:**

```bash
# Build check
npm run build 2>&1 | tail -20

# Test check (capture exit code)
npm run test 2>&1 | tail -30
TEST_EXIT=$?

# Lint check
npm run lint 2>&1 | tail -30
LINT_EXIT=$?
```

**Evaluate results:**
- **Build**: Must pass with no errors
- **Tests**: Should pass (`$TEST_EXIT` = 0). If tests fail, show failures and ask user to fix or confirm skip with reason.
- **Lint**: Check for new errors vs pre-existing. New errors introduced by this branch should be fixed.

**If checks fail:**
1. Show the failing output
2. Ask user: "Build/test/lint checks failed. Would you like to:"
   - Fix the issues before creating PR (recommended)
   - Skip checks with `--skip-checks` flag (document reason in PR)

**Skip with flag:**
- `--skip-checks`: Bypass build/test/lint (must document reason in PR body)

### 3. Integration Test with Local Server

**For frontend micro-apps, run integration tests against the local dev server:**

```bash
# Kill any existing dev server
kill -9 $(lsof -ti:4038) 2>/dev/null || true
kill -9 $(lsof -ti:8082) 2>/dev/null || true

# Start dev server in background
pnpm start &
DEV_SERVER_PID=$!

# Wait for server to be ready (check webpack port)
echo "Waiting for dev server..."
for i in {1..30}; do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8082 2>/dev/null | grep -q "200\|304"; then
    echo "✅ Dev server ready"
    break
  fi
  sleep 2
done

# Run integration/API tests
pnpm test:integration 2>&1 || true
INTEGRATION_EXIT=$?

# Clean up
kill $DEV_SERVER_PID 2>/dev/null || true
```

**What this validates:**
- App builds and runs correctly
- API integrations work with local overrides
- No runtime errors in the bundled app

**If integration tests fail:**
1. Show the failing output
2. Ask user: "Integration tests failed. Would you like to:"
   - Fix issues before creating PR (recommended)
   - Skip with `--skip-integration` flag (document reason in PR)

**Skip with flag:**
- `--skip-integration`: Bypass integration tests (for non-UI changes)

**Check for integration tests:**
```bash
# Check if test:integration script exists
grep -q '"test:integration"' package.json && echo "✅ Integration tests found" || echo "⚠️ No test:integration script in package.json"

# Check if integration test files exist
ls test/integration/*.test.ts 2>/dev/null && echo "✅ Integration test files found" || echo "⚠️ No integration test files in test/integration/"
```

**If no integration tests exist:**
- Warn user: "⚠️ No integration tests found. Consider adding tests to verify app loads correctly."
- Continue with PR creation (integration tests are recommended but not required)

**Note:** If no `test:integration` script exists, this step shows a warning but continues.

### 4. Check Version Bump

**For feature/release branches, verify version was bumped:**

```bash
# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "unknown")
echo "Current version: $CURRENT_VERSION"

# Check if package.json was modified in this branch
git diff main --name-only 2>/dev/null | grep -q "package.json" && echo "✅ package.json modified" || echo "⚠️ package.json NOT modified"
```

**Version check rules:**
- **Feature branches** (`feature/*`, `feat/*`): Should bump MINOR version
- **Fix branches** (`fix/*`, `bugfix/*`): Should bump PATCH version
- **Release branches** (`release/*`): Must have version bump

**If version not bumped:**
1. Warn user: "Version in package.json has not been bumped. Current: X.Y.Z"
2. Ask: "Would you like to bump the version before creating PR?"
   - Yes: Bump appropriately and commit
   - No: Continue with `--skip-version` flag (document in PR)

**Skip with flag:**
- `--skip-version`: Bypass version check (for non-release changes like docs, CI config)

### 5. Analyze Branch

```bash
git branch --show-current
git log main..HEAD --oneline 2>/dev/null || git log origin/main..HEAD --oneline
git diff main --stat 2>/dev/null || git diff origin/main --stat
```

Identify:
- Branch name
- All commits (not just latest!)
- Files changed
- Base branch (usually main)

### 6. Ensure Pushed

```bash
git status
```

If commits not pushed:
- Push first: `git push -u origin $(git branch --show-current)`

### 7. Generate PR Content

Analyze ALL commits on the branch to create:

**Title**: Conventional format matching primary change
- `feat(scope): description`
- `fix(scope): description`

**Body**:
```markdown
## Summary
<1-3 bullet points covering ALL commits>

## Changes
<List of key changes from all commits>

## Code Review Summary
<If code review exists, embed the actual findings - don't just link to a file path that doesn't exist in the target repo>

**Verdict:** <APPROVE/REQUEST CHANGES>

### Security
<Summarize security review findings, or "No security concerns identified">

### Key Findings
<Bullet list of important review observations>
- <Finding 1>
- <Finding 2>

### Issues Addressed
<If fixes were made after review, list them>
- <Issue fixed>

## Test Plan
- [ ] <Testing checklist from code review, if available>
- [ ] <Additional testing items>

---
🤖 Generated with [Claude Code](https://claude.ai/code)
```

**Important:** The code review file lives in the ADW project workspace, not in the target repository. Always embed the review summary content directly in the PR rather than linking to a file path that reviewers cannot access.

### 8. Create PR

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

Optional flags from args:
- `--draft`: Create as draft
- `--reviewer <user>`: Request review
- `--label <label>`: Add label

### 9. Report Results

Report:
- PR URL
- PR number
- Reviewers assigned

## Arguments

- No args: Create PR to main
- `--draft`: Create draft PR
- `--base <branch>`: Target branch (default: main)
- `--skip-review`: Skip code review check (not recommended)
- `--skip-checks`: Skip build/test/lint checks (must document reason)
- `--skip-version`: Skip version bump check (for docs, CI config changes)
- `--skip-integration`: Skip integration tests with local server
- `<title>`: Override auto-generated title

## Output

Return the PR URL so user can view it.
