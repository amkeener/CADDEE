# ADW Session Context: batch-adw-20260121-130212

## Project Overview

This is the **anchor-planner** frontend application (micro-frontend for WakeCap portal).
The codebase is in `frontend-2.0-anchor-planner/` submodule on branch `ATDD`.

## Testing Infrastructure

### Current State
- **Test Framework**: Jest with @testing-library/react
- **ATDD Framework**: Custom DSL/Protocol Driver pattern
- **Coverage**: ~3.5% statements, 1.7% branches (very low)

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
```

## Key Files for Testing Tasks

### TEST-001: Empty index.test.tsx
- File: `src/app/index.test.tsx`
- Issue: Contains only `import "@testing-library/jest-dom";` - no actual tests
- This causes test suite issues

### TEST-002: ATDD Stub Tests
- Location: `test/acceptance/linear/*.test.ts`
- 7 test files with ~45 tests total
- All are `expect(true).toBe(true)` placeholders
- DSL classes exist but need connection to tests

### TEST-003: Code Coverage
Focus areas for coverage improvement:
- `src/app/services/analysis/*.ts` - Health calculation logic
- `src/app/services/config/configManager.ts` - Configuration singleton
- `src/app/utils/data/loadLiveData.ts` - Data loading utilities

Analysis services:
- `combinedAnchorAnalysis.ts`
- `coverageAnalysis.ts`
- `maintenanceAnalysis.ts`
- `rssiInterpolation.ts`

### TEST-004: GatewayHealthDSL Completion
- DSL: `test/acceptance/dsl/gateway_health_dsl.ts` (378 LOC, complete)
- Protocol Driver: `test/acceptance/dsl/protocol_drivers/gateway_health_protocol_driver.ts`
- Missing: `@/services/atdd/gateway_health_system.ts` (SUT)
- Missing: `@/services/atdd/types.ts` (type definitions)

## ATDD Architecture

```
Test File (*.test.ts)
    │
    ▼
DSL Class (Given/When/Then methods)
    │
    ▼
Protocol Driver (translates to system calls)
    │
    ▼
System Under Test (actual component/service)
```

## Expert Guidelines

### Playwright Expert (tests)
- Page Object Model pattern
- Canvas/map testing with coordinate clicks
- Wait strategies for async operations
- Screenshot capture for debugging

### Orchestrator Expert (coverage)
- Route to appropriate domain experts
- Cross-cutting concerns
- Session management

## Validation Commands
```bash
# TypeScript check
pnpm exec tsc --noEmit

# ESLint
pnpm lint:check

# Run tests
pnpm test

# Format
pnpm format:write
```
