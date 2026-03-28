---
name: plan_adw
description: Create an implementation plan using the ADW orchestrator with domain expert routing. Supports ATDD mode and Task dependency tracking.
argument-hint: [task-description] [--atdd]
---

# Plan ADW

Create an implementation plan using the ADW orchestrator with automatic domain expert routing. Supports ATDD workflow integration and Task-based progress tracking.

## Variables

PROMPT: $ARGUMENTS (task description or flags)
SESSION_ID: adw-plan-{timestamp}

## Task Integration

This workflow uses Claude Code's Task system for:
- **Progress tracking**: Each plan step becomes a trackable task
- **Dependencies**: Steps can block/be blocked by other steps
- **Resume capability**: Tasks persist across sessions
- **Parallel execution**: Independent steps can run concurrently

## Arguments

- `--atdd`: Generate ATDD-specific plan with test scaffolding phases
- No flags: Standard planning workflow

## Instructions

### 1. Initialize ADW Session

Generate a unique session ID and initialize the orchestrator:

```
Session: adw-plan-{YYYYMMDD-HHMMSS}
Directory: adws/sessions/{session_id}/
Logs: logs/adw/{session_id}/workflow.jsonl
```

### 1.5. Parse Arguments

**If `--atdd` flag present:**
- Plan will include ATDD scaffolding phases (RED/GREEN/REFACTOR)
- Output will include test file locations
- Validation will include test commands

### 2. Analyze Task & Route to Expert

Parse the PROMPT to identify:
- Primary domain (use file patterns and keywords from experts)
- Files likely to be affected (use Glob to find related files)
- Task type (feature, bug, chore, refactor)
- **Project context** (frontend, backend, which subproject)

**Expert Routing Logic:**
| Pattern | Expert |
|---------|--------|
| Matches expert file_patterns | Route to that expert |
| Matches expert keywords | Route to that expert |
| Keywords: security, audit, vulnerability | security_audit |
| Keywords: test, atdd, acceptance | testing |
| No match | research (for exploration) |

Read the selected expert's YAML from `.claude/commands/experts/{expert}/expertise.yaml` and apply its:
- Guidelines
- Context files
- Validation commands
- **ATDD context** (if atdd mode and expert has atdd_context)

### 3. Research Codebase

Using the expert's `context_files`, gather relevant context:
1. Read each context file
2. Search for related patterns using Glob/Grep
3. Build context document at `adws/sessions/{session_id}/context.md`

Log expert selection to `logs/adw/{session_id}/workflow.jsonl`:
```json
{"event_type": "expert_selected", "expert": "{expert}", "reason": "..."}
```

### 4. Design Solution

Apply the expert's domain knowledge to design the solution:
- Consider the expert's `capabilities`
- Follow the expert's `guidelines`
- Reference any domain-specific context files

### 5. Create Plan

**Standard Plan Path:** `project/specs/plan/plan-adw-{descriptive-name}.md`
**ATDD Plan Path:** `project/specs/plan/plan-atdd-{issue-id-or-name}.md`

**Plan Format:**
```markdown
---
status: approved
type: {feature|bug|chore|refactor}
complexity: {trivial|simple|moderate|complex|major}
adw_session: {session_id}
expert: {expert_name}
atdd: {true if ATDD mode, otherwise omit}
---

# Plan: {Title}

## Task Description
{PROMPT}

## Expert Context
{Expert name and why it was selected}

## Objective
{Clear goal statement}

## Relevant Files
### To Read (for context)
- {file paths}

### To Modify
- {file paths}

### To Create
- {file paths}

## Implementation Phases

{For ATDD mode, use these phases:}

### Phase 1: Scaffold (RED)
- Create test files that define expected behavior
- Tests should FAIL at this point

### Phase 2: Implement (GREEN)
- Implement minimum code to make tests pass
- Focus on correctness, not elegance

### Phase 3: Refactor
- Clean up code while keeping tests passing
- Extract common patterns

{For standard mode:}
{Break into logical phases}

## Step by Step Tasks
1. {First task}
2. {Second task}
...

## Testing Strategy
{How to test the changes}

{For ATDD mode, include test file locations:}
### Test Files
- Test: `{test file path}`
- Fixtures/DSL: `{fixture/DSL path}`

## Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}

## Validation Commands
{From expert's validation_commands}
```

### 6. Create Tasks from Plan Steps

**Convert plan steps to Tasks with dependencies for build phase:**

For each step in "Step by Step Tasks", create a Task:

```
TaskCreate:
  subject: "{Step description}"
  description: |
    Plan: {plan_path}
    Step: {step_number}
    Expert: {expert}

    {Full step details from plan}
  activeForm: "{Present tense action, e.g., 'Implementing feature X'}"
  metadata:
    plan_path: "{plan_path}"
    step_number: {n}
    expert: "{expert}"
    phase: "{scaffold|implement|refactor}"
```

**For ATDD plans, create phased tasks with dependencies:**

```
Phase 1 Tasks (RED - no dependencies):
  TaskCreate: "Scaffold test files"
  TaskCreate: "Create DSL layer"
  TaskCreate: "Create protocol drivers"

Phase 2 Tasks (GREEN - blocked by Phase 1):
  TaskCreate: "Implement business logic"
    blockedBy: [scaffold-task-ids]
  TaskCreate: "Make tests pass"
    blockedBy: [implement-task-id]

Phase 3 Tasks (REFACTOR - blocked by Phase 2):
  TaskCreate: "Refactor and cleanup"
    blockedBy: [green-task-ids]
```

**Store task IDs in plan metadata:**
```yaml
---
# Add to frontmatter after task creation
task_ids:
  scaffold: ["task-id-1", "task-id-2"]
  implement: ["task-id-3"]
  refactor: ["task-id-4"]
---
```

### 7. Update State & Log

Save session state to `adws/sessions/{session_id}/state.json`:
```json
{
  "session_id": "{session_id}",
  "workflow_type": "plan",
  "status": "completed",
  "expert_used": "{expert}",
  "plan_path": "project/specs/plan/plan-adw-{name}.md",
  "tasks_created": ["task-id-1", "task-id-2", ...]
}
```

Log workflow completion.

### 8. Output Task Summary

After creating tasks, output summary:
```
TaskList  # Show all created tasks with dependencies
```

## Output

Return the plan path and task summary:
```
## Plan Created

**Plan:** project/specs/plan/plan-adw-{descriptive-name}.md
**Expert:** {expert}
**Tasks Created:** {count}

### Task Breakdown
| ID | Task | Phase | Blocked By |
|----|------|-------|------------|
| {id} | {subject} | {phase} | {deps} |

### Next Steps
1. Review plan and tasks
2. Run `/build_adw {plan_path}` to execute
3. Tasks will auto-progress through phases
```

## Examples

**Example 1: Standard planning**
```
/plan_adw Add rate limiting to API endpoints
```
Routes to: `python_tooling` (if keywords match)
Creates: `project/specs/plan/plan-adw-api-rate-limiting.md`

**Example 2: ATDD planning**
```
/plan_adw Add gateway diagnostics endpoint --atdd
```
Creates ATDD plan from description
Creates: `project/specs/plan/plan-atdd-gateway-diagnostics.md`
