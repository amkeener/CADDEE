#!/bin/bash
# init_adw.sh — Bootstrap ADW framework into a subproject
#
# Usage: init_adw.sh <target_dir>
#
# Creates symlinks from <target_dir>/.claude/ back to the AdwProject
# framework, giving the subproject access to all ADW commands, hooks,
# rules, and scripts while preserving its own CLAUDE.md and conventions.

set -euo pipefail

ADW_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET_DIR="${1:?Usage: init_adw.sh <target_dir>}"

# Resolve target to absolute path
if [[ ! "$TARGET_DIR" = /* ]]; then
  TARGET_DIR="$ADW_ROOT/$TARGET_DIR"
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: $TARGET_DIR does not exist or is not a directory"
  exit 1
fi

ADW_CLAUDE="$ADW_ROOT/.claude"
TARGET_CLAUDE="$TARGET_DIR/.claude"

echo "ADW Framework Bootstrap"
echo "======================="
echo "  Source: $ADW_CLAUDE"
echo "  Target: $TARGET_CLAUDE"
echo ""

# Create .claude directory
mkdir -p "$TARGET_CLAUDE"

# --- Symlinked directories (shared ADW framework) ---
SYMLINK_DIRS=(
  "commands"       # /prime, /wrap_up, /plan_adw, /build_adw, etc.
  "hooks"          # pre/post tool use, stop hooks
  "scripts"        # aggregate_learnings, generate_session_summary, etc.
  "adws"           # ADW core framework (orchestrator, router, state)
  "agents"         # Sub-agent definitions
  "skills"         # Skill definitions
  "rules"          # Org-wide rules (Linear workflow, git rules, etc.)
  "output-styles"  # Output formatting
)

for dir in "${SYMLINK_DIRS[@]}"; do
  src="$ADW_CLAUDE/$dir"
  dst="$TARGET_CLAUDE/$dir"

  if [[ -L "$dst" ]]; then
    # Already a symlink — check if it points to the right place
    current_target=$(readlink "$dst")
    if [[ "$current_target" = "$src" ]]; then
      echo "  [skip] $dir (already linked)"
    else
      rm "$dst"
      ln -s "$src" "$dst"
      echo "  [update] $dir -> $src"
    fi
  elif [[ -d "$dst" ]]; then
    echo "  [WARN] $dir exists as a real directory — skipping (remove manually to symlink)"
  elif [[ -e "$src" ]]; then
    ln -s "$src" "$dst"
    echo "  [link] $dir -> $src"
  else
    echo "  [skip] $dir (source not found)"
  fi
done

# --- Copied files (project-specific, may need customization) ---
if [[ ! -f "$TARGET_CLAUDE/settings.json" ]]; then
  cp "$ADW_CLAUDE/settings.json" "$TARGET_CLAUDE/settings.json"
  echo "  [copy] settings.json (customize per project)"
else
  echo "  [skip] settings.json (already exists)"
fi

# --- Local directories (per-project, not symlinked) ---
LOCAL_DIRS=("learning" "memory")
for dir in "${LOCAL_DIRS[@]}"; do
  dst="$TARGET_CLAUDE/$dir"
  if [[ ! -d "$dst" ]]; then
    mkdir -p "$dst"
    echo "  [create] $dir/ (local to this project)"
  else
    echo "  [skip] $dir/ (already exists)"
  fi
done

# --- Add .claude to .gitignore (symlinks are machine-specific) ---
GITIGNORE="$TARGET_DIR/.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -q "^\.claude/$" "$GITIGNORE" 2>/dev/null; then
    echo "" >> "$GITIGNORE"
    echo "# ADW framework (symlinked from AdwProject, machine-specific)" >> "$GITIGNORE"
    echo ".claude/" >> "$GITIGNORE"
    echo "  [update] .gitignore — added .claude/ exclusion"
  else
    echo "  [skip] .gitignore (already excludes .claude/)"
  fi
else
  echo "# ADW framework (symlinked from AdwProject, machine-specific)" > "$GITIGNORE"
  echo ".claude/" >> "$GITIGNORE"
  echo "  [create] .gitignore with .claude/ exclusion"
fi

# --- Summary ---
echo ""
echo "Done! ADW framework bootstrapped into $TARGET_DIR"
echo ""
echo "You can now:"
echo "  cd $TARGET_DIR"
echo "  claude"
echo ""
echo "All ADW commands (/prime, /wrap_up, /plan_adw, etc.) will be available."
echo "The project's own CLAUDE.md and conventions are preserved."
echo ""
echo "To update after ADW changes: re-run this script (safe to run multiple times)"
