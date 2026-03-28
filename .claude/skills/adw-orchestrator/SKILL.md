---
name: adw-orchestrator
description: Orchestrates ADW workflows with domain expert routing. Use when user asks to plan, build, review, or fix with expert guidance, or mentions ADW workflows.
---

# ADW Orchestrator

Intelligent workflow orchestration with automatic domain expert routing.

## Overview

The ADW (AI Developer Workflow) Orchestrator provides expert-guided development workflows that automatically route tasks to specialized domain experts based on file patterns and task requirements.

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/plan_adw <prompt>` | Expert-guided planning | `/plan_adw Add rate limiting to API` |
| `/build_adw <plan>` | Expert-guided implementation | `/build_adw plan-adw-rate-limiting.md` |
| `/code_review_adw [scope]` | Multi-expert security-first review | `/code_review_adw 3` |
| `/fix_adw <review>` | Expert-guided fix application | `/fix_adw 2024-01-12-adw-review.md` |
| `/research_adw <topic>` | Expert-guided research | `/research_adw How does auth work?` |

## Domain Experts

Experts are defined in `.claude/commands/experts/{name}/expertise.yaml`.

Default experts included:
- `security_audit` - Security review, vulnerabilities (always for reviews)
- `python_tooling` - Hooks, scripts, automation
- `research` - Exploration and investigation
- `orchestrator` - Workflow coordination

## Expert Routing Logic

```
1. Analyze prompt/files for domain keywords
2. Match against expert file_patterns
3. Score matches (patterns: 2x, keywords: 1x)
4. Select highest confidence expert
5. If no match → research expert
6. Always include security_audit for review workflows
```

## Workflow Lifecycle

### Plan Workflow
```
analyze_task → research_codebase → design_solution → create_plan
```
Output: `project/specs/plan/plan-adw-{name}.md`

### Build Workflow
```
load_plan → implement → validate_changes
```
Output: Modified files + validation results

### Review Workflow
```
diff_analysis (security_audit) → domain_review (auto) → generate_report
```
Output: `project/code_reviews/{date}-adw-{name}.md`

### Fix Workflow
```
parse_review → prioritize_issues → apply_fixes → verify_fixes
```
Output: Fixed issues + backlog updates

## Session Management

Sessions are stored in `adws/sessions/{session_id}/`:
- `state.json` - Workflow state and step progress
- `context.md` - Accumulated context between steps

Logs are stored in `logs/adw/{session_id}/`:
- `workflow.jsonl` - Workflow events
- `expert_calls.jsonl` - Expert invocation details

## Expert YAML Structure

```yaml
name: expert_name
description: What this expert does
version: "1.0"

domain:
  primary: "Main expertise"
  secondary: ["Related skill 1", "Related skill 2"]

file_patterns:
  - "path/to/**/*.ext"

keywords:
  - keyword1
  - keyword2

capabilities:
  - "What this expert can do"

guidelines:
  - "Best practices to follow"

validation_commands:
  - "Commands to verify work"

context_files:
  - "Files to read for context"
```

## Creating New Experts

1. Create directory: `.claude/commands/experts/{expert_name}/`
2. Add `expertise.yaml` following the structure above
3. Update orchestrator's `verified_experts` list

## Best Practices

1. **Use ADW for complex tasks** - Simple changes don't need expert routing
2. **Let the router choose** - Don't override expert unless necessary
3. **Follow the workflow** - plan → build → review → fix
4. **Check expert context** - Read the expert YAML to understand guidelines
5. **Review validation commands** - Experts specify how to verify work
