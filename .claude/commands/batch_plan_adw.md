---
name: batch_plan_adw
description: Create multiple plans in parallel using ADW orchestrator with domain expert routing. Each plan gets expert-guided context.
argument-hint: "[P1: task1, P2: task2, ...]" [--implement]
---

# Batch Plan ADW

Create multiple plans in parallel using spawned agents with ADW domain expert routing. Each plan is created by an agent guided by the appropriate domain expert.

## Variables

features: $ARGUMENTS
SESSION_ID: batch-adw-{timestamp}

## Arguments

Parse `features` for:
- **Feature list**: Comma-separated or newline-separated features with priorities
- **`--implement`**: (Optional) Automatically spawn implementation agents after planning
- **`--plan-only`**: (Default) Generate plans only, do not implement

Examples:
```
/batch_plan_adw "P1: Add RPC rate limiting, P1: Add wallet biometrics"           # Plan only
/batch_plan_adw "P1: Add RPC rate limiting, P2: Fix bridge timeout" --implement  # Plan + implement
```

## Architecture

```
adws/sessions/{session_id}/
├── state.json              # ADW session state
├── context.md              # Pre-computed project context
├── expert-routing.json     # Expert assignment per task
└── logs/
    └── workflow.jsonl      # Event log

project/specs/batch-adw-{timestamp}/
├── manifest.json           # Batch metadata, plan status tracking
├── plan-01-{name}.md       # Individual plan files (with expert metadata)
├── plan-02-{name}.md
└── ...
```

---

## Phase 1: Initialize ADW Session

1. **Generate Session ID**:
   ```
   SESSION_ID: batch-adw-{YYYYMMDD-HHMMSS}
   ```

2. **Create ADW Session Directory**:
   ```bash
   mkdir -p adws/sessions/{session_id}/logs
   mkdir -p project/specs/batch-adw-{timestamp}
   ```

3. **Initialize State** (`adws/sessions/{session_id}/state.json`):
   ```json
   {
     "session_id": "{session_id}",
     "workflow_type": "batch_plan",
     "status": "initializing",
     "created": "{ISO timestamp}",
     "implement": false,
     "experts_used": [],
     "plans": []
   }
   ```

4. **Log Session Start** (`adws/sessions/{session_id}/logs/workflow.jsonl`):
   ```json
   {"timestamp": "...", "event_type": "session_start", "workflow": "batch_plan_adw", "task_count": N}
   ```

---

## Phase 2: Parse Features & Route Experts

1. **Parse Features** from `features` input:
   - Comma-separated: `"P0: Dispute UI, P1: Evidence system"`
   - JSON array: `[{"priority": "P0", "feature": "...", "description": "..."}]`
   - Check for `--implement` flag

2. **Route Each Feature to Expert**:

   **Expert Routing Logic:**
   | Pattern | Expert | Expertise File |
   |---------|--------|----------------|
   | `src/**/*.rs`, `crates/**/*.rs` | `rust` | `.claude/commands/experts/rust/expertise.yaml` |
   | `src/**/*.py`, `scripts/**/*.py` | `python` | `.claude/commands/experts/python/expertise.yaml` |
   | `src/**/*.ts`, `lib/**/*.ts` | `typescript` | `.claude/commands/experts/typescript/expertise.yaml` |
   | security, audit, vulnerability, attack | `security_audit` | `.claude/commands/experts/security_audit/expertise.yaml` |
   | `.claude/**/*.py`, scripts, hooks, tooling | `python_tooling` | `.claude/commands/experts/python_tooling/expertise.yaml` |
   | research, docs, investigation | `research` | `.claude/commands/experts/research/expertise.yaml` |
   | No match | `orchestrator` | `.claude/commands/experts/orchestrator/expertise.yaml` |

   > **Note:** Update patterns above to match your project structure. See `.claude/commands/experts/` for available experts.

3. **Create Expert Routing Map** (`adws/sessions/{session_id}/expert-routing.json`):
   ```json
   {
     "routings": [
       {"plan_id": "plan-01", "feature": "...", "expert": "{expert_1}", "reason": "..."},
       {"plan_id": "plan-02", "feature": "...", "expert": "{expert_2}", "reason": "..."}
     ]
   }
   ```

4. **Log Expert Selections**:
   ```json
   {"timestamp": "...", "event_type": "expert_routed", "plan_id": "plan-01", "expert": "{expert}", "reason": "..."}
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

## Phase 4: Parallel Plan Generation (Multiple Agents)

Spawn **multiple Task agents in parallel** with expert-specific prompts.

### Agent Spawning

For each feature, spawn a Plan agent **in the same message** to run in parallel:

```
Task(
  subagent_type: "general-purpose",
  run_in_background: true,
  prompt: <see PLAN_AGENT_PROMPT below>
)
```

**CRITICAL**:
- Spawn all agents in a single message with multiple Task tool calls. Max 4 concurrent agents.
- Use `subagent_type: "general-purpose"` (NOT "Plan") to ensure the agent has Write tool access for creating plan files.

### Plan Agent Prompt Template

```
PLAN_AGENT_PROMPT:
"""
You are generating a plan for: {priority}: {feature_description}

## ADW Session
Session ID: {session_id}
Your Expert: {expert_name}

## Expert Knowledge
Read and apply guidance from: .claude/commands/experts/{expert}/expertise.yaml

Key guidelines from your expert:
{expert_guidelines_summary}

Context files to read:
{expert_context_files}

Validation commands to include:
{expert_validation_commands}

## Your Task
1. Read the context file: adws/sessions/{session_id}/context.md
2. Read your expert's expertise.yaml for domain knowledge
3. Research the codebase using expert's context_files
4. Generate a comprehensive plan following the format below
5. **CRITICAL: You MUST use the Write tool to save your plan to:**
   `project/specs/batch-adw-{timestamp}/plan-{nn}-{slugified-name}.md`

DO NOT just return the plan as text output. You MUST write it to the file path above.

## Output File
- Path: project/specs/batch-adw-{timestamp}/plan-{nn}-{slugified-name}.md
- The file MUST be created before you finish

## Plan Format
Your plan file must follow this exact structure:

```md
---
status: approved
type: {feature|bug|chore|refactor}
complexity: {trivial|simple|moderate|complex|major}
adw_session: {session_id}
expert: {expert_name}
batch_id: batch-adw-{timestamp}
plan_id: plan-{nn}
priority: {priority}
---

# Plan: {task_name}

## Task Description
{description}

## Expert Context
Expert: {expert_name}
Reason: {why this expert was selected}

## Objective
{what will be accomplished}

## Relevant Files
### To Read (for context)
- `path/to/file` - Why needed

### To Modify
- `path/to/file` - What changes

### To Create
- `path/to/new_file` - Purpose

## Implementation Phases
{For complex tasks, break into phases}

## Step by Step Tasks
1. {First task}
2. {Second task}
...

## Testing Strategy
{How to test, from expert's validation approach}

## Validation Commands
```bash
{From expert's validation_commands}
```

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

## Important Rules
- Apply expert's guidelines and conventions
- Keep "Relevant Files" to <15 files
- Break large features into phases
- Include expert's validation commands
- Be specific in implementation steps
- After writing the file, confirm it was created
"""
```

### Collecting Plan Results

After spawning all agents, wait for completion:

```
For each agent_id:
  TaskOutput(task_id: agent_id, block: true, timeout: 180000)
```

Verify each plan file was created:
```bash
ls -la project/specs/batch-adw-{timestamp}/plan-*.md
```

Update manifest status to `ready` for each completed plan.

Log completion:
```json
{"timestamp": "...", "event_type": "plan_created", "plan_id": "plan-01", "expert": "...", "path": "..."}
```

---

## Phase 5: Parallel Implementation (Optional)

**Only execute if `--implement` flag was passed.**

Once all plans have status `ready`, spawn implementation agents in parallel.

### Implementation Agent Spawning

```
For each plan with status "ready":
  Task(
    subagent_type: "general-purpose",
    run_in_background: true,
    prompt: <see IMPLEMENT_AGENT_PROMPT below>
  )
```

### Implementation Agent Prompt Template

```
IMPLEMENT_AGENT_PROMPT:
"""
Implement the plan at: project/specs/batch-adw-{timestamp}/plan-{nn}-{name}.md

## ADW Session
Session ID: {session_id}
Expert guidance: .claude/commands/experts/{expert}/expertise.yaml

## Instructions
1. Read the plan file completely (note the expert in frontmatter)
2. Read the expert's expertise.yaml for domain conventions
3. Read the context file: adws/sessions/{session_id}/context.md
4. Execute each implementation step in order
5. Run validation commands from the plan after completion
6. Report success or any issues encountered

## Important
- Follow the expert's guidelines for code style and patterns
- Follow the plan's implementation steps exactly
- Run tests after making changes
- If you encounter blocking issues, document them and continue with other steps
- Do not modify files outside the plan's "Relevant Files" without good reason
"""
```

### Collecting Implementation Results

```
For each agent_id:
  TaskOutput(task_id: agent_id, block: true, timeout: 300000)
```

Update manifest status to `complete` or `failed` based on results.

Log completion:
```json
{"timestamp": "...", "event_type": "implementation_complete", "plan_id": "plan-01", "status": "success"}
```

---

## Phase 6: Finalize Session

1. **Update Session State** (`adws/sessions/{session_id}/state.json`):
   ```json
   {
     "session_id": "{session_id}",
     "workflow_type": "batch_plan",
     "status": "completed",
     "experts_used": ["{expert_1}", "{expert_2}"],
     "plans": [
       {"id": "plan-01", "path": "...", "status": "ready", "expert": "..."},
       {"id": "plan-02", "path": "...", "status": "ready", "expert": "..."}
     ],
     "completed": "{ISO timestamp}"
   }
   ```

2. **Create Manifest** (`project/specs/batch-adw-{timestamp}/manifest.json`):
   ```json
   {
     "batch_id": "batch-adw-{timestamp}",
     "adw_session": "{session_id}",
     "created": "{ISO timestamp}",
     "status": "ready",
     "implement": false,
     "plans": [
       {
         "id": "plan-01",
         "priority": "P1",
         "name": "feature-name",
         "status": "ready",
         "expert": "{expert}",
         "file": "plan-01-feature-name.md"
       }
     ]
   }
   ```

3. **Log Session End**:
   ```json
   {"timestamp": "...", "event_type": "session_end", "status": "completed", "plan_count": N}
   ```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│  /batch_plan_adw "P0: feature A, P1: feature B" [--implement]       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. Initialize ADW session (state.json, workflow.jsonl)             │
│  2. Parse features, route each to domain expert                     │
│  3. Generate context.md with expert knowledge                       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. Spawn Plan agents IN PARALLEL (each with expert context)        │
│     ├─► Plan Agent 1 ({expert_1}): Write plan-01-*.md               │
│     ├─► Plan Agent 2 ({expert_2}): Write plan-02-*.md               │
│     └─► Plan Agent 3 ({expert_3}): Write plan-03-*.md               │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. Wait for all agents (TaskOutput), verify files exist            │
│  6. Update manifest + session state: all plans status = "ready"     │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  --implement flag?    │
                └───────────────────────┘
                      │           │
                     Yes          No
                      │           │
                      ▼           ▼
┌────────────────────────────┐   ┌─────────────────────────────┐
│  7. Spawn Implement agents │   │  7. Report plans created    │
│     with expert guidance   │   │     with expert assignments │
│  8. Wait, update status    │   │     (done)                  │
│  9. Report results         │   └─────────────────────────────┘
└────────────────────────────┘
```

---

## Example Usage

### Plan Only (Default)
```
/batch_plan_adw "P1: Add API rate limiting, P1: Add user authentication"
```

**Output:**
```
ADW Session: batch-adw-20260113-140000

Expert Routing:
├─ P1: Add API rate limiting     → {expert_1}
├─ P1: Add user authentication   → {expert_2}

Planning Phase (2 parallel agents):
├─ plan-01-api-rate-limiting.md   [{expert_1}]  ✓ Written
├─ plan-02-user-authentication.md [{expert_2}]  ✓ Written

Plans ready at: project/specs/batch-adw-20260113-140000/
Session logs:   adws/sessions/batch-adw-20260113-140000/

To implement, run:
  /batch_plan_adw --implement project/specs/batch-adw-20260113-140000/
  OR
  /implement project/specs/batch-adw-20260113-140000/plan-01-api-rate-limiting.md
```

### Plan + Implement
```
/batch_plan_adw "P1: Add logging middleware, P2: Fix dashboard UI" --implement
```

**Output:**
```
ADW Session: batch-adw-20260113-140000

Expert Routing:
├─ P1: Add logging middleware  → {expert_1}
├─ P2: Fix dashboard UI        → {expert_2}

Planning Phase (2 parallel agents):
├─ plan-01-logging-middleware.md  [{expert_1}]  ✓ Written
├─ plan-02-dashboard-ui-fix.md    [{expert_2}]  ✓ Written

Implementation Phase (2 parallel agents):
├─ plan-01 [{expert_1}]: ✓ Complete
├─ plan-02 [{expert_2}]: ✓ Complete

All plans implemented successfully.
Session: adws/sessions/batch-adw-20260113-140000/
```

---

## Manifest Status Values

| Status | Description |
|--------|-------------|
| `pending` | Not yet started |
| `planning` | Plan agent running |
| `ready` | Plan complete, awaiting implementation |
| `implementing` | Implementation agent running |
| `complete` | Successfully implemented |
| `failed` | Agent failed, needs retry/manual intervention |
| `blocked` | Waiting on dependency |

---

## Error Handling

- **Expert not found**: Fall back to `orchestrator` expert
- **Plan agent doesn't write file**: Check agent output, manually extract and write if needed
- **Plan agent fails**: Mark as `failed` in manifest, can retry individually
- **Implementation agent fails**: Preserve partial work, log error, continue with other plans
- **Retry failed plans**: `/implement {batch_folder}/plan-{nn}.md`
- **Debug agents**: `TaskOutput(agent_id, block=false)` for status check

---

## Notes

- **Max 4 concurrent agents** recommended to avoid resource contention
- Plans execute in **priority order** (P0 → P1 → P2 → P3) when dependencies exist
- Each agent gets **expert-specific context** for better domain knowledge
- Session logs in `adws/sessions/` enable debugging and learning
- For **project-wide changes**, decompose into domain-specific plans first
- **Always verify** plan files exist before proceeding to implementation
