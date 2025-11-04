# HNSW Index Tuning Guide for Knowledge Graph

This guide explains how to optimize HNSW (Hierarchical Navigable Small World) indexes for pgvector to achieve optimal search performance.

---

## Understanding HNSW Parameters

HNSW indexes have two critical parameters that affect performance:

### 1. `m` (Maximum Connections)

- **Range**: 4-64 (practical: 8-32)
- **Default**: 16
- **Effect**: 
  - Higher `m` = More connections per node = Better recall, slower build
  - Lower `m` = Fewer connections = Faster build, lower recall

### 2. `ef_construction` (Construction Time Search Depth)

- **Range**: 8-512 (practical: 32-256)
- **Default**: 64
- **Effect**:
  - Higher `ef_construction` = More thorough index building = Better quality
  - Lower `ef_construction` = Faster index building = Lower quality

---

## Performance Trade-offs

```
┌─────────────────────────────────────────────────────────────┐
│                    HNSW Parameter Matrix                     │
├─────────────────────────────────────────────────────────────┤
│              Build Time  │  Query Speed  │  Recall Quality  │
├─────────────────────────────────────────────────────────────┤
│ Low m, Low ef           │    Fast       │     Fast    │  Low   │
│ Med m, Med ef (default) │    Medium     │     Medium  │  Good  │
│ High m, High ef         │    Slow       │     Slow    │  Best  │
└─────────────────────────────────────────────────────────────┘
```

---

## Recommended Configurations

### Configuration 1: Small Codebase (<10K vectors)

**Best For**: Quick prototyping, small projects

```sql
CREATE INDEX code_embeddings_embedding_idx 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**Characteristics**:
- Build Time: ~30 seconds
- Query P95: <10ms
- Recall@10: ~95%
- Storage: ~1.5x vector data size

**Use Case**: Personal projects, POCs, <1000 files

---

### Configuration 2: Medium Codebase (10K-100K vectors)

**Best For**: Production applications, team projects

```sql
CREATE INDEX code_embeddings_embedding_idx 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 24, ef_construction = 96);
```

**Characteristics**:
- Build Time: ~5-10 minutes
- Query P95: <20ms
- Recall@10: ~97%
- Storage: ~2x vector data size

**Use Case**: Monorepos, enterprise codebases, 1K-10K files

---

### Configuration 3: Large Codebase (>100K vectors)

**Best For**: High-scale production, multiple repositories

```sql
CREATE INDEX code_embeddings_embedding_idx 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 32, ef_construction = 128);
```

**Characteristics**:
- Build Time: ~20-40 minutes
- Query P95: <40ms
- Recall@10: ~98%
- Storage: ~2.5x vector data size

**Use Case**: Organization-wide code search, >10K files

---

### Configuration 4: Maximum Quality (Research/Evaluation)

**Best For**: Benchmarking, high-precision requirements

```sql
CREATE INDEX code_embeddings_embedding_idx 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 48, ef_construction = 256);
```

**Characteristics**:
- Build Time: ~1-2 hours (100K vectors)
- Query P95: <50ms
- Recall@10: ~99%+
- Storage: ~3x vector data size

**Use Case**: Research, evaluation, when accuracy > speed

---

## When to Re-index

### Trigger 1: Dataset Size Growth

Re-index if your dataset has grown significantly:

```sql
-- Check current vector count
SELECT count(*) as vector_count FROM code_embeddings;

-- If 10x+ growth from original size, consider re-indexing
```

**Example**:
- Original: 1,000 vectors (m=16, ef=64)
- Current: 50,000 vectors
- **Action**: Re-index with m=24, ef=96

### Trigger 2: Query Performance Degradation

Monitor query latency:

```sql
-- Run sample query with timing
\timing on
SELECT file_path, embedding <=> '[0.1, 0.1, ...]'::vector AS distance
FROM code_embeddings
ORDER BY distance
LIMIT 10;
```

**Re-index if**:
- P50 increased >50%
- P95 increased >100%
- P95 > 50ms consistently

### Trigger 3: Recall Quality Issues

If users report missing relevant results:

```sql
-- Test recall by searching for known similar code
-- If top-10 results don't include expected matches, re-index
```

---

## Re-indexing Procedure

### Step 1: Analyze Current Performance

```sql
-- Get index statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname = 'code_embeddings_embedding_idx';

-- Check index size
SELECT pg_size_pretty(pg_relation_size('code_embeddings_embedding_idx'));
```

### Step 2: Create New Index (Concurrent)

**Recommended Approach**: Create new index, then drop old one

```sql
-- Create new index with different name
CREATE INDEX CONCURRENTLY code_embeddings_embedding_idx_v2 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 32, ef_construction = 128);

-- Monitor progress
SELECT 
    phase,
    round(100.0 * blocks_done / nullif(blocks_total, 0), 2) AS "% complete"
FROM pg_stat_progress_create_index
WHERE relid = 'code_embeddings'::regclass;
```

### Step 3: Test New Index

```sql
-- Force use of new index
SET enable_seqscan = off;

-- Run test queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT file_path, embedding <=> '[...]'::vector AS distance
FROM code_embeddings
ORDER BY distance
LIMIT 10;

-- Check query plan uses new index
```

### Step 4: Switch Indexes

```sql
-- Drop old index
DROP INDEX IF EXISTS code_embeddings_embedding_idx;

-- Rename new index
ALTER INDEX code_embeddings_embedding_idx_v2 
    RENAME TO code_embeddings_embedding_idx;
```

---

## Query-Time Tuning

### Parameter: `ef_search`

Controls search quality at query time (different from `ef_construction`):

```sql
-- Increase search quality (slower)
SET hnsw.ef_search = 100;

-- Run query
SELECT ... FROM code_embeddings ...

-- Reset to default
SET hnsw.ef_search = 40;
```

**Guidelines**:
- Default: 40
- For better recall: 100-200
- For speed: 20-40

**Trade-off**:
```
ef_search    Query Time    Recall@10
   20          ~5ms          ~93%
   40          ~10ms         ~95%
  100          ~25ms         ~98%
  200          ~50ms         ~99%
```

---

## Performance Monitoring

### Query 1: Index Usage Statistics

```sql
SELECT 
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'code_embeddings';
```

### Query 2: Query Performance Analysis

```sql
-- Enable timing
\timing on

-- Run sample queries
SELECT file_path, embedding <=> '[...]'::vector AS distance
FROM code_embeddings
WHERE language = 'python'
ORDER BY distance
LIMIT 10;
```

### Query 3: Index Bloat Check

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_size_pretty(pg_relation_size(relid)) as table_size,
    round(100.0 * pg_relation_size(indexrelid) / pg_relation_size(relid), 2) as index_ratio
FROM pg_stat_user_indexes
WHERE tablename = 'code_embeddings';
```

**Healthy ratio**: 150-250% (index size / table size for HNSW)

---

## Benchmarking Script

Save as `scripts/benchmark_hnsw.sql`:

```sql
-- Benchmark HNSW index performance

\timing on

-- Test 1: Simple similarity search
SELECT 'Test 1: Simple search' as test;
SELECT file_path, embedding <=> '[0.1]'::vector AS distance
FROM code_embeddings
ORDER BY distance
LIMIT 10;

-- Test 2: Search with filter
SELECT 'Test 2: Filtered search' as test;
SELECT file_path, embedding <=> '[0.1]'::vector AS distance
FROM code_embeddings
WHERE language = 'python'
ORDER BY distance
LIMIT 10;

-- Test 3: Larger result set
SELECT 'Test 3: Top 50 results' as test;
SELECT file_path, embedding <=> '[0.1]'::vector AS distance
FROM code_embeddings
ORDER BY distance
LIMIT 50;

\timing off
```

Run with:
```bash
psql $DB_URL -f scripts/benchmark_hnsw.sql
```

---

## Decision Tree

```
How many vectors do you have?
│
├─ <10,000
│   └─ Use: m=16, ef_construction=64
│       ✓ Fast build (~30s)
│       ✓ Good enough quality
│
├─ 10,000-100,000
│   ├─ Need speed?
│   │   └─ Use: m=16, ef_construction=64
│   │       ✓ Faster queries
│   │       ⚠ Slight quality loss
│   │
│   └─ Need quality?
│       └─ Use: m=24, ef_construction=96
│           ✓ Better recall
│           ⚠ Slower build
│
└─ >100,000
    ├─ Production system?
    │   └─ Use: m=32, ef_construction=128
    │       ✓ Balanced
    │
    └─ Research/evaluation?
        └─ Use: m=48, ef_construction=256
            ✓ Maximum quality
            ⚠ Slow build (1-2hrs)
```

---

## Common Issues

### Issue: Index Build Too Slow

**Symptom**: Index creation taking hours

**Solutions**:
1. **Reduce parameters**:
   ```sql
   -- Try lower values first
   WITH (m = 16, ef_construction = 64)
   ```

2. **Use CONCURRENTLY** (allows queries during build):
   ```sql
   CREATE INDEX CONCURRENTLY ...
   ```

3. **Increase work_mem**:
   ```sql
   SET work_mem = '1GB';
   CREATE INDEX ...
   SET work_mem = '64MB';  -- Reset
   ```

### Issue: Queries Still Slow

**Symptom**: P95 > 100ms after re-indexing

**Solutions**:
1. **Check query plan**:
   ```sql
   EXPLAIN (ANALYZE) SELECT ...
   -- Should use "Index Scan using hnsw"
   ```

2. **Increase ef_search**:
   ```sql
   SET hnsw.ef_search = 100;
   ```

3. **Add covering index** for filtered queries:
   ```sql
   CREATE INDEX code_embeddings_lang_idx 
       ON code_embeddings(language);
   ```

### Issue: Low Recall

**Symptom**: Missing obvious similar results

**Solutions**:
1. **Increase index parameters**:
   ```sql
   -- Rebuild with higher values
   WITH (m = 32, ef_construction = 128)
   ```

2. **Increase query-time ef_search**:
   ```sql
   SET hnsw.ef_search = 200;
   ```

3. **Verify vector quality**:
   ```sql
   -- Check for null/zero vectors
   SELECT count(*) FROM code_embeddings 
   WHERE embedding = '[0]'::vector;
   ```

---

## Best Practices

### 1. Start Conservative

Begin with default parameters (m=16, ef=64) and only increase if needed.

### 2. Monitor Before Re-indexing

Collect at least 1 week of query performance data before deciding to re-index.

### 3. Test on Staging First

Always test new index parameters on staging/development before production.

### 4. Document Changes

Keep a log of index changes and their impact:
```
2025-01-15: Increased to m=24, ef=96
           - Build time: 8min
           - P95 improved: 35ms → 18ms
           - Recall improved: 95% → 97%
```

### 5. Schedule Downtime

For large re-indexes (>100K vectors), schedule during low-traffic hours.

---

## Further Reading

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)
- [PostgreSQL Index Tuning](https://www.postgresql.org/docs/current/indexes-types.html)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-17  
**For**: Knowledge Graph System (Phase 1 Week 5)
