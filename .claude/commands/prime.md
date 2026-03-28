# Prime
> Execute the following sections to understand the codebase then summarize your understanding.

## Start Agent Messenger (Background)
Start the inter-agent communication listener so other Claude instances on the network can reach us.

```bash
# Start agent-messenger in background with project-specific UUID
PROJECT_NAME="${PROJECT_NAME:-$(basename $(pwd))}"
agent-messenger --uuid "${PROJECT_NAME}-$(hostname | tr '[:upper:]' '[:lower:]' | cut -d. -f1)" listen > /tmp/agent-messenger-${PROJECT_NAME}.log 2>&1 &
echo "Agent messenger started (PID: $!, UUID: ${PROJECT_NAME}-$(hostname | tr '[:upper:]' '[:lower:]' | cut -d. -f1))"
```

To send a message to other agents: `agent-messenger send "Hello from ${PROJECT_NAME}!"`
To see active peers: `agent-messenger peers`

## Read & Cleanup (if exists)
wip_summary.md - Resume context from previous session.

**After reading (or if file is >7 days old):** Delete the file to prevent stale context.
```bash
# Check age and delete if stale (>7 days) or after reading
find . -maxdepth 1 -name "wip_summary.md" -mtime +7 -delete 2>/dev/null
```
If you successfully read it, delete it after this prime session completes.

## Read (if exists)
project/reports/last_nights_work.md - Review what the nightly autonomous run completed.

If nightly work exists:
1. Print summary to user
2. Show `git status` and `git diff --stat` if there are uncommitted changes
3. Ask: "Nightly work completed. Review changes and commit? (yes/no/diff)"
   - **yes**: Run `/commit` with appropriate message
   - **no**: Continue without committing (changes preserved)
   - **diff**: Show full diff, then ask again

## Read
project/backlog.md - Master work tracking. Shows what's done, in progress, and planned.

## Read Sub-Project Backlogs (if they exist)
Scan for `project/backlog.md` in known sub-projects within the AdwProject workspace. Read each one that exists and include a brief summary alongside the master backlog.

```bash
for dir in frontend-2.0-anchor-planner frontend-2.0-site-support diagnostics-service wakecap-on-site-support identity-service; do
  backlog="$dir/project/backlog.md"
  if [ -f "$backlog" ]; then
    echo "📋 Found: $backlog"
  fi
done
```

Read any backlogs found above. When summarizing, note which sub-project each item belongs to.

<!-- ## Read Roadmap (if exists)
# Read current project roadmap if one exists (e.g., project/roadmap.md)
# Roadmaps typically contain implementation priorities and milestones
-->

## Run
git ls-files

## Read
README.md
.claude/commands/conditional_docs.md - this is a guide for you to determine which documentation to read based on the upcoming task.

<!-- ## Optional: Project-Specific Health Checks
# Add health checks relevant to your project here, e.g.:
# - API endpoint health
# - Database connectivity
# - External service status
-->

<!-- ## Optional: Cloud/Infrastructure Logs
# If using cloud infrastructure, add log checks here, e.g.:
# - gcloud logging read for GCP
# - aws logs for AWS
# - Check for recent errors before starting new work
-->

## Run
/scripts - List available project scripts

## Load MCP Servers

### Step 1: Check MCP Configuration
Check for `.mcp.json` (native Claude Code format) at project root:

```bash
if [ -f ".mcp.json" ]; then
  echo "📡 MCP Configuration (.mcp.json):"
  cat .mcp.json
else
  echo "No .mcp.json found at project root"
fi
```

### Step 2: Check Current MCP Status
Run `claude mcp list` to see connection status:

```bash
claude mcp list 2>&1
```

### Step 3: Handle Disconnected MCPs
**If any MCPs show as disconnected or need authentication:**

Display status summary:
```
📡 MCP Server Status:
- ✓ Connected: <list>
- ⚠ Needs Auth: <list>
- ✗ Disconnected: <list>
```

**If MCPs need authentication or are disconnected, ask:**
"Some MCP servers need attention. Would you like to:
- **Authenticate**: Open auth flow for MCPs needing login
- **Skip**: Continue without these MCPs
- **Remove**: Remove problematic MCPs from config"

### Step 4: Legacy Fallback
If no `.mcp.json` exists, check for legacy `.claude/available_mcps.json`:

```bash
cat .claude/available_mcps.json 2>/dev/null
```

If found, offer to create `.mcp.json` from the legacy format:
```bash
# Convert available_mcps.json to .mcp.json format
```

**Note:**
- `.mcp.json` is the native Claude Code format (auto-loaded)
- MCPs persist in user config once authenticated
- To manually add: `claude mcp add <name> <command>`
- To remove: `claude mcp remove <name>`

## Show Working Branches

Display current branch state for reference. Do NOT ask the user to confirm — just list them.

```bash
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📍 CURRENT BRANCHES"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Main repo: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
git submodule foreach --quiet 'echo "  $sm_path: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"'
```

**Note:** `.session_branches.json` is tracked in git to preserve branch state across clones. Update it at session end via `/wrap_up`.
