# Security Audit

This directory contains GitHub Actions workflows for automated security checks.

## Workflows

### `security.yml` - Dependency Vulnerability Scan

Scans Python dependencies for known vulnerabilities using `pip-audit`.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Weekly on Mondays at 8:00 AM UTC (scheduled)
- Manual trigger via `workflow_dispatch`

**What it does:**
1. Runs `pip-audit` on `requirements.txt`
2. Generates JSON audit report
3. Uploads audit results as artifacts (retained for 30 days)
4. **Fails the build** if any critical or high severity vulnerabilities are found

**Running locally:**

```bash
# Install pip-audit
pip install pip-audit

# Run audit
pip-audit --requirement requirements.txt

# Generate JSON report
pip-audit --requirement requirements.txt --format json --output audit-results.json

# View summary
pip-audit --requirement requirements.txt --format json | jq '.dependencies[] | select(.vulns | length > 0)'
```

**Interpreting results:**

The workflow checks for vulnerabilities with `critical` or `high` severity levels and fails the build if any are found. Medium and low severity vulnerabilities will be reported but won't fail the build.

**Fixing vulnerabilities:**

When vulnerabilities are found:
1. Check the audit output for affected packages and fix versions
2. Update `requirements.txt` with the recommended fix versions
3. Test the application thoroughly after updating dependencies
4. Re-run the audit to confirm the vulnerabilities are resolved

**Example output:**

```
Found 5 known vulnerabilities in 4 packages
Name          Version ID             Fix Versions
------------- ------- -------------- ------------
pyjwt         2.10.1  CVE-2026-32597 2.12.0
python-dotenv 1.0.1   CVE-2026-28684 1.2.2
pytest        8.3.4   CVE-2025-71176 9.0.3
starlette     0.46.2  CVE-2025-54121 0.47.2
```

## Security Best Practices

1. **Keep dependencies up to date** - Regularly update dependencies to get security patches
2. **Review audit results** - Don't ignore security warnings, even for low severity issues
3. **Test after updates** - Always run full test suite after dependency updates
4. **Monitor scheduled runs** - Check weekly audit results for new vulnerabilities
5. **Pin versions** - Use exact version pinning in `requirements.txt` for reproducible builds

## Resources

- [pip-audit documentation](https://pypi.org/project/pip-audit/)
- [NIST National Vulnerability Database](https://nvd.nist.gov/)
- [GitHub Security Advisories](https://github.com/advisories)
