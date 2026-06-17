# Migration Guide - Applying Code Quality to Existing Code

This guide helps you apply the new code quality standards to your existing codebase.

## 📋 Overview

The code quality setup is now installed, but your existing code may need updates to comply with the new standards. This guide walks you through the migration process.

---

## 🚀 Step-by-Step Migration

### Step 1: Install Development Environment

```bash
make install-dev
```

This installs all tools and sets up pre-commit hooks.

### Step 2: Run Initial Assessment

Check the current state of your codebase:

```bash
# Check linting issues (no changes)
make lint > lint-report.txt 2>&1

# Check formatting issues (no changes)
make format-check > format-report.txt 2>&1

# Count issues
echo "Linting issues found:"
grep -c "error" lint-report.txt || echo "0"

echo "Formatting issues found:"
grep -c "would reformat" format-report.txt || echo "0"
```

### Step 3: Auto-Fix What You Can

Ruff can automatically fix many issues:

```bash
# Fix linting issues automatically
make lint-fix

# Format all code
make format
```

**Expected output:**
- Ruff will fix import sorting, trailing whitespace, unused imports, etc.
- Code will be reformatted to match style guidelines

### Step 4: Review Changes

```bash
# See what changed
git diff

# Review by file
git diff --stat
```

**Important:** Review changes carefully before committing. Auto-fixes are usually safe, but verify critical logic wasn't affected.

### Step 5: Fix Remaining Issues Manually

Some issues require manual fixes:

```bash
# See remaining linting issues
make lint
```

Common manual fixes needed:

#### Unused Variables

```python
# Before (Ruff error: F841)
def process_data():
    result = calculate()  # Unused variable
    return True

# After - Use the variable
def process_data():
    result = calculate()
    return result

# Or - Prefix with underscore if intentionally unused
def process_data():
    _result = calculate()  # Marked as intentionally unused
    return True
```

#### Complex Functions

```python
# Before (Ruff error: C901 - too complex)
def complex_function(data):
    if condition1:
        if condition2:
            if condition3:
                # ... deeply nested logic
                pass

# After - Extract functions
def complex_function(data):
    if not is_valid(data):
        return None
    return process_valid_data(data)

def is_valid(data):
    return condition1 and condition2 and condition3

def process_valid_data(data):
    # ... processing logic
    pass
```

#### Security Issues

```python
# Before (Bandit warning: S106 - hardcoded password)
PASSWORD = "secret123"

# After - Use environment variables
import os
PASSWORD = os.getenv("PASSWORD")

# Or - Use configuration
from src.app.config.app_config import app_config
PASSWORD = app_config.password
```

### Step 6: Update Tests

Ensure tests still pass after formatting:

```bash
# Run tests
make test

# Run with coverage
make coverage
```

If tests fail:
1. Review test logic - formatting shouldn't break tests
2. Update test fixtures if needed
3. Fix any issues introduced by refactoring

### Step 7: Address Type Checking (Optional but Recommended)

```bash
# Run type checker
make type-check > mypy-report.txt 2>&1

# Review issues
cat mypy-report.txt
```

Add type hints gradually:

```python
# Before
def get_user(user_id):
    return repository.find(user_id)

# After
from typing import Optional
from src.app.features.users.domain.entities.user_entity import UserEntity

def get_user(user_id: int) -> Optional[UserEntity]:
    return repository.find(user_id)
```

### Step 8: Run Security Scan

```bash
# Check for security issues
make security
```

Address any critical security issues found.

### Step 9: Commit Changes

```bash
# Stage all changes
git add .

# Commit with proper message
git commit -m "style: apply code quality standards with Ruff

- Format all Python files with Ruff
- Fix linting issues (imports, unused vars, etc.)
- Update code to comply with project standards
- All tests passing after formatting"
```

Pre-commit hooks will run automatically. If they fail:

```bash
# Fix issues
make lint-fix format

# Try commit again
git commit --amend --no-edit
```

---

## 🔍 Dealing with Large Codebases

If you have hundreds of files, migrate incrementally:

### Option 1: Migrate by Module

```bash
# Fix one module at a time
ruff check --fix src/app/features/users/
ruff format src/app/features/users/

# Commit
git add src/app/features/users/
git commit -m "style(users): apply code quality standards"

# Repeat for other modules
```

### Option 2: Migrate by Issue Type

```bash
# Fix only import issues
ruff check --select I --fix .

# Fix only unused imports
ruff check --select F401 --fix .

# Fix only formatting
ruff format .
```

### Option 3: Gradual Migration with Baseline

Create a baseline to ignore existing issues:

```bash
# Generate baseline (ignore current issues)
ruff check . --output-format=json > .ruff-baseline.json

# Only new code must pass checks
# (Note: This is a manual approach, Ruff doesn't have built-in baseline)
```

---

## 🛠️ Handling Specific Issues

### Large Number of Import Sorting Changes

Ruff will reorganize imports according to standards:

```python
# Before (mixed order)
import os
from fastapi import APIRouter
import sys
from src.app.features.users.domain import UserEntity

# After (organized by Ruff)
import os
import sys

from fastapi import APIRouter

from src.app.features.users.domain import UserEntity
```

**Action:** Accept these changes - they improve readability.

### Line Length Violations

Some lines may exceed 120 characters:

```python
# Before (140 characters)
very_long_function_call_with_many_parameters(param1, param2, param3, param4, param5, param6, param7, param8)

# After (formatted by Ruff)
very_long_function_call_with_many_parameters(
    param1, param2, param3, param4,
    param5, param6, param7, param8
)
```

If you need to adjust line length, edit `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120  # Default; adjust if needed
```

### False Positives

If Ruff flags something incorrectly:

```python
# Ignore specific rule for one line
result = eval(expression)  # noqa: S307

# Ignore all rules for one line (not recommended)
result = eval(expression)  # noqa

# Ignore for entire file (add at top)
# ruff: noqa: S307
```

Update `pyproject.toml` to ignore globally:

```toml
[tool.ruff.lint]
ignore = [
    "S307",  # Use of eval
]
```

---

## 🧪 Testing After Migration

### Run Full Test Suite

```bash
# Unit tests
make test-unit

# Integration tests (requires database)
make test-integration

# E2E tests
make test-e2e

# All tests with coverage
make coverage-all
```

### Verify Local Quality

Ensure all checks pass before pushing:

```bash
# Unit tests
make test-unit

# Integration tests (requires database)
make test-integration

# E2E tests
make test-e2e

# All tests with coverage
make coverage-all
```

Quality enforcement is handled by pre-commit hooks that run automatically on `git commit`.

---

## 📊 Before/After Comparison

Track your progress:

```bash
# Before migration
make lint 2>&1 | tee before-lint.txt
make format-check 2>&1 | tee before-format.txt

# After migration
make lint 2>&1 | tee after-lint.txt
make format-check 2>&1 | tee after-format.txt

# Compare
echo "Before: $(grep -c 'error' before-lint.txt) errors"
echo "After: $(grep -c 'error' after-lint.txt) errors"
```

---

## 🎯 Goal: Zero Violations

**Target:** No linting errors, no formatting issues

```bash
# This should pass cleanly
make lint && echo "✅ Linting passed"
make format-check && echo "✅ Formatting passed"
make test && echo "✅ Tests passed"
```

---

## 🔄 Ongoing Maintenance

### Pre-commit Hooks

Hooks prevent new issues:

```bash
# Installed automatically with make install-dev
pre-commit install
```

Now every commit runs quality checks automatically.

### Manual Checks

Before pushing:

```bash
make lint-fix format test
```

### CI/CD Enforcement

GitHub Actions will reject PRs with quality issues.

---

## 📝 Checklist

- [ ] Installed dev environment (`make install-dev`)
- [ ] Ran initial assessment (`make lint`, `make format-check`)
- [ ] Auto-fixed issues (`make lint-fix`, `make format`)
- [ ] Reviewed changes (`git diff`)
- [ ] Fixed remaining manual issues
- [ ] Tests still pass (`make test`)
- [ ] Addressed security issues (`make security`)
- [ ] Committed changes with proper message
- [ ] Pre-commit hooks working
- [ ] CI/CD passing
- [ ] Zero violations achieved

---

## 🆘 Troubleshooting

### "Too many changes!"

- Migrate incrementally by module or feature
- Review changes in small batches
- Use `git add -p` for selective staging

### "Tests failing after formatting"

- Formatting shouldn't break logic
- Check for accidental changes in test assertions
- Verify fixtures and mock data

### "Pre-commit hooks too slow"

- Skip MyPy hook temporarily (comment out in `.pre-commit-config.yaml`)
- Run full checks in CI only
- Use `git commit --no-verify` sparingly

### "Ruff conflicts with existing tools"

- Remove old tools (black, isort, flake8)
- Uninstall old pre-commit hooks
- Use only Ruff for consistency

---

## 🎉 Success!

Once migration is complete, you'll have:
- ✅ Consistent code formatting
- ✅ No linting violations
- ✅ Automated quality checks
- ✅ Clean commit history
- ✅ CI/CD enforcement

**Your codebase is now production-ready!** 🚀
