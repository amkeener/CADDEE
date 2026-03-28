# Project Report ADW

Generate a comprehensive project status report with grades across multiple dimensions.

## Variables

OUTPUT_PATH: project/PROJECT_REVIEW_{YYYY-MM-DD}.md
SESSION_ID: adw-report-{timestamp}

## Instructions

### 1. Initialize ADW Session

```
Session: adw-report-{YYYYMMDD-HHMMSS}
Directory: adws/sessions/{session_id}/
```

### 2. Gather Project Statistics

Run these commands to collect metrics:

```bash
# Total lines of code
find . -name "*.rs" -o -name "*.dart" | xargs wc -l 2>/dev/null | tail -1

# File counts by type
find . -name "*.rs" | wc -l
find wallet-app -name "*.dart" | wc -l

# Rust test count
cd trustchain-core && cargo test --no-run 2>&1 | grep -c "test " || cargo test 2>&1 | grep -E "^test result" | head -1

# Flutter test count
cd wallet-app && flutter test --reporter compact 2>&1 | grep -E "^\+[0-9]+" | tail -1
```

### 3. Assess Feature Completeness

Read and analyze these key files:
- `project/BACKLOG.md` - Outstanding work items
- `project/ROADMAP.md` - Current priorities
- `project/code_reviews/coverage-tracker.md` - Review coverage
- `CHANGELOG.md` - Recent changes

#### Feature Categories to Assess

**Core Blockchain:**
- Consensus mechanism
- Trust scoring system
- Smart contract runtime
- P2P networking
- State management
- Transaction types
- Validator selection

**Wallet App:**
- Send/Receive
- NFC Payments
- Chat
- Exchange
- Disputes
- Profiles
- TNS
- Mining
- NFTs

**Smart Contracts:**
- Exchange
- Bridge
- NFT Marketplace
- Commerce SDK
- Credentials

**Cross-Chain:**
- Ethereum bridge
- Bitcoin bridge
- Atomic swaps
- Multisig

### 4. Security Assessment

Read recent security-related code reviews:
```bash
ls -la project/code_reviews/*security*.md project/code_reviews/*trust*.md project/code_reviews/*ffi*.md 2>/dev/null
```

Check `project/BACKLOG.md` for:
- Security Debt section
- HIGH priority items
- Outstanding vulnerabilities

#### Security Checklist
- [ ] Cryptographic choices documented
- [ ] Memory safety (zeroization)
- [ ] FFI boundary safety
- [ ] Consensus security
- [ ] Cross-chain security
- [ ] Input validation
- [ ] Authentication/Authorization

### 5. Test Coverage Analysis

**Rust Coverage:**
```bash
cd trustchain-core && cargo test 2>&1 | grep -E "^test result|running [0-9]+ tests"
```

Assess by crate:
- trustchain-primitives
- trustchain-crypto
- trustchain-trust
- trustchain-state
- trustchain-consensus
- trustchain-network
- trustchain-runtime
- trustchain-node
- trustchain-ffi
- contracts/*
- E2E tests

**Flutter Coverage:**
```bash
cd wallet-app && flutter test 2>&1 | grep -E "tests passed|All tests passed"
```

Assess by category:
- Provider tests
- Widget tests
- Integration tests

### 6. Code Quality Assessment

Check for:
```bash
# Rust lints
cd trustchain-core && cargo clippy 2>&1 | grep -c "warning:"

# Flutter analyze
cd wallet-app && flutter analyze 2>&1 | grep -c "info\|warning\|error"
```

Review:
- Architecture clarity
- Error handling patterns
- Documentation coverage
- Code style consistency
- Code review coverage %

### 7. Ecosystem Usefulness Assessment

Evaluate:
- Unique value propositions
- Innovation level
- Technical depth
- Mobile UX quality
- Developer tools
- Ecosystem readiness

### 8. Calculate Grades

Use this weighted scoring:

| Category | Weight | Score Range |
|----------|--------|-------------|
| Feature Completeness | 25% | 0-100 |
| Security | 25% | 0-100 |
| Test Coverage | 20% | 0-100 |
| Code Quality | 15% | 0-100 |
| Ecosystem Value | 15% | 0-100 |

**Grade Scale:**
- A+ (97-100), A (93-96), A- (90-92)
- B+ (87-89), B (83-86), B- (80-82)
- C+ (77-79), C (73-76), C- (70-72)
- D+ (67-69), D (63-66), D- (60-62)
- F (<60)

### 9. Generate Report

Write to: `project/PROJECT_REVIEW_{YYYY-MM-DD}.md`

**Report Structure:**

```markdown
# TrustChain Project Review - {Month} {Day}, {Year}

## Executive Summary

{2-3 sentence overview of project state}

**Overall Grade: {LETTER} ({SCORE}/100)**

---

## Project Statistics

| Metric | Value |
|--------|-------|
| **Total Lines of Code** | ~{N} |
| **Rust Files** | {N} |
| **Dart/Flutter Files** | {N} |
| **Rust Tests** | {N} passing |
| **Flutter Tests** | {N} passing |
| **Code Review Coverage** | {N}% ({done}/{total} modules) |
| **Feature Completeness** | ~{N}% |

---

## Feature Completeness Assessment

### Core Blockchain ({N}%)

| Feature | Status | Notes |
|---------|--------|-------|
| {Feature} | ✅ Complete / 🔶 Partial / ❌ Missing | {Notes} |
...

### Wallet App ({N}%)
{Same table format}

### Smart Contracts ({N}%)
{Same table format}

### Cross-Chain ({N}%)
{Same table format}

---

## Security Assessment

### Strengths
1. {Strength}
...

### Outstanding Security Debt ({N} HIGH items)

| ID | Issue | Complexity | Risk |
|----|-------|------------|------|
| H{N} | {Issue} | {trivial/simple/moderate/complex} | {Risk description} |
...

### Security Grade: {LETTER} ({SCORE}/100)

{1-2 sentence summary}

---

## Test Coverage Analysis

### Rust Coverage by Crate

| Crate | Tests | Assessment |
|-------|-------|------------|
| {crate} | {N} | Excellent/Good/Adequate/Poor |
...

### Flutter Coverage

| Category | Tests | Assessment |
|----------|-------|------------|
| {category} | {N} | Excellent/Good/Adequate/Poor |
...

### Test Grade: {LETTER} ({SCORE}/100)

---

## Code Quality Assessment

### Strengths
- {Strength}
...

### Areas for Improvement
- {Area}
...

### Code Quality Grade: {LETTER} ({SCORE}/100)

---

## Ecosystem Usefulness Assessment

### Unique Value Propositions
1. {UVP}
...

### Market Position

| Aspect | Assessment |
|--------|------------|
| Innovation | **High/Moderate/Low** - {reason} |
| Technical Depth | **High/Moderate/Low** - {reason} |
| Mobile UX | **Good/Moderate/Poor** - {reason} |
| Developer Tools | **Good/Moderate/Poor** - {reason} |
| Ecosystem Readiness | **Good/Moderate/Poor** - {reason} |

### Ecosystem Grade: {LETTER} ({SCORE}/100)

---

## Overall Project Grade

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Feature Completeness | 25% | {N} | {N*0.25} |
| Security | 25% | {N} | {N*0.25} |
| Test Coverage | 20% | {N} | {N*0.20} |
| Code Quality | 15% | {N} | {N*0.15} |
| Ecosystem Value | 15% | {N} | {N*0.15} |
| **Total** | **100%** | | **{SUM}** |

## **Final Grade: {LETTER} ({SCORE}/100)**

---

## Recommendations

### Immediate (Before {Next Milestone})
1. {Recommendation}
...

### Short-Term ({Timeframe})
1. {Recommendation}
...

### Medium-Term ({Timeframe})
1. {Recommendation}
...

---

## Changes Since Last Review

{If previous review exists, summarize key changes}

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Overall Grade | {X} | {Y} | {+/-} |
| Security Grade | {X} | {Y} | {+/-} |
| Test Count | {X} | {Y} | {+/-} |
...

---

*Review conducted by Claude Code (Opus 4.5) on {YYYY-MM-DD}*
```

### 10. Log to Audit Trail

```bash
python3 scripts/adw_audit.py log \
  --session "{session_id}" \
  --event "report_generated" \
  --workflow "project_report_adw" \
  --output-files "project/PROJECT_REVIEW_{date}.md" \
  --status "success" \
  --next-workflow "plan_adw"
```

### 11. Compare to Previous Review (Optional)

If a previous `PROJECT_REVIEW_*.md` exists:
1. Read the previous review
2. Compare grades across categories
3. Add "Changes Since Last Review" section
4. Highlight improvements and regressions

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│  /project_report_adw                                                │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. Initialize ADW session                                          │
│  2. Gather project statistics (LOC, files, tests)                   │
│  3. Read BACKLOG.md, ROADMAP.md, coverage-tracker.md                │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. Assess each dimension:                                          │
│     ├── Feature Completeness (25%)                                  │
│     ├── Security (25%)                                              │
│     ├── Test Coverage (20%)                                         │
│     ├── Code Quality (15%)                                          │
│     └── Ecosystem Value (15%)                                       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. Calculate weighted scores and letter grades                     │
│  6. Generate recommendations by timeframe                           │
│  7. Compare to previous review (if exists)                          │
│  8. Write report to project/PROJECT_REVIEW_{date}.md                │
│  9. Log to audit trail                                              │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Output: project/PROJECT_REVIEW_{YYYY-MM-DD}.md                     │
│  With: Executive summary, grades, recommendations                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Output

Return the path and summary:
```
Project Report Generated: project/PROJECT_REVIEW_{date}.md

Overall Grade: {LETTER} ({SCORE}/100)

| Category | Grade |
|----------|-------|
| Feature Completeness | {LETTER} |
| Security | {LETTER} |
| Test Coverage | {LETTER} |
| Code Quality | {LETTER} |
| Ecosystem Value | {LETTER} |

Key Recommendations:
1. {Top recommendation}
2. {Second recommendation}
3. {Third recommendation}
```

---

## Examples

**Example 1: Generate new report**
```
/project_report_adw
```

Generates full project review with all dimensions graded.

**Example 2: Focus on specific area**
```
/project_report_adw --focus security
```

Generates report with deeper security analysis.

---

## Notes

- Run this monthly or at major milestones
- Compare to previous reviews to track progress
- Use grades to prioritize work (lowest grades = highest priority)
- Recommendations feed into BACKLOG.md and sprint planning
- Archive old roadmap files when they become obsolete
