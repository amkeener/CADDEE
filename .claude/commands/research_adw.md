---
name: research_adw
description: Research a topic using ADW with domain expert routing and session tracking.
argument-hint: [research-topic]
---

# Research ADW

Research a topic using the ADW orchestrator with expert routing and session tracking.

## Variables

TOPIC: $ARGUMENTS
SESSION_ID: adw-research-{timestamp}

## Instructions

### 1. Initialize ADW Session

```
Session: adw-research-{YYYYMMDD-HHMMSS}
Directory: adws/sessions/{session_id}/
```

### 2. Route to Expert

Analyze TOPIC to determine domain:
- Match keywords against expert definitions
- Default to `research` expert for exploratory tasks

### 3. Research Phase

Using the expert's context:
1. **Explore Codebase**
   - Use expert's `context_files` as starting points
   - Search for related patterns
   - Follow imports and dependencies

2. **Gather Documentation**
   - Read relevant README files
   - Check for inline documentation
   - Find related specs/plans

3. **Build Understanding**
   - Document findings in `context.md`
   - Note patterns and conventions
   - Identify gaps in understanding

### 4. Generate Report

Output to: `project/research/{topic-slug}.md`

**Report Format:**
```markdown
# Research: {Topic}

**Date:** {date}
**Session:** {session_id}
**Expert:** {expert}

## Summary
{1-2 paragraph overview}

## Key Findings

### Finding 1
{Description with file references}

### Finding 2
{Description with file references}

## Relevant Files
- `path/to/file.py` - {brief description}
- `path/to/other.py` - {brief description}

## Patterns Observed
- {Pattern 1}
- {Pattern 2}

## Open Questions
- {Question 1}
- {Question 2}

## Recommendations
- {Recommendation 1}
- {Recommendation 2}
```

### 5. Finalize Session

Save state and log completion.

## Output

Return the path to the research report:
```
project/research/{topic-slug}.md
```

## Examples

**Example 1: Research authentication**
```
/research_adw How does authentication work in this project?
```

**Example 2: Research a pattern**
```
/research_adw Explore the error handling patterns
```
