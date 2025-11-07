/**
 * Unit tests for enhanced i18n coverage script
 * Tests ICU detection, pluralization detection, ignore lists, and namespace statistics
 */

const { describe, it, expect, beforeEach } = require('@jest/globals');

// Mock functions extracted from test-i18n-enhanced.cjs for testing
function detectICUFormat(value) {
  if (typeof value !== 'string') return false;
  
  const icuPatterns = [
    /\{[^}]+,\s*plural,/,
    /\{[^}]+,\s*select,/,
    /\{[^}]+,\s*selectordinal,/,
    /\{[^}]+,\s*number,/,
    /\{[^}]+,\s*date,/,
    /\{[^}]+,\s*time,/
  ];
  
  return icuPatterns.some(pattern => pattern.test(value));
}

function detectI18nextPluralization(key) {
  const pluralSuffixes = ['_zero', '_one', '_two', '_few', '_many', '_other'];
  return pluralSuffixes.some(suffix => key.endsWith(suffix));
}

function getNamespace(key) {
  const parts = key.split('.');
  return parts.length > 1 ? parts[0] : 'root';
}

function shouldIgnoreKey(key, config) {
  if (config.ignoreKeys.includes(key)) {
    return true;
  }
  
  for (const pattern of config.ignorePatterns) {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    if (regex.test(key)) {
      return true;
    }
  }
  
  return false;
}

function getAllKeys(obj, prefix = '', config = { ignoreKeys: [], ignorePatterns: [], detectICU: true, detectPluralization: true }) {
  const keys = [];
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      keys.push(...getAllKeys(value, fullKey, config));
    } else {
      const metadata = {
        key: fullKey,
        namespace: getNamespace(fullKey),
        ignored: shouldIgnoreKey(fullKey, config),
        hasICU: config.detectICU && detectICUFormat(value),
        hasPluralization: config.detectPluralization && detectI18nextPluralization(fullKey),
        value: value
      };
      keys.push(metadata);
    }
  }
  
  return keys;
}

function groupByNamespace(keys) {
  const namespaces = {};
  
  for (const keyMeta of keys) {
    const ns = keyMeta.namespace;
    if (!namespaces[ns]) {
      namespaces[ns] = [];
    }
    namespaces[ns].push(keyMeta);
  }
  
  return namespaces;
}

function calculateCoverage(primaryKeys, secondaryKeys, config) {
  const relevantPrimaryKeys = primaryKeys.filter(k => !k.ignored);
  const secondaryKeySet = new Set(secondaryKeys.map(k => k.key));
  
  const covered = relevantPrimaryKeys.filter(k => secondaryKeySet.has(k.key)).length;
  const total = relevantPrimaryKeys.length;
  
  return {
    covered,
    total,
    percentage: total > 0 ? (covered / total) * 100 : 0
  };
}

describe('Enhanced i18n Coverage Script', () => {
  describe('ICU Format Detection', () => {
    it('should detect plural ICU format', () => {
      const value = '{count, plural, one {# item} other {# items}}';
      expect(detectICUFormat(value)).toBe(true);
    });

    it('should detect select ICU format', () => {
      const value = '{gender, select, male {He} female {She} other {They}}';
      expect(detectICUFormat(value)).toBe(true);
    });

    it('should detect number ICU format', () => {
      const value = '{price, number, currency}';
      expect(detectICUFormat(value)).toBe(true);
    });

    it('should detect date ICU format', () => {
      const value = '{date, date, short}';
      expect(detectICUFormat(value)).toBe(true);
    });

    it('should detect time ICU format', () => {
      const value = '{time, time, medium}';
      expect(detectICUFormat(value)).toBe(true);
    });

    it('should not detect ICU format in simple strings', () => {
      expect(detectICUFormat('Hello world')).toBe(false);
      expect(detectICUFormat('{{count}} items')).toBe(false);
      expect(detectICUFormat('{count} items')).toBe(false);
    });

    it('should handle non-string values', () => {
      expect(detectICUFormat(null)).toBe(false);
      expect(detectICUFormat(undefined)).toBe(false);
      expect(detectICUFormat(123)).toBe(false);
      expect(detectICUFormat({})).toBe(false);
    });
  });

  describe('i18next Pluralization Detection', () => {
    it('should detect _one suffix', () => {
      expect(detectI18nextPluralization('item_one')).toBe(true);
    });

    it('should detect _other suffix', () => {
      expect(detectI18nextPluralization('item_other')).toBe(true);
    });

    it('should detect _zero suffix', () => {
      expect(detectI18nextPluralization('item_zero')).toBe(true);
    });

    it('should detect _two suffix', () => {
      expect(detectI18nextPluralization('item_two')).toBe(true);
    });

    it('should detect _few suffix', () => {
      expect(detectI18nextPluralization('item_few')).toBe(true);
    });

    it('should detect _many suffix', () => {
      expect(detectI18nextPluralization('item_many')).toBe(true);
    });

    it('should not detect pluralization in regular keys', () => {
      expect(detectI18nextPluralization('item')).toBe(false);
      expect(detectI18nextPluralization('items')).toBe(false);
      expect(detectI18nextPluralization('one_item')).toBe(false);
    });
  });

  describe('Namespace Extraction', () => {
    it('should extract namespace from dotted keys', () => {
      expect(getNamespace('common.hello')).toBe('common');
      expect(getNamespace('auth.login.title')).toBe('auth');
      expect(getNamespace('errors.notFound')).toBe('errors');
    });

    it('should return "root" for keys without namespace', () => {
      expect(getNamespace('hello')).toBe('root');
      expect(getNamespace('title')).toBe('root');
    });
  });

  describe('Ignore List Functionality', () => {
    const config = {
      ignoreKeys: ['common.appName', 'common.version'],
      ignorePatterns: ['debug.*', 'test.*', 'dev.*'],
      detectICU: true,
      detectPluralization: true
    };

    it('should ignore exact key matches', () => {
      expect(shouldIgnoreKey('common.appName', config)).toBe(true);
      expect(shouldIgnoreKey('common.version', config)).toBe(true);
    });

    it('should ignore pattern matches', () => {
      expect(shouldIgnoreKey('debug.log', config)).toBe(true);
      expect(shouldIgnoreKey('debug.trace.error', config)).toBe(true);
      expect(shouldIgnoreKey('test.unit', config)).toBe(true);
      expect(shouldIgnoreKey('dev.feature', config)).toBe(true);
    });

    it('should not ignore non-matching keys', () => {
      expect(shouldIgnoreKey('common.hello', config)).toBe(false);
      expect(shouldIgnoreKey('auth.login', config)).toBe(false);
      expect(shouldIgnoreKey('production.feature', config)).toBe(false);
    });
  });

  describe('Key Extraction with Metadata', () => {
    const config = {
      ignoreKeys: ['common.version'],
      ignorePatterns: ['debug.*'],
      detectICU: true,
      detectPluralization: true
    };

    it('should extract keys with correct metadata', () => {
      const data = {
        common: {
          hello: 'Hello',
          version: '1.0.0',
          items_one: '{count} item',
          items_other: '{count} items'
        },
        debug: {
          log: 'Debug log'
        }
      };

      const keys = getAllKeys(data, '', config);

      expect(keys).toHaveLength(5);
      
      const helloKey = keys.find(k => k.key === 'common.hello');
      expect(helloKey).toBeDefined();
      expect(helloKey.namespace).toBe('common');
      expect(helloKey.ignored).toBe(false);
      expect(helloKey.hasICU).toBe(false);
      expect(helloKey.hasPluralization).toBe(false);

      const versionKey = keys.find(k => k.key === 'common.version');
      expect(versionKey).toBeDefined();
      expect(versionKey.ignored).toBe(true);

      const debugKey = keys.find(k => k.key === 'debug.log');
      expect(debugKey).toBeDefined();
      expect(debugKey.ignored).toBe(true);

      const pluralOneKey = keys.find(k => k.key === 'common.items_one');
      expect(pluralOneKey).toBeDefined();
      expect(pluralOneKey.hasPluralization).toBe(true);
    });

    it('should detect ICU format in values', () => {
      const data = {
        messages: {
          count: '{count, plural, one {# item} other {# items}}'
        }
      };

      const keys = getAllKeys(data, '', config);
      const countKey = keys.find(k => k.key === 'messages.count');
      
      expect(countKey).toBeDefined();
      expect(countKey.hasICU).toBe(true);
    });
  });

  describe('Namespace Grouping', () => {
    it('should group keys by namespace', () => {
      const keys = [
        { key: 'common.hello', namespace: 'common', ignored: false },
        { key: 'common.world', namespace: 'common', ignored: false },
        { key: 'auth.login', namespace: 'auth', ignored: false },
        { key: 'auth.logout', namespace: 'auth', ignored: false },
        { key: 'errors.notFound', namespace: 'errors', ignored: false }
      ];

      const namespaces = groupByNamespace(keys);

      expect(Object.keys(namespaces)).toHaveLength(3);
      expect(namespaces.common).toHaveLength(2);
      expect(namespaces.auth).toHaveLength(2);
      expect(namespaces.errors).toHaveLength(1);
    });
  });

  describe('Coverage Calculation', () => {
    const config = {
      ignoreKeys: ['common.version'],
      ignorePatterns: [],
      detectICU: true,
      detectPluralization: true
    };

    it('should calculate coverage correctly', () => {
      const primaryKeys = [
        { key: 'common.hello', ignored: false },
        { key: 'common.world', ignored: false },
        { key: 'common.version', ignored: true },
        { key: 'auth.login', ignored: false }
      ];

      const secondaryKeys = [
        { key: 'common.hello', ignored: false },
        { key: 'common.world', ignored: false },
        { key: 'common.version', ignored: true }
      ];

      const coverage = calculateCoverage(primaryKeys, secondaryKeys, config);

      expect(coverage.total).toBe(3); // Excludes ignored key
      expect(coverage.covered).toBe(2);
      expect(coverage.percentage).toBeCloseTo(66.67, 1);
    });

    it('should handle 100% coverage', () => {
      const primaryKeys = [
        { key: 'common.hello', ignored: false },
        { key: 'common.world', ignored: false }
      ];

      const secondaryKeys = [
        { key: 'common.hello', ignored: false },
        { key: 'common.world', ignored: false }
      ];

      const coverage = calculateCoverage(primaryKeys, secondaryKeys, config);

      expect(coverage.total).toBe(2);
      expect(coverage.covered).toBe(2);
      expect(coverage.percentage).toBe(100);
    });

    it('should handle 0% coverage', () => {
      const primaryKeys = [
        { key: 'common.hello', ignored: false },
        { key: 'common.world', ignored: false }
      ];

      const secondaryKeys = [];

      const coverage = calculateCoverage(primaryKeys, secondaryKeys, config);

      expect(coverage.total).toBe(2);
      expect(coverage.covered).toBe(0);
      expect(coverage.percentage).toBe(0);
    });

    it('should handle empty primary keys', () => {
      const primaryKeys = [];
      const secondaryKeys = [];

      const coverage = calculateCoverage(primaryKeys, secondaryKeys, config);

      expect(coverage.total).toBe(0);
      expect(coverage.covered).toBe(0);
      expect(coverage.percentage).toBe(0);
    });
  });
});
