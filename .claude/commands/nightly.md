# Nightly Autonomous Work

Automatically process backlog items autonomously. Handles trivial-moderate complexity items.

## Variables
dry_run: $ARGUMENTS

## Configuration

```yaml
limits:
  trivial_simple: 5    # Max trivial/simple items per run
  moderate: 2          # Max moderate items per run
  complex: 1           # Max complex items per run (rare)
  max_runtime_minutes: 25

priority_order:
  - HIGH
  - MEDIUM
  - LOW

complexity_filter:
  - trivial
  - simple
  - moderate
```

## Instructions

Process backlog items autonomously. For each item: research, plan, implement, test. If blocked by questions, annotate the item and move on.

## Workflow

### 1. Initialize Session

```
Session: nightly-{YYYYMMDD-HHMMSS}
Start time: {timestamp}
Log: .claude/learning/nightly-logs/{date}.jsonl
Report: project/reports/last_nights_work.md
```

### 2. Parse Backlog

Read `project/backlog.md` and extract eligible items:

```python
eligible = []
for item in backlog:
    if item.status not in ['done', 'blocked', 'in_progress']:
        if item.complexity in ['trivial', 'simple', 'moderate']:
            eligible.append(item)

# Sort by priority (HIGH > MEDIUM > LOW), then by age
eligible.sort(key=lambda x: (priority_rank(x), x.added_date))
```

### 3. Select Work Batch

Apply limits:
```python
batch = []
counts = {'trivial': 0, 'simple': 0, 'moderate': 0}

for item in eligible:
    complexity = item.complexity
    if complexity in ['trivial', 'simple']:
        if counts['trivial'] + counts['simple'] < 5:
            batch.append(item)
            counts[complexity] += 1
    elif complexity == 'moderate':
        if counts['moderate'] < 2:
            batch.append(item)
            counts['moderate'] += 1
```

### 4. Process Each Item

For each item in batch:

#### 4a. Research Phase
- Understand the item's context
- Identify relevant files
- Check for dependencies

#### 4b. Plan Phase (if needed)
- For simple items: mental plan, no doc
- For moderate items: brief plan in memory

#### 4c. Implement Phase
- Make the code changes
- Follow existing patterns
- DO NOT commit yet (leave for morning review)

#### 4d. Test Phase
- Write tests if missing
- Run existing tests
- Log results (pass/fail)

#### 4e. Handle Questions/Blockers
If blocked or uncertain:
```markdown
<!-- NIGHTLY-QUESTION: {date} -->
**Questions from nightly run:**
- {question 1}
- {question 2}
<!-- END-NIGHTLY-QUESTION -->
```
- Add annotation to backlog item
- Skip implementation
- Log as "blocked"
- Continue to next item

### 5. Runtime Management

Check elapsed time after each item:
```python
if elapsed_minutes > 25:
    log("Runtime limit reached, stopping")
    break
```

### 6. Generate Report

Create `project/reports/last_nights_work.md`:

```markdown
# Nightly Work Report - {date}

## Summary
- **Run time**: {start} - {end} ({duration})
- **Items attempted**: {count}
- **Completed**: {count}
- **Blocked**: {count}
- **Failed**: {count}

## Completed Items

### 1. {item description}
- **Complexity**: {complexity}
- **Domain**: {domain}
- **Files changed**: {list}
- **Tests**: {passed/failed/written}
- **Time**: {duration}

## Blocked Items (Need Input)

### 1. {item description}
- **Reason**: {why blocked}
- **Questions**:
  - {question 1}
  - {question 2}

## Failed Items

### 1. {item description}
- **Error**: {what went wrong}
- **Logs**: {reference to detailed logs}

## Changes Ready for Review

```bash
git status
git diff --stat
```

**To commit all changes:**
```bash
git add -A && git commit -m "feat: nightly autonomous work ({date})"
```

**To review changes:**
```bash
git diff
```

## Next Steps
- [ ] Review completed work
- [ ] Answer blocked item questions
- [ ] Commit or discard changes
```

## Dry Run Mode

If `dry_run` is "true" or "--dry-run":
- Parse backlog and select batch
- Print what WOULD be done
- Do not make any changes
- Useful for testing selection logic

## Safety Rules

- NEVER commit changes (leave for morning review)
- NEVER push to remote
- ALWAYS log what was attempted
- ALWAYS generate report even if nothing completed
- STOP if runtime exceeds 25 minutes

## Error Handling

- Individual item failure: Log, skip, continue
- Parse error: Log, abort run
- Git error: Log, abort run
- Timeout: Log current state, generate partial report

## Output

Return path to report:
```
project/reports/last_nights_work.md
```
