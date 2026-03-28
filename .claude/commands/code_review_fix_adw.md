---
name: code_review_fix_adw
description: Fix code review issues using ADW orchestrator with domain expert guidance and parallel execution. Routes fixes to appropriate experts, batches by complexity.
argument-hint: [review-file-path]
---

# Code Review Fix ADW

Fix code review issues using the ADW orchestrator with domain expert guidance and parallel execution.

## Variables

REVIEW_PATH: $ARGUMENTS (required - path to code review markdown)
SESSION_ID: adw-fix-{timestamp}

## Instructions

### 1. Initialize ADW Session

```
Session: adw-fix-{YYYYMMDD-HHMMSS}
Directory: adws/sessions/{session_id}/
Logs: logs/adw/{session_id}/workflow.jsonl
```

### 2. Parse Review File

Read the review file and extract:
- All issues from Critical Issues, Concerns, Edge Cases Not Covered
- Complexity tags: `[trivial]`, `[simple]`, `[moderate]`, `[complex]`, `[major]`
- Security Notes (for backlog)
- Suggestions (for backlog)
- Files mentioned in each issue

### 3. Route to Domain Experts

For each issue, identify the domain expert based on files mentioned:

| File Pattern | Expert |
|--------------|--------|
| `src/**/*.rs`, `crates/**/*.rs` | rust |
| `src/**/*.py`, `scripts/**/*.py` | python |
| `src/**/*.ts`, `lib/**/*.ts` | typescript |
| `.claude/hooks/**/*.py`, `adws/**/*.py` | python_tooling |
| Security-related keywords | security_audit |

> **Note:** Update patterns above to match your project structure. See `.claude/commands/experts/` for available experts.

Load each expert's:
- `guidelines` - Apply when fixing
- `validation_commands` - Run after fixes
- `context_files` - Reference as needed

Log expert assignments to `logs/adw/{session_id}/workflow.jsonl`.

### 4. Group Issues by Complexity and Expert

Create batches for parallel execution:

```
{expert_1}:
  trivial_simple: [issue1, issue2, ...]
  moderate: [issue3, issue4, ...]
  complex_major: [issue5, ...]

{expert_2}:
  trivial_simple: [...]
  moderate: [...]
  complex_major: [...]
```

### 5. Execute Fixes with Parallel Batching

#### Trivial & Simple `[trivial]` `[simple]`
- **Batch by expert, max 5 items per haiku agent**
- Include expert guidelines in agent prompt
- Run expert's validation_commands after each batch
- MAX 2 haiku agents concurrent per expert

#### Moderate `[moderate]`
- **Batch 1-2 items per sonnet agent**
- Include expert guidelines and context_files
- Run expert's validation_commands after each fix
- MAX 2 sonnet agents concurrent per expert

#### Complex & Major `[complex]` `[major]`
- **DO NOT IMPLEMENT**
- Create plan using expert context: `project/specs/plan/plan-adw-{issue-slug}.md`
- Include expert's guidelines in plan
- Mark as `📋 PLANNED` in review file

### 6. Agent Prompts

#### Trivial/Simple Batch (haiku) with Expert Context
```
You are fixing code review items as a {expert_name} specialist.

## Expert Guidelines
{expert.guidelines}

## Items to Fix (max 5)
{list items}

For each fix:
1. Follow the expert guidelines above
2. Make minimal, targeted changes
3. Update the review file with ✅ FIXED status
4. Note what you changed

After ALL fixes, run validation:
{expert.validation_commands}
```

#### Moderate Batch (sonnet) with Expert Context
```
You are fixing code review items as a {expert_name} specialist.

## Expert Guidelines
{expert.guidelines}

## Context Files to Reference
{expert.context_files}

## Items to Fix (1-2)
{list items}

For each fix:
1. Understand the issue in context of the domain
2. Follow expert guidelines strictly
3. Add tests if appropriate
4. Update the review file with ✅ FIXED status

After fixes, run validation:
{expert.validation_commands}
```

#### Complex/Major Plan Template
```markdown
---
status: pending
type: fix
complexity: {complex|major}
source: {REVIEW_PATH}
expert: {expert_name}
adw_session: {session_id}
---

# Plan: {Issue Title}

## Problem Statement
{Issue description from review}

## Expert Context
**Domain:** {expert.domain.primary}
**Guidelines:**
{expert.guidelines}

## Proposed Solution
{High-level approach following expert guidelines}

## Files Affected
| File | Changes |
|------|---------|
{files from issue}

## Implementation Steps
1. {Step following expert patterns}
2. ...

## Validation
{expert.validation_commands}

## Test Strategy
{Based on expert domain}
```

### 7. Status Update Format

**EXACT format required:** `✅ FIXED`

Insert BEFORE the complexity tag:

**Before:**
```markdown
1. **Issue description** (`file.rs:100`) - Details. `[simple]`
```

**After:**
```markdown
1. **Issue description** (`file.rs:100`) - Details. ✅ FIXED `[simple]`
```

**Status Values:**
| Status | Meaning |
|--------|---------|
| `✅ FIXED` | Issue resolved |
| `📋 PLANNED` | Plan created for complex/major |
| `⏳ PARTIAL` | Partially addressed |
| `⏭️ DEFERRED` | Skipped (document reason) |
| `❌ BLOCKED` | Cannot fix |

### 8. Run Domain Validation

After all fixes complete, run validation for each affected expert using their configured `validation_commands` from the expert's `expertise.yaml`.

Each expert defines validation commands appropriate for their domain. Execute these for all experts involved in the fixes.

### 9. Update Backlog

Add **Suggestions** and **Security Notes** to `project/BACKLOG.md`:

**Suggestions (from Code Reviews):**
```markdown
| Priority | Item | Source | Complexity |
|----------|------|--------|------------|
| LOW | {suggestion} | {review-date}-adw | `[{complexity}]` |
```

**Security Debt (from Code Reviews):**
```markdown
| Priority | Item | Source | Complexity |
|----------|------|--------|------------|
| {SEVERITY} | {security note} | {review-date}-adw | `[{complexity}]` |
```

### 10. Finalize Session

Update review file header:
```markdown
## ADW Fix Summary
- **Session:** {session_id}
- **Experts Used:** {list of experts}
- **Fixed:** {count}
- **Planned:** {count}
- **Deferred:** {count}
- **Completed:** {date if all done}
```

Save session state to `adws/sessions/{session_id}/state.json`.

## Execution Flow

```
1. Initialize ADW session
2. Parse review file → extract issues
3. Route each issue to domain expert
4. Group by complexity + expert
5. Launch parallel agents with expert context:
   ├── [trivial]+[simple]: batches of ≤5, haiku, expert guidelines
   ├── [moderate]: batches of 1-2, sonnet, expert context
   └── [complex]+[major]: create plans with expert template
6. Each agent: fix → validate → update status
7. Wait for completion
8. Run domain validation commands
9. Update backlog (Suggestions + Security)
10. Finalize session, add completion date if all fixed
```

## Output

```
## Code Review Fix ADW Complete

**Session:** {session_id}
**Review:** {REVIEW_PATH}
**Experts Used:** {expert_1, expert_2, ...}

### Fixed by Expert

**{expert_1} ({count})**
- ✅ Issue 1 `[trivial]`
- ✅ Issue 2 `[simple]`

**{expert_2} ({count})**
- ✅ Issue 3 `[moderate]`

### Planned ({count})
- 📋 Issue 4 → project/specs/plan/plan-adw-{slug}.md
- 📋 Issue 5 → project/specs/plan/plan-adw-{slug}.md

### Validation Results

**{expert_1}:**
{validation command output}

**{expert_2}:**
{validation command output}

### Added to Backlog
**Suggestions:** {count} items
**Security Debt:** {count} items

### Updated Files
- {REVIEW_PATH} - Fix markers added
- project/BACKLOG.md - {n} items added
- project/specs/plan/plan-adw-*.md - {n} plans created
```

## Examples

**Example 1: Fix specific review**
```
/code_review_fix_adw project/code_reviews/2026-01-15-adw-feature-auth.md
```

**Example 2: Fix latest ADW review**
```
/code_review_fix_adw
```
Finds most recent `*-adw-*.md` in `project/code_reviews/`.

**Example 3: Fix any review with expert routing**
```
/code_review_fix_adw project/code_reviews/2026-01-10-api-refactor.md
```
Works with non-ADW reviews too - adds expert routing.
