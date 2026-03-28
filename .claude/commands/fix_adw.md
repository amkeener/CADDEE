---
name: fix_adw
description: Fix review issues using the ADW orchestrator with domain expert guidance. Processes issues by priority and complexity.
argument-hint: [review-path]
---

# Fix ADW

Fix issues identified in a code review using ADW with expert guidance.

## Variables

REVIEW_PATH: $ARGUMENTS
SESSION_ID: adw-fix-{timestamp}

## Instructions

### 1. Load Review

Read the review from REVIEW_PATH (or search in `project/code_reviews/` if just a date):
- Parse all issues by severity (critical, high, medium, low)
- Extract complexity tags from each issue
- Identify the experts used in the review

### 2. Initialize ADW Session

```
Session: adw-fix-{YYYYMMDD-HHMMSS}
Link to review session
```

### 3. Prioritize Issues

Order by fix priority:
1. **Critical** - Fix immediately
2. **High** - Fix in this session
3. **Medium** - Fix if time permits
4. **Low** - Consider for later

Within each severity, order by complexity (trivial first).

### 4. Execute Fixes

For each issue:

1. **Analyze Issue**
   - Understand the problem
   - Load relevant expert for guidance

2. **Plan Fix**
   - For trivial/simple: mental plan
   - For moderate+: brief written plan

3. **Implement Fix**
   - Follow expert guidelines
   - Make minimal changes to fix the issue

4. **Validate Fix**
   - Run expert's validation_commands
   - Ensure no regressions

5. **Log Completion**
   - Mark issue as resolved
   - Record time spent

### 5. Handle Deferrals

If an issue cannot be fixed in this session:
- Add to project backlog with context
- Note why it was deferred
- Link back to review

### 6. Update Review

Mark fixed issues in the original review:
```markdown
### Critical Issues
1. ~~Issue description~~ [FIXED in {commit}]
```

### 7. Finalize Session

Generate summary:
```markdown
## Fix Summary

**Session:** {session_id}
**Review:** {REVIEW_PATH}

### Fixed
- {issue 1} [trivial]
- {issue 2} [simple]

### Deferred
- {issue 3} [complex] - Added to backlog

### Validation
{validation command output}
```

## Output

Return:
- Number of issues fixed
- Number of issues deferred
- Path to updated review

## Examples

**Example 1: Fix from review path**
```
/fix_adw project/code_reviews/2024-01-15-adw-auth-flow.md
```

**Example 2: Fix from date**
```
/fix_adw 2024-01-15
```
Finds most recent review from that date.
