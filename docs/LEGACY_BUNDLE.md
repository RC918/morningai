# Legacy Bundle (99_Original_Bundle)

The original bundle has been archived to reduce repository size and improve CI performance.

## Access

Download from: https://github.com/RC918/morningai/releases/tag/v1.0-legacy-bundle

## Contents

- Original handoff deliverables
- Vendored dependencies
- Historical reference code

## Statistics

- **Files**: 12,575 files
- **Size**: 129MB (compressed to 20MB)
- **CI Impact**: Reduced CI time by 2-3 minutes
- **Status**: Not actively used in development

## Why archived?

The 99_Original_Bundle directory contained legacy code that was:
- Slowing down CI/CD pipelines
- Increasing repository clone time
- Degrading developer experience
- Not actively used in current development

By archiving to GitHub Releases, we maintain access to historical code while improving repository performance.

## Restoration

If you need to restore the bundle for reference:

```bash
# Download the archive
wget https://github.com/RC918/morningai/releases/download/v1.0-legacy-bundle/99_Original_Bundle.tar.gz

# Extract to handoff directory
cd handoff/20250928
tar -xzf 99_Original_Bundle.tar.gz
```

## Related

- Issue: #872
- Roadmap: docs/TECHNICAL_DEBT_ROADMAP.md (Phase 2)
- Release: https://github.com/RC918/morningai/releases/tag/v1.0-legacy-bundle
