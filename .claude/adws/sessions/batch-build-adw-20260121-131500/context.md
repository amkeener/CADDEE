# ADW Build Session Context: batch-build-adw-20260121-131500

## Project Overview

This is the **anchor-planner** frontend application (micro-frontend for WakeCap portal).
The codebase is in `frontend-2.0-anchor-planner/` submodule on branch `ATDD`.

## Batch Source

Plans from: `project/specs/batch-adw-20260121-130212/`

## Testing Infrastructure

### Current State
- **Test Framework**: Jest with @testing-library/react
- **ATDD Framework**: Custom DSL/Protocol Driver pattern
- **Coverage**: ~3.5% statements, 1.7% branches (very low)
- **Setup File**: `src/app/jest.setup.ts` (fixed in previous session)

### Test Locations
| Location | Purpose |
|----------|---------|
| `src/app/**/*.test.tsx` | Unit tests (Jest) |
| `test/acceptance/` | ATDD acceptance tests |
| `test/acceptance/dsl/` | DSL classes |
| `test/acceptance/dsl/protocol_drivers/` | Protocol drivers |
| `test/acceptance/linear/` | Linear-generated test stubs |
| `tests/e2e/` | Playwright E2E tests |

### Test Commands
```bash
pnpm test                  # Run Jest tests
pnpm test:acceptance       # Run acceptance tests
pnpm lint:check           # ESLint check
pnpm exec tsc --noEmit    # TypeScript check
```

## Expert Guidelines

### Playwright Expert (Tests)
- ATDD three-layer architecture: DSL -> Protocol Driver -> SUT
- Use Given/When/Then pattern
- Keep tests focused - one behavior per test
- Use descriptive test names: test_feature_scenario

### Orchestrator Expert (Coverage)
- Route to appropriate domain experts
- Cross-cutting concerns
- Focus on pure functions for high ROI testing

## Key Files for Each Plan

### For plan-02 (ATDD test bodies)
- `frontend-2.0-anchor-planner/test/acceptance/dsl/zone_health_dsl.ts`
- `frontend-2.0-anchor-planner/test/acceptance/dsl/gateway_health_dsl.ts`
- `frontend-2.0-anchor-planner/test/acceptance/linear/test_zone_health_from_linear.test.ts`
- `frontend-2.0-anchor-planner/test/acceptance/linear/test_gateway_health_from_linear.test.ts`

### For plan-03 (Code coverage)
- `frontend-2.0-anchor-planner/src/app/services/analysis/combinedAnchorAnalysis.ts`
- `frontend-2.0-anchor-planner/src/app/services/analysis/coverageAnalysis.ts`
- `frontend-2.0-anchor-planner/src/app/services/analysis/maintenanceAnalysis.ts`
- `frontend-2.0-anchor-planner/src/app/services/config/configManager.ts`

### For plan-04 (GatewayHealthDSL)
- `frontend-2.0-anchor-planner/src/app/services/atdd/` - SUT directory (exists!)
- `frontend-2.0-anchor-planner/test/acceptance/dsl/gateway_health_dsl.ts`

## Validation Commands
```bash
# Working directory: frontend-2.0-anchor-planner/

# TypeScript check (use skipLibCheck to avoid config conflict)
pnpm exec tsc --noEmit --skipLibCheck 2>&1 | grep -v "TS5053"

# ESLint
pnpm lint:check

# Run tests
pnpm test

# Format
pnpm format:write
```

## Important Notes

1. All work is in the `frontend-2.0-anchor-planner/` submodule
2. Use `pnpm` as the package manager
3. Path alias `@/` maps to `src/app/`
4. CSS prefix is `twap-` for Tailwind classes
5. **Known Issue**: TypeScript has emitDeclarationOnly conflict - use `--skipLibCheck`
6. **Known Issue**: ESM import error with @esri/calcite-components in tests

