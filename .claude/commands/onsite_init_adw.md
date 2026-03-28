# Initialize ADW Framework in Subproject

> Bootstrap the ADW framework (commands, hooks, rules, scripts) into a subproject via symlinks.

## Usage

```
/init_adw <subproject_directory>
```

**Examples:**
- `/init_adw wakecap-on-site-support`
- `/init_adw identity-service`
- `/init_adw /absolute/path/to/repo`

## What It Does

1. Creates `.claude/` in the target repo
2. **Symlinks** shared ADW directories (commands, hooks, scripts, rules, agents, etc.) back to AdwProject
3. **Copies** `settings.json` so it can be customized per project (e.g., adding `dotnet` to allowed commands)
4. Creates local `learning/` and `memory/` directories for project-specific data
5. Adds `.claude/` to the target's `.gitignore` (symlinks are machine-specific)

## Execute

```bash
bash .claude/scripts/init_adw.sh "$1"
```

After running, verify the setup:

```bash
ls -la "$1/.claude/"
```

Then tell the user:
- They can now `cd` into the subproject and run `claude` with full ADW support
- The project's own `CLAUDE.md` and conventions (e.g., `ClaudeContext/`) are preserved
- `/prime`, `/wrap_up`, `/plan_adw`, `/build_adw` and all other ADW commands are available
- If the project needs specific permissions (e.g., `dotnet` commands), edit `.claude/settings.json` in the subproject
- The script is idempotent — safe to re-run after ADW updates
