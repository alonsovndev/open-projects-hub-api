# Coverage Quick Reference

## 🎯 Target: ≥80% Line Coverage

## 📊 Current Status
```
Coverage: 79% (2801 statements, 602 missed)
Gap: -1% from target
```

## 🚀 Quick Commands

```bash
# Run tests with coverage (fast, no DB)
make coverage

# Open HTML report
make coverage-report

# Run all tests including integration (requires DB)
make coverage-all

# Clean coverage files
make clean
```

## 📁 Key Files

- **CI Workflow:** `.github/workflows/test-coverage.yml`
- **Config:** `.coveragerc`, `pytest.ini`
- **Commands:** `Makefile`
- **Docs:** `docs/testing/coverage-strategy.md`

## 🔍 Analyzing Coverage

```bash
# Terminal report with missing lines
pytest --cov=src/app --cov-report=term-missing -v

# HTML report (best for exploration)
pytest --cov=src/app --cov-report=html -v
open htmlcov/index.html

# Check if threshold met
coverage report --fail-under=80
```

## 🎨 HTML Report Navigation

1. **Run:** `make coverage-report`
2. **Click file** to see line-by-line coverage
3. **Red lines** = not covered
4. **Green lines** = covered
5. **Sort by coverage** to find gaps

## 🏗️ CI/CD Behavior

### ✅ Build Passes If:
- All tests pass
- Coverage ≥ 80%

### ❌ Build Fails If:
- Any test fails
- Coverage < 80%

### 📦 Artifacts (30 days retention):
- HTML coverage report
- XML report (Codecov)
- PR coverage comment

## 📈 Improving Coverage

### 1. Find Gaps
```bash
make coverage
# Look for files with <80% coverage
```

### 2. Open HTML Report
```bash
make coverage-report
# Click red files, see uncovered lines
```

### 3. Add Tests
```python
# Focus on:
# - Error paths
# - Edge cases
# - Exception handlers
# - Domain logic branches
```

### 4. Verify
```bash
make coverage
coverage report --fail-under=80
```

## 🎯 Priority Files (Need Improvement)

| File                      | Coverage | Gap  |
|---------------------------|----------|------|
| `retry_decorator.py`      | 28%      | -52% |
| `config_util.py`          | 67%      | -13% |
| `exception_handlers.py`   | 71%      | -9%  |
| `base_repository.py`      | 75%      | -5%  |

**Quick win:** Add 10-15 tests for these → 80%+

## 🚫 Excluding Code

```python
def debug_only():  # pragma: no cover
    print("Not covered")
```

## 📚 Documentation

Full guide: `docs/testing/coverage-strategy.md`

## 🆘 Help

```bash
make help
pytest --help
coverage --help
```

## 🔗 Resources

- [pytest-cov docs](https://pytest-cov.readthedocs.io/)
- [coverage.py docs](https://coverage.readthedocs.io/)
- Local: `docs/testing/coverage-strategy.md`
