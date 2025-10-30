# Legacy Bundle (99_Original_Bundle)

The original bundle has been archived to reduce repository size and improve CI performance.

## Access

Download from: https://github.com/RC918/morningai/releases/tag/v1.0-legacy

## Contents

- Original handoff deliverables (12,575 files)
- Vendored dependencies
- Historical reference code
- Legacy implementations

## Why archived?

- **Size**: 129MB (12,575 files)
- **CI Impact**: Slowed CI by 2-3 minutes
- **Usage**: Not actively used in development
- **Maintenance**: Reduced repository bloat

## How to restore

If you need to access the original bundle:

```bash
# Download the archive
wget https://github.com/RC918/morningai/releases/download/v1.0-legacy/99_Original_Bundle.tar.gz

# Extract to handoff directory
cd handoff/20250928
tar -xzf 99_Original_Bundle.tar.gz
```

## Archive Details

- **Created**: 2025-10-30
- **Release**: v1.0-legacy
- **Compressed Size**: 20MB (tar.gz)
- **Original Size**: 129MB (uncompressed)
- **File Count**: 12,575 files

## Related

- Issue #872: Archive 99_Original_Bundle to GitHub releases
- Technical Debt Roadmap: Phase 2 cleanup
