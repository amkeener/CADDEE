---
name: batch_build_adw
description: Implement multiple plans in parallel using ADW orchestrator with domain expert routing. Each plan is implemented by an agent guided by the assigned expert.
argument-hint: "[batch-folder | manifest.json]" [--plan-ids plan-01,plan-02]
---

# Batch Build ADW

Implement multiple plans in parallel using spawned agents with ADW domain expert routing. Each plan is implemented by an agent guided by its assigned domain expert.

## Variables

BATCH_INPUT: $ARGUMENTS
SESSION_ID: batch-build-adw-{timestamp}

## Arguments

Parse `BATCH_INPUT` for:
- **Batch folder**: `project/specs/batch-adw-{timestamp}/`
- **Manifest path**: Direct path to `manifest.json`
- **`--plan-ids`**: (Optional) Comma-separated list of specific plan IDs to implement
- **`--priority`**: (Optional) Only implement plans of given priority (P0, P1, P2, P3)

Examples:
```
/batch_build_adw project/specs/batch-adw-20260113-120000/           # All ready plans
/batch_build_adw project/specs/batch-adw-20260113-120000/ --plan-ids plan-01,plan-02
/batch_build_adw project/specs/batch-adw-20260113-120000/ --priority P1
```

## Architecture

```
adws/sessions/{session_id}/
├── state.json              # ADW session state
├── context.md              # Pre-computed project context
├── expert-assignments.json # Expert assignments for each plan
└── logs/
    └── workflow.jsonl      # Event log

project/specs/{batch-folder}/
├── manifest.json           # Updated with implementation status
├── plan-01-{name}.md       # Status updated to "done" after success
├── plan-02-{name}.md
└── ...
```

---

## Phase 1: Initialize ADW Session

1. **Generate Session ID**:
   ```
   SESSION_ID: batch-build-adw-{YYYYMMDD-HHMMSS}
   ```

2. **Create ADW Session Directory**:
   ```bash
   mkdir -p adws/sessions/{session_id}/logs
   ```

3. **Initialize State** (`adws/sessions/{session_id}/state.json`):
   ```json
   {
     "session_id": "{session_id}",
     "workflow_type": "batch_build",
     "status": "initializing",
     "created": "{ISO timestamp}",
     "batch_source": "{batch_folder}",
     "plans_total": 0,
     "plans_completed": 0,
     "plans_failed": 0,
     "experts_used": []
   }
   ```

4. **Log Session Start** (`adws/sessions/{session_id}/logs/workflow.jsonl`):
   ```json
   {"timestamp": "...", "event_type": "session_start", "workflow": "batch_build_adw", "batch_source": "..."}
   ```

---

## Phase 2: Load Batch Manifest & Filter Plans

1. **Load Manifest** from batch folder:
   ```bash
   cat {batch_folder}/manifest.json
   ```

2. **Filter Plans** to implement:
   - Default: All plans with status `ready`
   - With `--plan-ids`: Only specified plan IDs
   - With `--priority`: Only plans matching priority

3. **Verify Plan Status**:
   - Each plan file must have `status: approved` or `status: ready`
   - Skip plans with status `done`, `implementing`, or `failed`
   - Warn about any skipped plans

4. **Create Expert Assignments** (`adws/sessions/{session_id}/expert-assignments.json`):
   ```json
   {
     "assignments": [
       {"plan_id": "plan-01", "plan_path": "...", "expert": "{expert_1}", "priority": "P1"},
       {"plan_id": "plan-02", "plan_path": "...", "expert": "{expert_2}", "priority": "P2"}
     ]
   }
   ```

5. **Log Plan Selection**:
   ```json
   {"timestamp": "...", "event_type": "plans_selected", "count": N, "plan_ids": ["plan-01", "plan-02"]}
   ```

---

## Phase 3: Generate Context

1. **Read Expert YAML files** for each unique expert being used

2. **Build Context File** (`adws/sessions/{session_id}/context.md`):
   - Project overview (from README.md)
   - Architecture summary relevant to batch scope
   - Key file locations from each expert's `context_files`
   - Keep under 500 lines

---

## Phase 4: Parallel Implementation (Multiple Agents)

Spawn **multiple Task agents in parallel** with expert-specific prompts.

### Agent Spawning

For each plan to implement, spawn a Build agent **in the same message** to run in parallel:

```
Task(
  subagent_type: "general-purpose",
  run_in_background: true,
  prompt: <see BUILD_AGENT_PROMPT below>
)
```

**CRITICAL**:
- Spawn all agents in a single message with multiple Task tool calls. Max 4 concurrent agents.
- Use `subagent_type: "general-purpose"` to ensure full tool access (Read, Write, Edit, Bash).
- For more than 4 plans, batch into groups of 4 and wait between batches.

### Build Agent Prompt Template

```
BUILD_AGENT_PROMPT:
"""
You are implementing a plan with domain expert guidance.

## ADW Session
Session ID: {session_id}
Your Expert: {expert_name}

## Plan to Implement
Plan Path: {plan_path}
Plan ID: {plan_id}
Priority: {priority}

## Expert Knowledge
Read and apply guidance from: .claude/commands/experts/{expert}/expertise.yaml

Key guidelines from your expert:
{expert_guidelines_summary}

Context files to reference:
{expert_context_files}

Validation commands to run:
{expert_validation_commands}

## Your Task
1. Read the plan file completely: {plan_path}
2. Read your expert's expertise.yaml for domain conventions
3. Read the context file: adws/sessions/{session_id}/context.md
4. Execute each implementation step in the plan's "Step by Step Tasks"
5. Follow expert guidelines for code style and patterns
6. Run validation commands after completion
7. Report results

## Implementation Rules
- Follow the plan's implementation steps IN ORDER
- Apply expert's guidelines and conventions
- Run expert's validation_commands after changes
- If you encounter blocking issues:
  - Document the issue clearly
  - Continue with other non-dependent steps if possible
  - Do NOT mark the plan as complete if blocked
- Do not modify files outside the plan's "Relevant Files" without good reason

## Validation
After implementing all steps, run:
```bash
{expert_validation_commands}
```

## Output Format
When complete, output a summary:
```
## Build Result: {plan_id}

**Status:** success | partial | failed
**Expert:** {expert_name}
**Plan:** {plan_path}

### Completed Steps
- [x] Step 1: ...
- [x] Step 2: ...

### Files Changed
{list of files created/modified}

### Validation Results
{output from validation commands}

### Issues Encountered (if any)
{description of any problems}

### TODO Items (if any)
{any TODO comments added}
```

## Important
- If all steps complete and validation passes: Status = success
- If some steps complete but blocked on others: Status = partial
- If critical failure prevents progress: Status = failed
"""
```

### Collecting Build Results

After spawning all agents, wait for completion:

```
For each agent_id:
  TaskOutput(task_id: agent_id, block: true, timeout: 300000)
```

Parse each agent's output for:
- Status (success/partial/failed)
- Files changed
- Validation results
- Issues encountered

Log results:
```json
{"timestamp": "...", "event_type": "build_complete", "plan_id": "plan-01", "status": "success", "expert": "..."}
```

---

## Phase 5: Update Tracking

### Update Plan Files
For each successfully implemented plan:
```yaml
---
status: done  # Changed from approved/ready
completed_at: {ISO timestamp}
build_session: {session_id}
---
```

### Update Manifest
Update `manifest.json` with implementation status:
```json
{
  "plans": [
    {
      "id": "plan-01",
      "status": "complete",  // or "failed", "partial"
      "implemented_at": "{ISO timestamp}",
      "build_session": "{session_id}"
    }
  ]
}
```

### Update BACKLOG.md (if applicable)
- Move completed items to "Completed (Recent)"
- Add completion date

---

## Phase 6: Finalize Session

1. **Update Session State** (`adws/sessions/{session_id}/state.json`):
   ```json
   {
     "session_id": "{session_id}",
     "workflow_type": "batch_build",
     "status": "completed",
     "created": "{ISO timestamp}",
     "completed": "{ISO timestamp}",
     "batch_source": "{batch_folder}",
     "plans_total": 4,
     "plans_completed": 3,
     "plans_failed": 1,
     "experts_used": ["{expert_1}", "{expert_2}"],
     "results": [
       {"plan_id": "plan-01", "status": "complete", "expert": "{expert_1}"},
       {"plan_id": "plan-02", "status": "failed", "expert": "{expert_1}", "error": "..."}
     ]
   }
   ```

2. **Log Session End**:
   ```json
   {"timestamp": "...", "event_type": "session_end", "status": "completed", "success_count": 3, "fail_count": 1}
   ```

3. **Generate Summary**

---

## Workflow Summary

```
+---------------------------------------------------------------------+
|  /batch_build_adw project/specs/batch-adw-{timestamp}/              |
+---------------------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------------------+
|  1. Initialize ADW session (state.json, workflow.jsonl)             |
|  2. Load manifest, filter plans by status/priority/ids              |
|  3. Generate context.md with expert knowledge                       |
+---------------------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------------------+
|  4. Spawn Build agents IN PARALLEL (each with expert context)       |
|     +-> Build Agent 1 ({expert_1}): Implement plan-01               |
|     +-> Build Agent 2 ({expert_1}): Implement plan-02               |
|     +-> Build Agent 3 ({expert_2}): Implement plan-03               |
|     +-> Build Agent 4 ({expert_2}): Implement plan-04               |
+---------------------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------------------+
|  5. Wait for all agents (TaskOutput), collect results               |
|  6. Update plan files (status: done), manifest, BACKLOG.md          |
|  7. Finalize session state, generate summary                        |
+---------------------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------------------+
|  Output: Summary of all implementations with validation results     |
+---------------------------------------------------------------------+
```

---

## Example Usage

### Implement All Ready Plans
```
/batch_build_adw project/specs/batch-adw-20260113-120000/
```

**Output:**
```
ADW Session: batch-build-adw-20260113-150000

Plans to Implement (4):
+- plan-01: Add User Authentication     [{expert_1}]       P2
+- plan-02: Implement API Rate Limiting [{expert_1}]       P2
+- plan-03: Add Logging Middleware      [{expert_2}]       P3
+- plan-04: Create Dashboard Component  [{expert_2}]       P3

Implementation Phase (4 parallel agents):
+- plan-01 [{expert_1}]:  SUCCESS  (15 files changed)
+- plan-02 [{expert_1}]:  SUCCESS  (8 files changed)
+- plan-03 [{expert_2}]:  SUCCESS  (12 files changed)
+- plan-04 [{expert_2}]:  PARTIAL  (blocked on dependency)

Summary:
- Completed: 3
- Partial: 1
- Failed: 0

Session: adws/sessions/batch-build-adw-20260113-150000/

Next Steps:
- Review changes: /code_review_adw
- Fix partial: /build_adw project/specs/batch-adw-20260113-120000/plan-04-reference-indexer.md
```

### Implement Specific Plans
```
/batch_build_adw project/specs/batch-adw-20260113-120000/ --plan-ids plan-01,plan-02
```

### Implement by Priority
```
/batch_build_adw project/specs/batch-adw-20260113-120000/ --priority P1
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `ready` | Plan approved, awaiting implementation |
| `implementing` | Build agent currently working |
| `complete` | Successfully implemented and validated |
| `partial` | Some steps complete, others blocked |
| `failed` | Critical failure, needs investigation |

---

## Error Handling

- **Expert not found**: Fall back to `orchestrator` expert
- **Plan not approved**: Skip with warning, suggest running /plan_adw first
- **Build agent fails**: Mark as `failed`, continue with other plans
- **Validation fails**: Mark as `partial`, log specific failures
- **Timeout**: Mark as `partial`, check agent output for progress
- **Retry failed plans**: `/build_adw {plan_path}` for individual retry
- **Debug agents**: `TaskOutput(agent_id, block=false)` for status check

---

## Notes

- **Max 4 concurrent agents** to avoid resource contention
- **Priority order**: P0 -> P1 -> P2 -> P3 when dependencies exist
- Each agent gets **expert-specific context** for domain knowledge
- Session logs in `adws/sessions/` enable debugging and learning
- **Validation is mandatory** - agents must run validation commands
- For **interdependent plans**, implement in dependency order (not parallel)
- Always **verify build success** before marking complete
