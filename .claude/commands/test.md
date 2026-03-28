# Application Validation Test Suite

Execute comprehensive validation tests, auto-detecting the project type and running the appropriate checks. Returns results in a standardized JSON format for automated processing.

## Purpose

Proactively identify and fix issues in the application before they impact users or developers. By running this comprehensive test suite, you can:
- Detect syntax errors, type mismatches, and import failures
- Identify broken tests or security vulnerabilities
- Verify build processes and dependencies
- Ensure the application is in a healthy state

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- First, detect the project type (see Project Type Detection below)
- Execute each test in the sequence for the detected project type
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- Error Handling:
  - If a command returns non-zero exit code, mark as failed and immediately stop processing tests
  - Capture stderr output for error field
  - Timeout commands after `TEST_COMMAND_TIMEOUT`
  - IMPORTANT: If a test fails, stop processing tests and return the results thus far
- Test execution order is important - dependencies should be validated first
- All file paths are relative to the project root
- Always run `pwd` before the first test to confirm you're in the correct directory

## Project Type Detection

Detect the project type by checking for marker files **in the current working directory**:

| Marker | Project Type |
|--------|-------------|
| `*.sln` file exists | **.NET** |
| `package.json` exists | **Node/TypeScript** |
| `pubspec.yaml` exists | **Flutter/Dart** |
| `pyproject.toml` or `requirements.txt` exists | **Python** |

If multiple markers exist, prefer: .NET > Flutter > Node > Python

## Test Execution Sequences

### .NET Projects

1. **Solution Build**
   - Command: `dotnet build <solution-file>.sln`
   - test_name: "dotnet_build"
   - test_purpose: "Validates the complete .NET solution build across all projects, catching compilation errors, missing references, and type mismatches"

2. **Unit Tests**
   - Command: `dotnet test <test-project-path> --filter "FullyQualifiedName!~Integration"` (if a test project exists)
   - test_name: "dotnet_unit_tests"
   - test_purpose: "Validates all unit tests excluding Docker/DB-dependent integration tests"
   - Note: Find the test project by looking for `*.Tests.csproj` or `*.Test.csproj`. If none found, skip this step.
   - Note: If all tests pass, include the pass/fail/skip counts in the test_purpose field.

3. **Integration Tests** (optional)
   - Command: `dotnet test <test-project-path> --filter "FullyQualifiedName~Integration"`
   - test_name: "dotnet_integration_tests"
   - test_purpose: "Validates integration tests against real infrastructure (Docker, database)"
   - Note: Only run if the user explicitly requests integration tests. Otherwise skip and note "skipped (requires Docker)" in results.

### Node/TypeScript Projects

1. **TypeScript Type Check**
   - Command: `npx tsc --noEmit` (or `pnpm tsc --noEmit` / `bun tsc --noEmit` depending on package manager)
   - test_name: "typescript_check"
   - test_purpose: "Validates TypeScript type correctness without generating output files, catching type errors, missing imports, and incorrect function signatures"
   - Note: Detect package manager from lock file: `pnpm-lock.yaml` → pnpm, `bun.lockb` → bun, `yarn.lock` → yarn, else npm.

2. **Linting**
   - Command: `<pm> run lint` or `<pm> run lint:check` (whichever exists in package.json scripts)
   - test_name: "frontend_linting"
   - test_purpose: "Validates code quality using the project's configured linter (ESLint, etc.)"
   - Note: Check `package.json` scripts for a lint command. If none found, skip.

3. **Build**
   - Command: `<pm> run build`
   - test_name: "frontend_build"
   - test_purpose: "Validates the complete build process including bundling, asset optimization, and production compilation"

4. **Tests**
   - Command: `<pm> test` or `<pm> run test` (whichever exists in package.json scripts)
   - test_name: "frontend_tests"
   - test_purpose: "Validates all unit and component tests"
   - Note: Check `package.json` scripts for a test command. If none found, skip.

### Flutter/Dart Projects

1. **Dart Analysis**
   - Command: `flutter analyze`
   - test_name: "dart_analyze"
   - test_purpose: "Validates Dart code quality and type correctness using static analysis"

2. **Flutter Build**
   - Command: `flutter build apk --debug` (or `flutter build web` if web-only)
   - test_name: "flutter_build"
   - test_purpose: "Validates the complete Flutter build process"

3. **Flutter Tests**
   - Command: `flutter test`
   - test_name: "flutter_tests"
   - test_purpose: "Validates all unit and widget tests"

### Python Projects

1. **Python Syntax Check**
   - Command: `python -m py_compile <main-files>` (or `uv run python -m py_compile` if uv is used)
   - test_name: "python_syntax_check"
   - test_purpose: "Validates Python syntax by compiling source files to bytecode"

2. **Code Quality Check**
   - Command: `ruff check .` (or `uv run ruff check .`)
   - test_name: "python_linting"
   - test_purpose: "Validates Python code quality, identifies unused imports, style violations, and potential bugs"
   - Note: If ruff is not available, try `flake8` or skip.

3. **Python Tests**
   - Command: `pytest tests/ -v --tb=short` (or `uv run pytest tests/ -v --tb=short`)
   - test_name: "python_tests"
   - test_purpose: "Validates all backend functionality"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test
- This allows subsequent agents to quickly identify and resolve errors

### Output Structure

```json
[
  {
    "test_name": "string",
    "passed": boolean,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  },
  ...
]
```

### Example Output (.NET)

```json
[
  {
    "test_name": "dotnet_build",
    "passed": true,
    "execution_command": "dotnet build Wakecap.OnSiteSupport.sln",
    "test_purpose": "Validates the complete .NET solution build across all 7 projects, catching compilation errors, missing references, and type mismatches. 0 errors, 55 warnings (all pre-existing)."
  },
  {
    "test_name": "dotnet_unit_tests",
    "passed": true,
    "execution_command": "dotnet test Wakecap.OnSiteSupport.Tests/Wakecap.OnSiteSupport.Tests.csproj --filter \"FullyQualifiedName!~Integration\"",
    "test_purpose": "Validates all unit tests excluding Docker/DB-dependent integration tests. Passed: 83, Failed: 0, Skipped: 0."
  },
  {
    "test_name": "dotnet_integration_tests",
    "passed": false,
    "execution_command": "dotnet test Wakecap.OnSiteSupport.Tests/Wakecap.OnSiteSupport.Tests.csproj --filter \"FullyQualifiedName~Integration\"",
    "test_purpose": "Validates integration tests against real infrastructure (Docker, database)",
    "error": "skipped (requires Docker)"
  }
]
```

### Example Output (Node/TypeScript)

```json
[
  {
    "test_name": "typescript_check",
    "passed": true,
    "execution_command": "pnpm tsc --noEmit",
    "test_purpose": "Validates TypeScript type correctness without generating output files"
  },
  {
    "test_name": "frontend_build",
    "passed": false,
    "execution_command": "pnpm run build",
    "test_purpose": "Validates the complete frontend build process",
    "error": "TS2345: Argument of type 'string' is not assignable to parameter of type 'number'"
  }
]
```
