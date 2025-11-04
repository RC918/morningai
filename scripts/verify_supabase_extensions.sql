
SELECT 
    name,
    default_version,
    installed_version,
    comment
FROM pg_available_extensions
WHERE name IN (
    'vector',           -- pgvector for embeddings
    'pg_stat_statements', -- Query performance monitoring
    'pg_trgm'           -- Trigram text search
)
ORDER BY name;

SELECT 
    extname as extension_name,
    extversion as version
FROM pg_extension
WHERE extname IN ('vector', 'pg_stat_statements', 'pg_trgm');

SELECT version();

SELECT 
    has_database_privilege(current_database(), 'CREATE') as can_create_extensions;
