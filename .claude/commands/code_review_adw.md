---
name: code_review_adw
description: Code review using the ADW orchestrator with multi-expert security-first analysis. Always includes security_audit expert.
argument-hint: [scope - number of commits, default 1]
---

# Code Review ADW

Review changes using the ADW orchestrator with security-first multi-expert analysis.

## Variables

SCOPE: $1 (optional, default: 1 - number of commits to review)
SESSION_ID: adw-review-{timestamp}

## Instructions

### 1. Initialize ADW Session

```
Session: adw-review-{YYYYMMDD-HHMMSS}
Logs: logs/adw/{session_id}/workflow.jsonl
```

### 2. Gather Changes

Run diff analysis:
```bash
git diff HEAD~{SCOPE}
git diff HEAD~{SCOPE} --stat
git log -n {SCOPE} --oneline
```

Identify affected files and categorize by domain based on expert file_patterns.

### 3. Security Review (Always First)

Load `.claude/commands/experts/security_audit/expertise.yaml` and apply its `audit_checklist`:

**Input Validation:**
- [ ] All user inputs validated at entry points
- [ ] Numeric bounds checked before operations
- [ ] String lengths and formats validated

**Authentication:**
- [ ] Signature verification before state changes
- [ ] Session validation for protected operations

**Authorization:**
- [ ] Access control on sensitive operations
- [ ] Permission checks enforced

**Cryptography:**
- [ ] Constant-time comparisons for secrets
- [ ] Proper key derivation
- [ ] Secure random number generation

**State Safety:**
- [ ] Reentrancy guards where needed
- [ ] Atomic state updates

Log security findings with severity levels:
- `critical`: Immediate security compromise
- `high`: Significant security weakness
- `medium`: Potential security issue
- `low`: Minor security consideration

### 3.5 Static Analysis (Always Run)

Run linting and type checks on changed files:

```bash
# ESLint (project-specific command)
pnpm lint:check  # or npm run lint

# TypeScript compilation check
tsc --noEmit

# Prettier format check
pnpm format:check  # or prettier --check .
```

**Blocking Issues:**
- ESLint errors → REQUEST CHANGES (must fix)
- TypeScript errors → REQUEST CHANGES (must fix)
- Prettier issues → Note in report (not blocking)

Log static analysis findings:
```json
{"event_type": "static_analysis", "eslint_errors": 0, "ts_errors": 0, "prettier_issues": 2}
```

### 4. Test Coverage Validation

**Run test suite and check coverage:**

```bash
# Python projects
pytest --cov=app --cov-report=term-missing

# TypeScript/Node projects
pnpm test:coverage
# or
pnpm test:acceptance
```

**Coverage Thresholds:**
- Overall: ≥70%
- Changed files: ≥80%
- New files: ≥90%

**Coverage Report:**
| File | Statements | Branches | Functions | Lines |
|------|------------|----------|-----------|-------|
| {file} | {%} | {%} | {%} | {%} |

**ATDD Compliance (if test files changed):**
- [ ] Tests follow Given/When/Then structure
- [ ] Test fixtures properly set up/torn down
- [ ] Edge cases covered
### 5. Domain Expert Review

For each affected domain:

1. **Load expert YAML** from `.claude/commands/experts/{expert}/expertise.yaml`
2. **Run validation_commands** (MANDATORY - blocking if they fail)
3. **Review against guidelines** - code quality per expert guidelines
4. **Check patterns** - ensure conventions are followed
5. **Verify error handling** - follows domain best practices

### 6. Generate Report

Create review at: `project/code_reviews/{YYYY-MM-DD}-adw-{feature}.md`

**Report Format:**
```markdown
## Summary
{1-2 sentences on what the changes do}

## Verdict: {APPROVE | REQUEST CHANGES | NEEDS DISCUSSION}

## ADW Review Metadata
- Session: {session_id}
- Experts: {list of experts used}
- Scope: {SCOPE} commit(s)
## Static Analysis

| Check | Status | Issues |
|-------|--------|--------|
| ESLint/Ruff | {PASS/FAIL} | {count} |
| TypeScript/mypy | {PASS/FAIL} | {count} |
| Prettier/black | {PASS/WARN} | {count} |

{Details of any failures}

## Test Coverage

| Metric | Coverage | Threshold | Status |
|--------|----------|-----------|--------|
| Statements | {%} | 70% | {PASS/FAIL} |
| Branches | {%} | 70% | {PASS/FAIL} |
| Functions | {%} | 70% | {PASS/FAIL} |

### Changed File Coverage
| File | Coverage | Status |
|------|----------|--------|
| {file} | {%} | {PASS/FAIL} |

## Security Review (security_audit)

### Critical Issues
{Numbered list or "None"}

### High Risk
{Numbered list or "None"}

### Medium Risk
{Numbered list or "None"}

### Low Risk
{Numbered list or "None"}

## Domain Review ({domain_expert})

### Validation Commands
{Output from expert validation_commands or "All passed"}

### Critical Issues (must fix)
{Numbered list with complexity tags or "None"}

### Concerns (should fix)
{Numbered list with complexity tags or "None"}

### Suggestions (nice to have)
{Numbered list with complexity tags or "None"}

## Edge Cases Not Covered
{Numbered list or "None"}

## What's Good
{1-2 things done well}
```

**Complexity Tags:**
| Tag | Meaning | Effort |
|-----|---------|--------|
| `[trivial]` | One-liner fix | < 5 min |
| `[simple]` | Small change | 5-30 min |
| `[moderate]` | Multiple files | 30 min - 2 hrs |
| `[complex]` | Significant changes | 2-8 hrs |
| `[major]` | Architecture change | 1+ days |

### 7. Finalize Session

Save session state and log completion.

## Output

Return the path to the review file:
```
project/code_reviews/{YYYY-MM-DD}-adw-{feature}.md
```

## Examples

**Example 1: Review last commit**
```
/code_review_adw
```
Reviews HEAD~1, security-first analysis.

**Example 2: Review last 3 commits**
```
/code_review_adw 3
```
Reviews HEAD~3 with multi-expert analysis.
