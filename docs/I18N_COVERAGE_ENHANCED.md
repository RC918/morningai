# Enhanced i18n Coverage Testing

## Overview

The enhanced i18n coverage testing system provides advanced features for monitoring translation coverage across applications, including ICU/pluralization support detection, ignore lists, per-namespace statistics, and flexible threshold validation.

## Features

### 1. ICU MessageFormat Detection

The system automatically detects ICU MessageFormat syntax in translation values:

```json
{
  "items": "{count, plural, one {# item} other {# items}}",
  "gender": "{gender, select, male {He} female {She} other {They}}",
  "price": "{price, number, currency}",
  "date": "{date, date, short}",
  "time": "{time, time, medium}"
}
```

**Supported ICU Patterns:**
- `plural` - Pluralization rules
- `select` - Selection based on value
- `selectordinal` - Ordinal selection (1st, 2nd, 3rd)
- `number` - Number formatting
- `date` - Date formatting
- `time` - Time formatting

### 2. i18next Pluralization Detection

The system detects i18next pluralization suffixes:

```json
{
  "item_zero": "No items",
  "item_one": "One item",
  "item_two": "Two items",
  "item_few": "A few items",
  "item_many": "Many items",
  "item_other": "{{count}} items"
}
```

**Supported Suffixes:**
- `_zero` - Zero items
- `_one` - Singular
- `_two` - Two items (for languages with dual form)
- `_few` - Few items
- `_many` - Many items
- `_other` - Default plural form

### 3. Ignore Lists

Configure keys or patterns to exclude from coverage calculation:

```json
{
  "ignoreKeys": [
    "common.appName",
    "common.version",
    "common.buildNumber"
  ],
  "ignorePatterns": [
    "debug.*",
    "test.*",
    "dev.*",
    "internal.*"
  ]
}
```

**Use Cases:**
- Brand names that shouldn't be translated
- Version numbers and technical identifiers
- Debug/development-only strings
- Internal tool strings not visible to users

### 4. Per-Namespace Statistics

Track coverage separately for each namespace (feature/module):

```
Namespace breakdown:
  ✅ common: 100% (19/19, threshold: 100%)
  ✅ auth: 100% (46/46, threshold: 100%)
  ✅ errors: 100% (27/27, threshold: 98%)
  ✅ dashboard: 100% (28/28, threshold: 95%)
  ⚠️  experimental: 85% (17/20, threshold: 95%)
```

**Benefits:**
- Identify which features need translation work
- Set different thresholds per namespace
- Track progress on specific modules
- Prioritize critical namespaces (auth, errors) with higher thresholds

### 5. Flexible Threshold Validation

Configure different coverage thresholds globally and per-namespace:

```json
{
  "thresholds": {
    "global": 95,
    "perNamespace": {
      "common": 100,
      "auth": 100,
      "errors": 98,
      "dashboard": 95,
      "experimental": 80
    }
  }
}
```

## Configuration

### Configuration File Location

Each application has its own configuration file:
- `frontend-dashboard/i18n-coverage-config.json`
- `owner-console/i18n-coverage-config.json`

### Configuration Schema

```json
{
  "primaryLocale": "en-US",
  "secondaryLocales": ["zh-TW", "ja-JP", "ko-KR"],
  "thresholds": {
    "global": 95,
    "perNamespace": {
      "common": 100,
      "errors": 98,
      "auth": 100
    }
  },
  "ignorePatterns": [
    "debug.*",
    "test.*",
    "dev.*"
  ],
  "ignoreKeys": [
    "common.appName",
    "common.version"
  ],
  "detectPluralization": true,
  "detectICU": true
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `primaryLocale` | string | `"en-US"` | Source locale (source of truth) |
| `secondaryLocales` | string[] | `["zh-TW"]` | Target locales to check coverage |
| `thresholds.global` | number | `95` | Global coverage threshold (%) |
| `thresholds.perNamespace` | object | `{}` | Per-namespace thresholds |
| `ignorePatterns` | string[] | `[]` | Glob patterns for keys to ignore |
| `ignoreKeys` | string[] | `[]` | Exact keys to ignore |
| `detectPluralization` | boolean | `true` | Detect i18next pluralization |
| `detectICU` | boolean | `true` | Detect ICU MessageFormat |

## Usage

### Running Enhanced Coverage Tests

```bash
# Frontend Dashboard
cd handoff/20250928/40_App/frontend-dashboard
node scripts/test-i18n-enhanced.cjs

# Owner Console
cd handoff/20250928/40_App/owner-console
node scripts/test-i18n-enhanced.cjs
```

### Output Example

```
🌍 Starting Enhanced i18n Coverage Tests...

Configuration:
  Primary locale: en-US
  Secondary locales: zh-TW
  Global threshold: 95%
  Ignore patterns: 3
  Ignore keys: 2
  Detect ICU: true
  Detect pluralization: true

Loading primary locale: en-US
  Total keys: 828
  Relevant keys: 826
  Ignored keys: 2
  Namespaces: 33
  ICU format keys: 5
  Pluralization keys: 12

Checking locale: zh-TW
  Total keys: 828
  Coverage: 100% (threshold: 95%)
  Missing keys: 0
  Extra keys: 0
  Status: ✅ PASS

  Namespace breakdown:
    ✅ common: 100% (19/19, threshold: 100%)
    ✅ auth: 100% (46/46, threshold: 100%)
    ✅ errors: 100% (27/27, threshold: 98%)
    ...

📊 Results saved to: i18n-test-results/i18n-test-report-enhanced.json
✅ All i18n tests PASSED
```

### Output Files

The script generates a detailed JSON report:

```json
{
  "timestamp": "2025-11-07T19:00:00.000Z",
  "passed": true,
  "results": {
    "primary": {
      "locale": "en-US",
      "totalKeys": 828,
      "relevantKeys": 826,
      "ignoredKeys": 2,
      "namespaces": 33,
      "icuKeys": 5,
      "pluralKeys": 12
    },
    "secondary": [
      {
        "locale": "zh-TW",
        "totalKeys": 828,
        "relevantKeys": 826,
        "coverage": 100,
        "covered": 826,
        "missing": 0,
        "extra": 0,
        "passed": true,
        "namespaces": {
          "common": {
            "totalKeys": 19,
            "relevantKeys": 19,
            "ignoredKeys": 0,
            "coverage": 100,
            "covered": 19,
            "missing": 0,
            "extra": 0,
            "threshold": 100,
            "passed": true,
            "icuKeys": 0,
            "pluralKeys": 0
          }
        }
      }
    ],
    "config": {
      "thresholds": {
        "global": 95,
        "perNamespace": {
          "common": 100,
          "errors": 98,
          "auth": 100
        }
      }
    }
  }
}
```

## Integration with CI/CD

### GitHub Actions Workflow

The enhanced i18n coverage tests are integrated into the UX Ops Pipeline:

```yaml
- name: Run enhanced i18n coverage tests
  working-directory: handoff/20250928/40_App/${{ matrix.app }}
  run: node scripts/test-i18n-enhanced.cjs
  continue-on-error: true

- name: Upload enhanced i18n test results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: i18n-results-enhanced-${{ matrix.app }}
    path: handoff/20250928/40_App/${{ matrix.app }}/i18n-test-results/
```

## Best Practices

### 1. Namespace Organization

Organize translation keys by feature/module:

```
common.*        - Shared strings (buttons, labels)
auth.*          - Authentication flows
errors.*        - Error messages
dashboard.*     - Dashboard-specific strings
settings.*      - Settings page strings
```

### 2. Threshold Configuration

Set appropriate thresholds based on criticality:

- **100%** - Critical namespaces (auth, errors, common)
- **98%** - Important namespaces (checkout, payment)
- **95%** - Standard namespaces (dashboard, reports)
- **80-90%** - Experimental/beta features

### 3. Ignore List Management

Use ignore lists judiciously:

**Good candidates for ignoring:**
- Brand names: `"common.appName": "MorningAI"`
- Technical identifiers: `"common.version": "1.0.0"`
- Debug strings: `"debug.trace": "Trace ID: {{id}}"`

**Bad candidates for ignoring:**
- User-visible strings
- Error messages
- Navigation labels

### 4. ICU vs i18next Pluralization

**Use ICU MessageFormat when:**
- You need complex pluralization rules
- You need select/choice formatting
- You need number/date/time formatting

**Use i18next pluralization when:**
- You have simple plural forms
- You want simpler syntax
- You're already using i18next

## Migration Guide

### From Basic to Enhanced Coverage

1. **Create configuration file:**
   ```bash
   cp i18n-coverage-config.json.example i18n-coverage-config.json
   ```

2. **Review and adjust thresholds:**
   - Start with global threshold at current coverage
   - Gradually increase thresholds
   - Set higher thresholds for critical namespaces

3. **Add ignore lists:**
   - Identify strings that shouldn't be translated
   - Add to `ignoreKeys` or `ignorePatterns`

4. **Update CI/CD:**
   - Replace `test-i18n.cjs` with `test-i18n-enhanced.cjs`
   - Update artifact paths if needed

5. **Run tests:**
   ```bash
   node scripts/test-i18n-enhanced.cjs
   ```

## Troubleshooting

### Coverage Below Threshold

**Problem:** Namespace coverage is below threshold

**Solutions:**
1. Check missing keys in the report
2. Add translations to secondary locale files
3. Adjust threshold if appropriate
4. Add keys to ignore list if they shouldn't be translated

### False Positives in ICU Detection

**Problem:** Non-ICU strings detected as ICU format

**Solutions:**
1. Review the detection patterns
2. Escape braces in strings: `"text": "Use \\{braces\\} for formatting"`
3. Disable ICU detection if not using ICU: `"detectICU": false`

### Ignored Keys Not Working

**Problem:** Keys still counted despite being in ignore list

**Solutions:**
1. Check exact key name matches
2. Verify pattern syntax (use `*` for wildcards)
3. Check configuration file is in correct location
4. Verify JSON syntax is valid

## Unit Tests

The enhanced i18n coverage system includes comprehensive unit tests:

```bash
# Run tests for frontend-dashboard
cd handoff/20250928/40_App/frontend-dashboard
pnpm test scripts/__tests__/test-i18n-enhanced.test.cjs

# Run tests for owner-console
cd handoff/20250928/40_App/owner-console
pnpm test scripts/__tests__/test-i18n-enhanced.test.cjs
```

**Test Coverage:**
- ICU format detection (plural, select, number, date, time)
- i18next pluralization detection (_one, _other, etc.)
- Namespace extraction
- Ignore list functionality (exact matches and patterns)
- Key extraction with metadata
- Namespace grouping
- Coverage calculation

## Related Documentation

- [UX Pipeline Documentation](./UX_PIPELINE.md)
- [i18n Guidelines](../CONTRIBUTING.md#i18n-guidelines)
- [i18next Documentation](https://www.i18next.com/)
- [ICU MessageFormat](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
