# Inline Styles Count Discrepancy Analysis

**Date**: 2025-11-02
**Issue**: Audit script reports 36, but independent verification shows 50

## Investigation

**Audit Script Count**: 36
- Command: `grep -r "style={{" [dirs] --include="*.tsx" --exclude="*.stories.tsx" --exclude="TokenExample.tsx" | grep -v Motion keys`

**Independent Verification Count**: 50
- Command: `grep -r "style={{" [dirs] --include="*.tsx" --exclude="*.stories.tsx" | grep -v Motion keys`

**Difference**: 14 instances

## Root Cause

The audit script excludes `TokenExample.tsx` which contains 14 inline style instances.

**TokenExample.tsx** is a documentation/example file in shared-ui that demonstrates how to use design tokens. It legitimately uses inline styles to show examples.

## Conclusion

Both counts are correct for their respective methodologies:
- **36**: Excludes TokenExample.tsx (documentation file with legitimate inline style examples)
- **50**: Includes TokenExample.tsx

The CTO's independent verification of **50** likely did not exclude TokenExample.tsx.

## Recommendation

For alignment with CTO's methodology, the audit script should **remove the TokenExample.tsx exclusion** to report 50 instances, matching the independent verification exactly.

This would make the count consistent and transparent.
