# Secret Scanning Guide

**MorningAI Platform - Security Best Practices**  
**Date**: 2025-10-24  
**Status**: ✅ Active  
**Priority**: P0 (Critical Security)

---

## Overview

This guide explains the secret scanning system implemented to prevent accidental exposure of sensitive credentials, API keys, tokens, and other secrets in the codebase.

### Tools Used

1. **Gitleaks** - Fast, lightweight secret scanner
2. **TruffleHog** - Deep secret scanner with verification capabilities

Both tools run automatically on every push and pull request to protect the repository from credential leaks.

---

## How It Works

### Automatic Scanning

The secret scanning workflow (`.github/workflows/secret-scanning.yml`) runs automatically:

- **On Push**: Scans commits pushed to `main` branch
- **On Pull Request**: Scans all commits in the PR before merge
- **Manual Trigger**: Can be triggered manually via GitHub Actions UI

### Scan Process

```
┌─────────────────────────────────────────────────────────────┐
│  1. Developer pushes code or creates PR                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  2. GitHub Actions triggers secret-scanning.yml             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├──────────────────┬──────────────────────────┐
                 ▼                  ▼                          ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────┐
│  Gitleaks Scan       │  │  TruffleHog Scan     │  │  Summary       │
│  - Fast detection    │  │  - Deep analysis     │  │  - Report      │
│  - Pattern matching  │  │  - Verification      │  │  - Block merge │
└──────────┬───────────┘  └──────────┬───────────┘  └────────┬───────┘
           │                         │                        │
           └─────────────────────────┴────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  ✅ Pass: No secrets detected  │
                    │  ❌ Fail: Secrets found        │
                    │  → Block PR merge              │
                    └────────────────────────────────┘
```

---

## Configuration Files

### 1. `.gitleaksignore`

Specifies false positives to ignore:

```gitignore
# Test files with example credentials
**/tests/**/*test*.py:*example*

# Documentation examples
docs/**/*.md:*example*

# Public configuration
.env.example:*
```

**When to update**:
- Add legitimate false positives (test fixtures, documentation examples)
- Use specific file:line:hash format for precision
- Document why each entry is safe

### 2. `.trufflehog.yaml`

Configures TruffleHog behavior:

```yaml
only-verified: true  # Only report verified secrets

exclude-paths:
  - node_modules/
  - .git/
  - dist/

exclude-globs:
  - "**/tests/**/*test*.py"
  - "**/__tests__/**/*.ts"
```

**Key settings**:
- `only-verified: true` - Reduces false positives by verifying secrets
- `exclude-paths` - Directories to skip
- `max-file-size` - Skip large binary files

---

## What Gets Detected

### Secrets Detected by Gitleaks

- AWS Access Keys
- GitHub Personal Access Tokens
- Slack Tokens
- Stripe API Keys
- OpenAI API Keys
- Database Connection Strings
- Private Keys (RSA, SSH)
- Generic API Keys (patterns like `api_key_[a-zA-Z0-9]{32}`)
- OAuth Tokens
- JWT Tokens
- And 100+ more patterns

### Secrets Detected by TruffleHog

- All of the above, plus:
- **Verified Secrets**: TruffleHog attempts to verify if secrets are active
- Custom patterns defined in `.trufflehog.yaml`
- Historical secrets in git history

---

## What to Do If Secrets Are Detected

### ❌ DO NOT

- ❌ Commit secrets to the repository
- ❌ Push secrets to GitHub
- ❌ Ignore secret detection warnings
- ❌ Add real secrets to `.gitleaksignore` to bypass checks

### ✅ DO

1. **Stop immediately** - Do not push the code
2. **Remove the secret** from the code
3. **Rotate the credential** immediately (assume it's compromised)
4. **Use environment variables** instead:
   ```python
   # ❌ Bad
   API_KEY = "sk_live_abc123..."
   
   # ✅ Good
   import os
   API_KEY = os.getenv("API_KEY")
   ```
5. **Update `.env.example`** with placeholder values
6. **Document** the required environment variable in `env_schema.yaml`

### If Secret Was Already Pushed

If a secret was accidentally pushed to GitHub:

1. **Rotate the credential immediately** (assume it's compromised)
2. **Remove the secret** from the code
3. **Rewrite git history** (if needed):
   ```bash
   # Use BFG Repo-Cleaner or git-filter-repo
   git filter-repo --path-glob '**/*.env' --invert-paths
   ```
4. **Force push** (only if absolutely necessary):
   ```bash
   git push --force-with-lease origin main
   ```
5. **Notify the team** about the incident

---

## Best Practices

### 1. Use Environment Variables

Always use environment variables for sensitive data:

```python
# Python
import os
API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# TypeScript
const apiKey = process.env.VITE_API_KEY;
const dbUrl = process.env.DATABASE_URL;
```

### 2. Use `.env.example` for Documentation

Create `.env.example` with placeholder values:

```bash
# .env.example
API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/db
STRIPE_SECRET_KEY=sk_test_...
```

### 3. Add Secrets to `.gitignore`

Ensure sensitive files are ignored:

```gitignore
# .gitignore
.env
.env.local
.env.production
*.pem
*.key
credentials.json
secrets.yaml
```

### 4. Use Secret Management Services

For production:
- **GitHub Secrets**: For CI/CD workflows
- **Vercel Environment Variables**: For frontend deployments
- **Render Environment Variables**: For backend deployments
- **Supabase Secrets**: For database credentials
- **AWS Secrets Manager** / **HashiCorp Vault**: For enterprise

### 5. Regular Security Audits

Run manual scans periodically:

```bash
# Scan entire repository history
docker run --rm -v "$PWD:/pwd" trufflesecurity/trufflehog:latest \
  filesystem /pwd --json

# Scan with Gitleaks
docker run --rm -v "$PWD:/path" zricethezav/gitleaks:latest \
  detect --source="/path" -v
```

---

## Handling False Positives

### Legitimate False Positives

Examples of safe "secrets" that can be ignored:

1. **Test Fixtures**:
   ```python
   # tests/fixtures/auth.py
   FAKE_API_KEY = "test_key_12345"  # Not a real secret
   ```

2. **Documentation Examples**:
   ```markdown
   # docs/API.md
   Example: `Authorization: Bearer YOUR_API_KEY_HERE`
   ```

3. **Public Configuration**:
   ```yaml
   # .env.example
   API_KEY=your_api_key_here
   ```

### Adding to `.gitleaksignore`

```gitignore
# Format: file:line:pattern
tests/fixtures/auth.py:*FAKE_API_KEY*
docs/API.md:*YOUR_API_KEY_HERE*
.env.example:*
```

### Adding to `.trufflehog.yaml`

```yaml
exclude-globs:
  - "**/tests/fixtures/**"
  - "docs/**/*.md"
```

---

## CI/CD Integration

### GitHub Actions Workflow

The workflow runs three jobs:

1. **Gitleaks**: Fast pattern-based detection
2. **TruffleHog**: Deep verification-based detection
3. **Security Summary**: Aggregates results and blocks PR if secrets found

### Status Checks

- ✅ **Pass**: No secrets detected → PR can be merged
- ❌ **Fail**: Secrets detected → PR blocked until resolved

### Viewing Results

1. Go to **Actions** tab in GitHub
2. Click on the failed workflow run
3. Review **Gitleaks** and **TruffleHog** job logs
4. Download artifacts for detailed reports

---

## Troubleshooting

### Issue: False Positive in Test File

**Solution**: Add to `.gitleaksignore`:
```gitignore
tests/test_auth.py:*mock_token*
```

### Issue: TruffleHog Taking Too Long

**Solution**: Reduce scan scope in `.trufflehog.yaml`:
```yaml
exclude-paths:
  - node_modules/
  - dist/
  - build/
```

### Issue: Gitleaks Blocking Legitimate Code

**Solution**: Use specific ignore patterns:
```gitignore
# Ignore specific line in specific file
src/config.ts:42:abc123def456
```

### Issue: Need to Scan Entire History

**Solution**: Run manual scan:
```bash
# Full history scan
docker run --rm -v "$PWD:/pwd" trufflesecurity/trufflehog:latest \
  git file:///pwd --since-commit HEAD~100
```

---

## Compliance & Standards

### Security Standards Met

- ✅ **OWASP Top 10**: Prevents A02:2021 - Cryptographic Failures
- ✅ **PCI DSS**: Requirement 3.4 - Protect cardholder data
- ✅ **GDPR**: Article 32 - Security of processing
- ✅ **SOC 2**: CC6.1 - Logical and physical access controls

### Audit Trail

All secret scanning results are:
- Logged in GitHub Actions
- Stored as artifacts (7-day retention)
- Visible in PR status checks
- Tracked in security summary

---

## Resources

### Documentation

- **Gitleaks**: https://github.com/gitleaks/gitleaks
- **TruffleHog**: https://github.com/trufflesecurity/trufflehog
- **GitHub Secret Scanning**: https://docs.github.com/en/code-security/secret-scanning

### Tools

- **BFG Repo-Cleaner**: https://rtyley.github.io/bfg-repo-cleaner/
- **git-filter-repo**: https://github.com/newren/git-filter-repo
- **git-secrets**: https://github.com/awslabs/git-secrets

### Best Practices

- **OWASP Secrets Management**: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **12-Factor App**: https://12factor.net/config

---

## Support

For questions or issues:
1. Check this guide first
2. Review GitHub Actions logs
3. Contact the security team
4. Create an issue with label `security`

---

**Last Updated**: 2025-10-24  
**Maintained By**: CTO Devin AI  
**Review Frequency**: Quarterly
