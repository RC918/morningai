# Dev_Agent Database Migrations

This directory contains SQL migration scripts for Dev_Agent's knowledge graph and learning features.

## Migrations

### 001_knowledge_graph_schema.sql

**Purpose**: Initialize knowledge graph schema with pgvector support

**Tables Created**:
- `code_entities` - Stores indexed code entities with vector embeddings
- `entity_relationships` - Stores relationships between entities
- `learned_patterns` - Stores learned bug/fix/style patterns
- `bug_fix_history` - Tracks bug fix attempts and outcomes

**Prerequisites**:
- PostgreSQL 12+
- pgvector extension installed

## Running Migrations

### Option 1: Direct SQL Execution

```bash
# For Supabase
psql -h db.YOUR_PROJECT_ID.supabase.co -U postgres -d postgres -f 001_knowledge_graph_schema.sql

# For local PostgreSQL
psql -U postgres -d morningai -f 001_knowledge_graph_schema.sql
```

### Option 2: Python Script

```python
from agents.dev_agent.knowledge import KnowledgeGraphManager

kg = KnowledgeGraphManager()
kg.connect()
kg.initialize_schema()
kg.close()
```

### Option 3: Automated Migration Tool

```bash
python agents/dev_agent/migrations/migrate.py
```

## Installing pgvector

### Supabase (Cloud)

pgvector is pre-installed. Enable it in your database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Local PostgreSQL

#### macOS (Homebrew)
```bash
brew install pgvector
```

#### Ubuntu/Debian
```bash
sudo apt install postgresql-contrib
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### Docker
```dockerfile
FROM postgres:15
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential git postgresql-server-dev-15 && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && make install && \
    cd .. && rm -rf pgvector && \
    apt-get remove -y build-essential git && \
    apt-get autoremove -y
```

## Verification

After running the migration, verify the schema:

```sql
-- Check tables
\dt

-- Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check indexes
\di

-- Sample query
SELECT COUNT(*) FROM code_entities;
```

## Rollback

To rollback the migration:

```sql
DROP TABLE IF EXISTS bug_fix_history CASCADE;
DROP TABLE IF EXISTS learned_patterns CASCADE;
DROP TABLE IF EXISTS entity_relationships CASCADE;
DROP TABLE IF EXISTS code_entities CASCADE;
DROP EXTENSION IF EXISTS vector;
```

## Performance Tuning

### pgvector Index Configuration

The default migration creates an IVFFlat index with 100 lists:

```sql
CREATE INDEX idx_entities_embedding 
ON code_entities USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Tuning Guidelines**:
- For < 1M vectors: `lists = 100` (default)
- For 1M-10M vectors: `lists = 1000`
- For > 10M vectors: `lists = sqrt(rows)`

### Maintenance

```sql
-- Rebuild indexes
REINDEX TABLE code_entities;

-- Update statistics
ANALYZE code_entities;
VACUUM ANALYZE code_entities;
```

## Monitoring

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('code_entities', 'entity_relationships', 'learned_patterns', 'bug_fix_history')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT 
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public';
```

## Troubleshomarks

### Issue: pgvector extension not found

**Solution**: Install pgvector (see "Installing pgvector" above)

### Issue: IVFFlat index build too slow

**Solution**: Reduce `lists` parameter or use HNSW index (PostgreSQL 15+):

```sql
CREATE INDEX idx_entities_embedding 
ON code_entities USING hnsw (embedding vector_cosine_ops);
```

### Issue: Out of memory during indexing

**Solution**: Increase `maintenance_work_mem`:

```sql
SET maintenance_work_mem = '2GB';
CREATE INDEX ...
```

## Environment Variables

Required environment variables for KnowledgeGraphManager:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-password

# Or direct PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=morningai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...
```

## Support

For issues or questions:
- Check [pgvector documentation](https://github.com/pgvector/pgvector)
- Open an issue in the repository
- Contact the development team
