---
name: build_adw
description: Implement a plan using the ADW orchestrator with domain expert guidance. Tracks progress via Tasks.
argument-hint: [plan-path]
---

# Build ADW

Implement a plan using the ADW orchestrator with domain expert guidance. Supports ATDD test-first development with Task-based progress tracking.

## Variables

PLAN_PATH: $ARGUMENTS
SESSION_ID: adw-build-{timestamp}

## Task Integration

Build ADW consumes Tasks created by `/plan_adw` or `/atdd_adw`:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILD TASK FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TaskList → Find pending tasks → Claim task → Execute → Complete│
│       ↓            ↓                 ↓           ↓         ↓    │
│  [View all]  [Filter by plan]  [Set owner]  [Do work]  [Update] │
│                                                                 │
│  Dependency Resolution:                                         │
│  - Tasks auto-unblock when blockers complete                    │
│  - Parallel execution for independent tasks                     │
│  - Sequential for dependent tasks                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Instructions

### 1. Load Plan and Tasks

Read the plan from PLAN_PATH (or search in `project/specs/plan/` if just a name):
- Extract implementation steps
- Identify the expert used during planning (from frontmatter `expert:`)
- **Check for `atdd: true` flag** in frontmatter
- **Check for `task_ids:` field** for existing tasks
- Get the original task description

If plan status is not `approved`, warn and ask for confirmation.

**Check for existing Tasks:**
```
TaskList  # View all tasks

# Filter for tasks related to this plan
# Look for tasks with metadata.plan_path matching PLAN_PATH
```

**If tasks exist from planning phase:**
- Resume from pending tasks
- Skip completed tasks
- Report current progress

**If no tasks exist (legacy plan):**
- Create tasks from "Step by Step Tasks" section
- See Section 4.5 for task creation

### 2. Initialize ADW Session

```
Session: adw-build-{YYYYMMDD-HHMMSS}
Link to planning session if exists (from plan's adw_session field)
```

Load the same expert used during planning for consistency.

### 3. Load Expert Context

Read expert YAML from `.claude/commands/experts/{expert}/expertise.yaml`:
- Load `guidelines` for implementation rules
- Load `validation_commands` for verification
- Load `context_files` for reference

Apply expert context to all implementation work.

### 4. Execute Implementation Steps

**Get pending tasks and execute:**

```
TaskList  # Get current task state

# Find next executable task (pending, not blocked)
# Priority: tasks with no blockedBy, or all blockers completed
```

**If plan has `atdd: true` flag, use ATDD phases:**

#### ATDD Phase 1: RED (Scaffold & Fail)

**Claim and execute scaffold tasks:**
```
# For each scaffold task
TaskGet: {task_id}  # Get full details

TaskUpdate:
  taskId: {task_id}
  status: "in_progress"
  owner: "build_adw"
```

1. **Create Test Files**
   - Write test cases from acceptance criteria
   - Use Given/When/Then structure
   - For Python: pytest fixtures and test functions
   - For TypeScript: Jest describe/test blocks with DSL

2. **Run Tests (Expect RED)**
   ```bash
   # Python
   pytest tests/acceptance/ -v

   # TypeScript
   pnpm test:acceptance
   ```
   - Tests SHOULD fail at this point
   - Log: `RED phase complete - X tests failing as expected`

3. **Complete scaffold tasks:**
   ```
   TaskUpdate:
     taskId: {task_id}
     status: "completed"

   # This auto-unblocks GREEN phase tasks
   ```

#### ATDD Phase 2: GREEN (Implement Until Pass)

**Claim GREEN phase tasks (now unblocked):**
```
TaskList  # GREEN tasks should now be unblocked

TaskUpdate:
  taskId: {green_task_id}
  status: "in_progress"
  owner: "build_adw"
```

**Goal:** Make tests PASS with minimal implementation

1. **Implement Business Logic**
   - Focus on making tests pass, not perfection
   - Follow expert guidelines

2. **Run Tests After Each Change**
   - Track progress: `X of Y tests passing`
   - Continue until ALL tests pass

3. **Final GREEN Check**
   - All tests passing
   - No regressions in existing tests

4. **Complete GREEN tasks:**
   ```
   TaskUpdate:
     taskId: {green_task_id}
     status: "completed"

   # This auto-unblocks REFACTOR phase tasks
   ```

#### ATDD Phase 3: REFACTOR (Improve Quality)

**Claim REFACTOR tasks:**
```
TaskUpdate:
  taskId: {refactor_task_id}
  status: "in_progress"
  owner: "build_adw"
```

**Goal:** Clean up without breaking tests

1. **Code Quality Improvements**
   - Extract common patterns
   - Improve naming and documentation
   - Apply expert guidelines

2. **Final Validation**
   - Run full test suite
   - Run linting/type checks

3. **Complete REFACTOR tasks:**
   ```
   TaskUpdate:
     taskId: {refactor_task_id}
     status: "completed"

   # This unblocks Review task
   ```

**For standard (non-ATDD) plans:**

For each step in the plan's "Step by Step Tasks":

1. **Claim Task**
   ```
   TaskUpdate:
     taskId: {step_task_id}
     status: "in_progress"
     owner: "build_adw"
   ```

2. **Execute**
   - Follow expert guidelines
   - Create/modify files as specified

3. **Complete Task**
   ```
   TaskUpdate:
     taskId: {step_task_id}
     status: "completed"
   ```

### 4.5. Create Tasks (Legacy Plans)

**If plan has no task_ids, create tasks from steps:**

```
# For each step in "Step by Step Tasks"
TaskCreate:
  subject: "Step {n}: {step_description}"
  description: "{full step details}"
  activeForm: "{action in progress tense}"
  metadata:
    plan_path: "{PLAN_PATH}"
    step_number: {n}

# Set up dependencies
TaskUpdate:
  taskId: {step_2_id}
  addBlockedBy: [{step_1_id}]
```

### 5. Validate Changes (MANDATORY)

> **CRITICAL**: You MUST run ALL validation commands AND coding standards checks. Do NOT skip this step.
> If validation fails, you MUST fix the issues before proceeding.

**Run the expert's `validation_commands` from expertise.yaml**

**Validation Rules:**
1. Run EVERY command in the expert's `validation_commands` list
2. If ANY command fails → STOP and fix before continuing
3. Do NOT mark build as complete until ALL validations pass
4. Report validation output in the build summary

#### 5.1 Coding Standards Check (MANDATORY)

**If the expert has a `coding_standards` field**, read each referenced coding standards file and verify all changed code complies:

1. Read each file listed in the expert's `coding_standards` array (e.g., `project/coding-standards/python.md`)
2. Review ALL changed/created files against the standards
3. Check for violations — common issues:
   - **Python:** missing `from __future__ import annotations`, using `os.path` instead of `pathlib`, printing to stdout, missing type hints on public functions, using TypedDict/Pydantic instead of dataclasses
   - **TypeScript:** using `any` without justification, CSS files instead of inline styles, class components, missing `type` keyword on type-only imports, direct IPC calls from renderer
   - **IPC:** message types not added to both `messages.py` and `messages.ts`, missing union type entries, missing handler in `main.py`
4. If violations found → fix them before proceeding
5. Report compliance status in build summary

**Check for TODO comments:**
- Pattern: `// TODO: <description>` or `# TODO: <description>`
- List any incomplete work
- TODOs are acceptable but MUST be reported

### 6. Update Tracking

1. **Update Plan Status**
   ```markdown
   status: done  # Changed from approved
   ```

2. **Move Plan to Completed Folder**
   ```bash
   mv project/specs/plan/<plan-file>.md project/specs/plan/completed/
   ```

### 7. Finalize Session

Save final state:
```json
{
  "session_id": "{session_id}",
  "workflow_type": "build",
  "status": "completed",
  "expert_used": "{expert}",
  "plan_path": "{PLAN_PATH}",
  "atdd_mode": true|false,
}
```

## Output

**Show final task state:**
```
TaskList  # Display all tasks with final status
```

Summarize completed work:
```
## Build Complete

**Session:** {session_id}
**Expert:** {expert}
**Plan:** {PLAN_PATH}
**Mode:** {ATDD Test-First | Standard}

### Task Summary
| ID | Task | Phase | Status |
|----|------|-------|--------|
| {id} | {subject} | {phase} | completed |
| {id} | {subject} | {phase} | completed |
| {id} | Review: Code review | review | pending (unblocked) |

**Completed:** {X} tasks
**Pending:** {Y} tasks (review phase)

### ATDD Summary (if applicable)
| Phase | Status | Tasks |
|-------|--------|-------|
| RED | Complete - {X} tests scaffolded | {count} completed |
| GREEN | Complete - {X}/{Y} tests passing | {count} completed |
| REFACTOR | Complete | {count} completed |

### Changes
{git diff --stat output}

### Validation Results
{Output from validation_commands}

### TODO Items (if any)
- {Any TODO comments found}

### Next Steps
- Review task is now unblocked
- Run `/code_review_adw` to validate changes
- Or resume later - tasks persist across sessions
```

## Examples

**Example 1: Build from plan path**
```
/build_adw project/specs/plan/plan-adw-rate-limiting.md
```

**Example 2: Build from plan name**
```
/build_adw plan-adw-biometric-auth
```
Searches `project/specs/plan/` for matching file.
