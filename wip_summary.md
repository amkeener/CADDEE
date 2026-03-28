# WIP Summary

**Last Updated:** 2026-03-28

This was the initial bootstrapping session for CADDEE (CAD-AI Collaborative Design Tool). The .claude framework was copied from AdwProject and adapted: all Linear integration was removed (rules, tightly-coupled commands like atdd_adw/batch_atdd_adw/release, and optional Linear references stripped from plan_adw, build_adw, code_review_adw, pr). Portal, import-map, and subproject rules were also removed. The scope PDF was reviewed — it defines a 4-phase Electron + Python sidecar desktop app for natural language 3D modeling via OpenSCAD/Three.js with FreeCAD integration.

**Completed This Session:**
- Copied .claude folder from AdwProject
- Deleted 7 irrelevant rules (Linear x4, portal, import-map, subproject)
- Deleted 3 tightly-coupled Linear commands (atdd_adw, batch_atdd_adw, release)
- Stripped Linear references from 4 commands (plan_adw, build_adw, code_review_adw, pr)
- Cleared AdwProject memory/learning data
- Reviewed cad-ai-tool-scope.pdf (10 pages, 4-phase build plan)
- Initialized git repo, pushed to github.com/amkeener/CADDEE (clean history, no secrets)
- Added .gitignore

**Next Steps:**
- Run `/plan_adw` to create implementation plans for all 4 phases
- Replace AdwProject domain experts with CADDEE-specific experts (openscad, threejs, electron, python-sidecar, freecad)
- Clean out AdwProject-specific sessions from .claude/adws/sessions/
- Clean out AdwProject-specific symlinks (deploy.md, merge_to_env.md, postman-api-test.md are broken symlinks)
- Create project/BACKLOG.md
- Consider adding .gitignore for __pycache__ files already committed in .claude/

**Open Items:**
- Experts directory still has AdwProject experts (database, diagnostics-service, frontend, etc.) — needs full replacement
- Some commands (deploy, merge_to_env, postman-api-test) are broken symlinks from AdwProject — need removal or replacement
- prime.md references AdwProject-specific subprojects — needs adaptation
