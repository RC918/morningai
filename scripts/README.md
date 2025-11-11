# Scripts Directory

This directory contains Python scripts for various operational tasks including monitoring, migrations, cost reporting, and system verification.

## Environment Configuration

### PYTHONPATH Requirements

All scripts in this directory require proper PYTHONPATH configuration to import modules correctly.

**Required PYTHONPATH**:
```bash
export PYTHONPATH="${WORKSPACE_ROOT}:${WORKSPACE_ROOT}/scripts"
```

Where `WORKSPACE_ROOT` is the repository root directory.

### CI Environment

The CI workflow (`.github/workflows/python-scripts-ci.yml`) automatically sets PYTHONPATH:

```yaml
- name: Set PYTHONPATH
  run: echo "PYTHONPATH=${GITHUB_WORKSPACE}:${GITHUB_WORKSPACE}/scripts" >> $GITHUB_ENV
```

This ensures:
- Repository root is in the Python path (for `common`, `handoff`, etc.)
- `scripts/` directory is in the Python path (for inter-script imports)

### Production/Staging Environment

**IMPORTANT**: Production and staging environments MUST use the same PYTHONPATH configuration as CI.

For production deployments:
```bash
cd /path/to/morningai
export PYTHONPATH="$(pwd):$(pwd)/scripts"
python scripts/monitor_orchestrator.py
```

For systemd services, add to the service file:
```ini
[Service]
Environment="PYTHONPATH=/path/to/morningai:/path/to/morningai/scripts"
WorkingDirectory=/path/to/morningai
ExecStart=/usr/bin/python3 scripts/monitor_orchestrator.py
```

### Local Development

For local testing, set PYTHONPATH before running scripts:

```bash
# From repository root
export PYTHONPATH="$(pwd):$(pwd)/scripts"
python scripts/monitor_orchestrator.py
```

Or use the virtual environment:
```bash
source .venv/bin/activate
export PYTHONPATH="$(pwd):$(pwd)/scripts"
python scripts/monitor_orchestrator.py
```

## Python Version

- **CI**: Python 3.11
- **Production**: Should match CI (Python 3.11+)
- **Local**: Python 3.11+ recommended

**Note**: Some scripts may use Python 3.12+ syntax (e.g., `kg_cost_report.py`). These are documented in the CI workflow denylist.

## CI Workflow

The Python Scripts CI workflow runs on every PR and includes:

1. **Python Syntax Validation**: Checks all scripts for syntax errors
2. **Monitor Orchestrator Tests**: Runs unit tests for monitor scripts
3. **Monitor Integration Check**: Validates monitor script can run (with graceful degradation)

### Branch Protection

The following CI checks are required to pass before merging to `main`:

- ✅ Python Syntax Validation
- ✅ Monitor Orchestrator Tests  
- ✅ Monitor Integration Check

These checks ensure code quality and prevent breaking changes.

## Script Categories

### Monitoring
- `monitor_orchestrator.py` - Main monitoring orchestrator
- `test_monitor_graceful_degradation.py` - Tests for monitor graceful degradation
- `repo_root_utils.py` - Repository root utilities

### Cost Reporting
- `kg_cost_report.py` - Knowledge graph cost analysis

### Migrations
- `apply_phase3_migrations.py` - Phase 3 migration scripts
- `send_phase3_notification_email.py` - Phase 3 notifications

### Security & Verification
- `validate_redis_tls.py` - Redis TLS validation
- `verify_redis_security.py` - Redis security checks
- `verify_secret_inventory.py` - Secret inventory verification

### Configuration
- `check-env-drift.py` - Environment drift detection
- `generate-env-examples.py` - Generate environment examples
- `generate_env_example.py` - Generate environment example
- `configure_sentry_alerts.py` - Sentry alert configuration

### Analytics
- `analyze_worker_optimization.py` - Worker optimization analysis
- `update_reputation_daily.py` - Daily reputation updates

## Troubleshooting

### ImportError or ModuleNotFoundError

If you see import errors:
```
ModuleNotFoundError: No module named 'common'
ModuleNotFoundError: No module named 'scripts.repo_root_utils'
```

**Solution**: Set PYTHONPATH correctly:
```bash
export PYTHONPATH="$(pwd):$(pwd)/scripts"
```

### Script runs in local but fails in CI

1. Check Python version compatibility (CI uses 3.11)
2. Verify PYTHONPATH is set correctly in both environments
3. Check for environment-specific dependencies

### Syntax errors in CI but not locally

This usually indicates Python version mismatch. CI uses Python 3.11. Check if your local Python version is newer and uses syntax not supported in 3.11.

## Adding New Scripts

When adding new scripts to this directory:

1. **Ensure Python 3.11 compatibility** - CI uses Python 3.11
2. **Test with correct PYTHONPATH** - Set `PYTHONPATH=$(pwd):$(pwd)/scripts`
3. **Add dependencies to `requirements.txt`** - If using new packages
4. **Run CI checks locally** - Use `python -m py_compile scripts/your_script.py`
5. **Document in this README** - Add to appropriate category above

## Related Documentation

- [CI Workflow](.github/workflows/python-scripts-ci.yml) - Full CI configuration
- [Environment Schema](../config/env.schema.yaml) - Environment variable schema
- [Settings Documentation](../docs/config/settings.md) - Application settings

## Support

For issues with scripts or CI:
1. Check this README for environment setup
2. Review CI logs for specific errors
3. Verify PYTHONPATH configuration matches CI
4. Contact the development team if issues persist
