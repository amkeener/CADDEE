# Wrap Up Session

End-of-session command to save progress, commit changes, and prepare for the next session.

## Instructions

Execute each section in order. This ensures all work is saved and the next session can resume seamlessly.

---

## 1. Review Session Work

Understand what was accomplished:

```bash
git status
git diff --stat HEAD
```

Identify:
- What features/bugs/chores were worked on
- Which plans were completed vs still in progress
- Any uncommitted changes that need to be saved

---

## 2. Update Plan Statuses

For any plans that were completed this session:
- Update `status: in_progress` → `status: done` in the plan's metadata
- If work is incomplete but progress was made, ensure status is `in_progress`

---

## 3. Update BACKLOG.md

Update `project/BACKLOG.md`:
- Move completed items from Features/Bugs/Chores to the Completed section
- Add today's date to completed entries
- Update status of any in-progress items
- Update the "Last Updated" date at the top

---

## 4. Generate Session Summary

Generate summary automatically from transcript:

```bash
# Discover transcript path and generate summary
TRANSCRIPT=$(python3 .claude/scripts/discover_transcript.py 2>/dev/null)
if [ -n "$TRANSCRIPT" ]; then
  python3 .claude/scripts/generate_session_summary.py \
    --transcript "$TRANSCRIPT" \
    --output wip_summary.md
fi
```

This extracts:
- Files created/modified
- Git commits made
- Key decisions
- Errors encountered
- TODOs mentioned
- Domains touched

The summary is saved to:
- `wip_summary.md` (for `/prime` in next session)
- `.claude/learning/session-summaries/{date}/{id}.yaml` (for nightly learning)

If the script fails or transcript unavailable, manually create `wip_summary.md`:

```markdown
# WIP Summary

**Last Updated:** <current date YYYY-MM-DD>

<One paragraph (3-5 sentences) covering:>
- What was accomplished this session
- Current state of work
- Any blockers or important findings

**Completed This Session:**
- <item 1>
- <item 2>

**Next Steps:**
- <priority 1>
- <priority 2>
- <priority 3>

**Open Items (if any):**
- <any work left in_progress>
```

---

## 5. Aggregate Learnings

Run the learning aggregation to capture insights from this session:

```bash
# Aggregate learnings for project and all submodules
python3 .claude/scripts/aggregate_learnings.py --days 1
```

This collects:
- Git commit patterns and domains touched
- Hot files (high churn indicating potential issues)
- Expert usage and success rates
- Session outcomes and durations

The aggregator creates:
- `.claude/learning/daily-insights/{date}.yaml` (project-level)
- `.claude/learning/submodules/{name}/{date}.yaml` (per submodule)

### Process Insights (Optional)

For longer sessions or significant work, also process insights:

```bash
# Process and route insights to appropriate handlers
python3 .claude/scripts/process_insights.py --days 1
```

This:
- Routes trivial/simple insights to `.claude/learning/pending/{expert}.yaml` for auto-improvement
- Routes moderate/complex insights to `project/BACKLOG.md` for human prioritization
- Updates the error catalog at `.claude/learning/error-catalog.yaml`
- Updates expert feedback files

### Submodule-Specific Learning

If you worked primarily in a specific submodule, also run:

```bash
# For frontend work
python3 .claude/scripts/aggregate_learnings.py --submodule frontend-2.0-anchor-planner --days 1

# For backend services
python3 .claude/scripts/aggregate_learnings.py --submodule diagnostics-service --days 1
python3 .claude/scripts/aggregate_learnings.py --submodule location-service --days 1
```

---

## 6. Frontend Linting Checks (if applicable)

**Before committing, check if this is a frontend project and run linting:**

```bash
# Check for frontend project
if [ -f "package.json" ] && grep -q '"lint:check"' package.json 2>/dev/null; then
  echo "Frontend project detected - running lint checks before commit..."

  # Auto-fix formatting first
  echo "Running format:write..."
  pnpm format:write 2>&1 | tail -5

  # Check for lint errors
  echo "Running lint:check..."
  pnpm lint:check 2>&1 | tail -20
  LINT_EXIT=$?

  if [ $LINT_EXIT -ne 0 ]; then
    echo "Note: lint:check has warnings/errors. Check if any are new errors that need fixing."
  fi
fi
```

**Also check submodules that were worked on:**
```bash
# For each submodule with changes
for submodule in frontend-2.0-anchor-planner diagnostics-service; do
  if [ -d "$submodule" ] && [ -n "$(cd $submodule && git status --porcelain 2>/dev/null)" ]; then
    echo "Checking $submodule..."
    (cd "$submodule" && \
      if [ -f "package.json" ] && grep -q '"format:check"' package.json 2>/dev/null; then
        pnpm format:write 2>&1 | tail -3
        pnpm lint:check 2>&1 | tail -10
      fi
    )
  fi
done
```

---

## 7. Commit Changes

Stage and commit all changes:

```bash
git add -A
git status
```

Create a commit with format: `chore: wrap up session - <brief summary>`

Example messages:
- `chore: wrap up session - implement dispute evidence system`
- `chore: wrap up session - reorganize documentation structure`
- `chore: wrap up session - fix iOS build issues`

Use conventional commit format with a HEREDOC:
```bash
git commit -m "$(cat <<'EOF'
chore: wrap up session - <summary>

<optional body with details>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## 8. Save Branch State

Save current branch information for session continuity (after commit so it captures final state):

```bash
# Create branch state file with actual values (not template strings)
echo '{' > .session_branches.json
echo '  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",' >> .session_branches.json
echo '  "main_repo": {' >> .session_branches.json
echo '    "branch": "'$(git rev-parse --abbrev-ref HEAD)'",' >> .session_branches.json
echo '    "commit": "'$(git rev-parse --short HEAD)'"' >> .session_branches.json
echo '  },' >> .session_branches.json
echo '  "submodules": [' >> .session_branches.json

# Add submodule branch info
FIRST=true
git submodule foreach --quiet '
  if [ "$FIRST" != "true" ]; then echo "," >> "$toplevel/.session_branches.json"; fi
  FIRST=false
  echo "    {" >> "$toplevel/.session_branches.json"
  echo "      \"path\": \"$sm_path\"," >> "$toplevel/.session_branches.json"
  echo "      \"branch\": \"$(git rev-parse --abbrev-ref HEAD)\"," >> "$toplevel/.session_branches.json"
  echo "      \"commit\": \"$(git rev-parse --short HEAD)\"" >> "$toplevel/.session_branches.json"
  printf "    }" >> "$toplevel/.session_branches.json"
'

echo '' >> .session_branches.json
echo '  ]' >> .session_branches.json
echo '}' >> .session_branches.json

echo "Branch state saved to .session_branches.json"
cat .session_branches.json
```

---

## 9. Push to Remote

Push changes to the remote repository:

```bash
git push
```

If the branch doesn't have an upstream, use:
```bash
git push -u origin <branch-name>
```

---

## 10. Final Verification

Confirm everything is saved:

```bash
git status
git log -1 --oneline
```

Expected output:
- "nothing to commit, working tree clean"
- Latest commit shows the wrap-up commit

---

## Report

Provide a brief summary:
- Commit hash and message
- Files changed count
- Confirmation push succeeded
- Reminder of next steps from WIP summary
