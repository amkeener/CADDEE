---
name: e2e_adw
description: End-to-end feature development with automatic research, planning, implementation, review, and fixes. Asks clarifying questions upfront and can pause for user input.
argument-hint: <feature description or issue>
---

# End-to-End ADW

Complete feature development workflow that combines research, planning, building, review, and fixes into a seamless process with intelligent pause points for user input.

## Variables

PROMPT: $ARGUMENTS
SESSION_ID: adw-e2e-{timestamp}

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     E2E ADW WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. INTAKE          Parse task, identify scope              │
│       │                                                     │
│       ▼                                                     │
│  2. CLARIFY         Ask questions if ambiguous   ◄─ PAUSE   │
│       │                                                     │
│       ▼                                                     │
│  3. RESEARCH        Optional: gather context     (skip if   │
│       │             from codebase & web          clear)     │
│       ▼                                                     │
│  4. PLAN            Create implementation plan              │
│       │                                                     │
│       ▼                                                     │
│  5. APPROVE         Present plan for approval    ◄─ PAUSE   │
│       │                                                     │
│       ▼                                                     │
│  6. BUILD           Implement the plan                      │
│       │                                                     │
│       ▼                                                     │
│  7. VALIDATE        Run expert validation commands          │
│       │                                                     │
│       ▼                                                     │
│  8. REVIEW          Multi-expert code review                │
│       │                                                     │
│       ▼                                                     │
│  9. FIX             Auto-fix trivial/simple issues          │
│       │                                                     │
│       ▼                                                     │
│  10. COMPLETE       Commit, summarize, next steps           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Instructions

### Phase 1: INTAKE

Initialize session and analyze the task:

```
Session: adw-e2e-{YYYYMMDD-HHMMSS}
Directory: adws/sessions/{session_id}/
State: adws/sessions/{session_id}/state.json
```

Parse PROMPT to extract:
- **Task type**: feature, bug, chore, refactor
- **Complexity estimate**: trivial, simple, moderate, complex, major
- **Affected domains**: Based on file patterns and expert routing
- **Ambiguity level**: clear, needs_clarification, highly_ambiguous

Route to domain expert using standard ADW routing:
| Pattern | Expert |
|---------|--------|
| `src/**/*.rs`, `crates/**/*.rs` | rust |
| `src/**/*.py`, `scripts/**/*.py` | python |
| `src/**/*.ts`, `lib/**/*.ts` | typescript |
| Security keywords | security_audit |
| `.claude/**/*.py` | python_tooling |

> **Note:** Update patterns above to match your project structure. See `.claude/commands/experts/` for available experts.

Save initial state:
```json
{
  "session_id": "{session_id}",
  "workflow": "e2e",
  "phase": "intake",
  "prompt": "{PROMPT}",
  "expert": "{routed_expert}",
  "task_type": "{type}",
  "complexity": "{complexity}",
  "created_at": "{timestamp}"
}
```

### Phase 2: CLARIFY (Pause Point)

**If ambiguity_level != "clear":**

Use AskUserQuestion tool to gather clarifications BEFORE proceeding:

```
Questions to consider:
- Scope: Is this limited to X or should it include Y?
- Approach: Should we use library A or implement from scratch?
- Priority: Focus on speed, maintainability, or extensibility?
- Dependencies: Should this integrate with existing system Z?
- Testing: Unit tests only or include integration tests?
```

**Question Guidelines:**
- Ask 1-4 questions max
- Group related questions
- Provide sensible defaults as first option
- Wait for user response before proceeding

**If PROMPT is clear:**
- Skip to Phase 3 or 4
- Log: "Prompt clear, skipping clarification phase"

### Phase 3: RESEARCH (Optional)

**Skip if:**
- Task is trivial/simple
- Domain is well-understood
- User provided sufficient context

**Execute if:**
- New technology or pattern needed
- Cross-domain interactions
- User explicitly requests research

If research is needed, invoke `/research_adw {PROMPT}`:
- Follow expert-guided search patterns
- Gather codebase context
- Identify existing patterns
- Generate 2-3 approaches

Save research output to `project/research/{session_id}.md`

Update state:
```json
{
  "phase": "research_complete",
  "research_path": "project/research/{session_id}.md",
  "approaches": ["{approach1}", "{approach2}"]
}
```

### Phase 4: PLAN

Invoke `/plan_adw {PROMPT}` with accumulated context:
- Include research findings if Phase 3 ran
- Include user clarifications from Phase 2
- Apply expert guidelines

Generate plan at: `project/specs/plan/plan-adw-e2e-{descriptive-name}.md`

**Plan must include:**
- Clear objective
- Step-by-step tasks
- Files to modify/create
- Validation commands
- Acceptance criteria

Update state:
```json
{
  "phase": "plan_complete",
  "plan_path": "project/specs/plan/plan-adw-e2e-{name}.md"
}
```

### Phase 5: APPROVE (Pause Point)

**Present plan summary to user:**

```markdown
## E2E Plan Ready for Approval

**Task:** {PROMPT}
**Expert:** {expert}
**Complexity:** {complexity}

### Summary
{2-3 sentence overview}

### Key Changes
- {file1}: {what changes}
- {file2}: {what changes}

### Approach
{Brief description of approach}

### Questions/Risks
{Any remaining uncertainties}

Approve this plan to proceed with implementation?
```

**Use AskUserQuestion:**
- Option 1: "Approve and build" (recommended)
- Option 2: "Modify plan first"
- Option 3: "Cancel"

**If user selects "Modify":**
- Ask what changes are needed
- Update plan accordingly
- Re-present for approval

**Do NOT proceed to Phase 6 without explicit approval.**

### Phase 6: BUILD

Invoke `/build_adw {plan_path}`:
- Load expert context
- Execute each step sequentially
- Log progress to state.json

For each step:
1. Mark `in_progress`
2. Execute changes
3. Mark `completed`
4. Run incremental validation if applicable

Update state after each step:
```json
{
  "phase": "building",
  "current_step": 3,
  "total_steps": 7,
  "completed_steps": ["step1", "step2"]
}
```

### Phase 7: VALIDATE

Run expert's `validation_commands` from the assigned expert's `expertise.yaml`.

Each expert defines validation commands appropriate for their domain. Execute these based on the routed expert.

**If validation fails:**
- Attempt auto-fix for common issues
- Re-run validation
- If still failing, pause and ask user

Update state:
```json
{
  "phase": "validated",
  "validation_results": {
    "passed": true,
    "warnings": 2,
    "errors": 0
  }
}
```

### Phase 8: REVIEW

Invoke `/code_review_adw 1` (review changes since build started):
- Security-first analysis with security_audit expert
- Domain expert review
- Generate review report

Save to: `project/code_reviews/{YYYY-MM-DD}-e2e-{feature}.md`

Update state:
```json
{
  "phase": "reviewed",
  "review_path": "project/code_reviews/{date}-e2e-{feature}.md",
  "verdict": "APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION"
}
```

### Phase 9: FIX

**If review verdict is not APPROVE:**

Invoke `/code_review_fix_adw {review_path}`:
- Auto-fix `[trivial]` and `[simple]` issues
- Create plans for `[moderate]`, `[complex]`, `[major]` issues
- Update review with fix status

**Fix Priority:**
1. Critical/Security issues - MUST fix
2. High concerns - Should fix
3. Medium concerns - Should fix if time
4. Suggestions - Add to backlog

**If complex issues remain:**
- Log them to backlog
- Continue to completion
- Note in summary

Update state:
```json
{
  "phase": "fixes_applied",
  "fixed_count": 5,
  "planned_count": 2,
  "deferred_count": 1
}
```

### Phase 10: COMPLETE

**Summarize and wrap up:**

1. **Update tracking:**
   - Move plan to `project/specs/plan/completed/`
   - Update BACKLOG.md if applicable
   - Log session metrics

2. **Generate completion summary:**

```markdown
## E2E ADW Complete

**Session:** {session_id}
**Task:** {PROMPT}
**Expert:** {expert}
**Duration:** {start_time} → {end_time}

### Phases Completed
- [x] Intake: Task analyzed
- [x] Clarify: {N} questions answered
- [x] Research: {Yes/Skipped}
- [x] Plan: {plan_path}
- [x] Build: {N} steps completed
- [x] Validate: {passed/failed}
- [x] Review: {verdict}
- [x] Fix: {N} issues fixed

### Changes
{git diff --stat}

### Validation Results
{Final validation output}

### Review Summary
{Brief review outcome}

### Remaining Work
- {Any deferred items}
- {Complex issues planned but not built}

### Next Steps
- [ ] Manual testing
- [ ] Deploy to testnet
- [ ] /commit to save changes
```

3. **Ask if user wants to commit:**

Use AskUserQuestion:
- Option 1: "Commit changes" (recommended)
- Option 2: "Review changes first"
- Option 3: "Don't commit yet"

## State Transitions

```
INTAKE → CLARIFY (if ambiguous) → RESEARCH (if needed) → PLAN →
APPROVE → BUILD → VALIDATE → REVIEW → FIX (if needed) → COMPLETE
```

**Pause Points (requires user input):**
- CLARIFY: Ask clarifying questions
- APPROVE: Get plan approval
- COMPLETE: Ask about committing

**Auto-resume Points:**
- After clarification answers
- After plan approval
- After fix decisions

## Error Handling

**Build Failure:**
```
1. Log error details
2. Attempt auto-fix for common issues
3. If unresolvable, pause and ask user
4. Option to skip step or abort workflow
```

**Validation Failure:**
```
1. Show failure output
2. Attempt auto-fix
3. If persistent, ask user:
   - Fix manually and continue
   - Skip validation (not recommended)
   - Abort workflow
```

**Review Rejection (REQUEST_CHANGES):**
```
1. Auto-fix trivial/simple issues
2. Plan complex issues
3. Re-run validation
4. Continue to completion with notes
```

## Session Recovery

If session is interrupted, can be resumed:

```bash
# Check for incomplete sessions
ls adws/sessions/adw-e2e-*/state.json | xargs grep '"phase":' | grep -v '"complete"'

# Resume specific session
/e2e_adw --resume {session_id}
```

State file tracks:
- Current phase
- Completed steps
- User decisions
- File paths

## Examples

### Example 1: Simple Feature
```
/e2e_adw Add a refresh button to the transaction list
```
Flow: INTAKE → PLAN → APPROVE → BUILD → VALIDATE → REVIEW → COMPLETE
(Skips CLARIFY and RESEARCH for simple, clear task)

### Example 2: Complex Feature
```
/e2e_adw Implement multi-signature wallet support
```
Flow: INTAKE → CLARIFY (ask about signature schemes) → RESEARCH → PLAN → APPROVE → BUILD → VALIDATE → REVIEW → FIX → COMPLETE

### Example 3: Bug Fix
```
/e2e_adw Fix the balance not updating after send transaction
```
Flow: INTAKE → RESEARCH (find root cause) → PLAN → APPROVE → BUILD → VALIDATE → REVIEW → COMPLETE

## Output

Final output summarizes the entire workflow:

```
## E2E Workflow Complete

Session: adw-e2e-20260115-141500
Duration: 45 minutes
Expert: {expert}

✅ Plan: project/specs/plan/completed/plan-adw-e2e-refresh-button.md
✅ Review: project/code_reviews/2026-01-15-e2e-refresh-button.md
✅ Changes: 3 files modified, 45 lines added

Ready to commit? Use /commit to save changes.
```
