# Conditional Documentation Guide

This guide helps determine what documentation to read based on the task at hand. Only read docs when conditions match - avoid excessive reading.

## Instructions
1. Review the task you've been asked to perform
2. Check each section below for matching conditions
3. Only read documentation if a condition applies to your task

## Conditional Documentation

### Core Documentation

- **project/backlog.md**
  - When checking work item status or priorities
  - When starting a new feature, bug, or chore
  - When looking for next tasks to work on

- **project/roadmap.md** (if exists)
  - When understanding current implementation priorities
  - When checking milestone status
  - When reviewing completed vs pending features

- **wip_summary.md**
  - When resuming work from a previous session
  - When checking what was last worked on

### ADW Framework

- **.claude/commands/experts/*/expertise.yaml**
  - When working in a specific domain
  - When needing domain-specific guidelines
  - When checking validation commands

- **adws/sessions/{session_id}/state.json**
  - When resuming an ADW session
  - When checking workflow progress

### Code Reviews

- **project/code_reviews/coverage-tracker.md**
  - When running /code_review
  - When checking review coverage status
  - When planning review work

### Testing

- **CLAUDE.md**
  - When checking project conventions
  - When verifying commit format
  - When understanding project structure

### Feature Documentation

- **app_docs/feature-2-issue-crud-tests.md**
  - When writing or modifying Issue-related tests
  - When adding new test fixtures for site monitoring services
  - When understanding the test patterns for domain entity and service tests

<!--
## Project-Specific Documentation

Add project-specific documentation sections below. Example format:

### Backend API

- **src/api/routes.ts**
  - When adding or modifying API endpoints
  - When working with request/response handling

### Database

- **src/db/schema.ts**
  - When working with database models
  - When modifying migrations

### Frontend Components

- **src/components/README.md**
  - When creating new components
  - When understanding component patterns

### Configuration

- **config/README.md**
  - When modifying environment settings
  - When adding new configuration options
-->
