
ALTER TABLE code_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding_cache_stats ENABLE ROW LEVEL SECURITY;


CREATE POLICY "Service role has full access to code_embeddings"
ON code_embeddings
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can read code_embeddings"
ON code_embeddings
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can insert code_embeddings"
ON code_embeddings
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authenticated users can update code_embeddings"
ON code_embeddings
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can delete code_embeddings"
ON code_embeddings
FOR DELETE
TO authenticated
USING (true);


CREATE POLICY "Service role has full access to code_patterns"
ON code_patterns
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can read code_patterns"
ON code_patterns
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can insert code_patterns"
ON code_patterns
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authenticated users can update code_patterns"
ON code_patterns
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can delete code_patterns"
ON code_patterns
FOR DELETE
TO authenticated
USING (true);


CREATE POLICY "Service role has full access to code_relationships"
ON code_relationships
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can read code_relationships"
ON code_relationships
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can insert code_relationships"
ON code_relationships
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authenticated users can update code_relationships"
ON code_relationships
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can delete code_relationships"
ON code_relationships
FOR DELETE
TO authenticated
USING (true);


CREATE POLICY "Service role has full access to embedding_cache_stats"
ON embedding_cache_stats
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can read embedding_cache_stats"
ON embedding_cache_stats
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can insert embedding_cache_stats"
ON embedding_cache_stats
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authenticated users can update embedding_cache_stats"
ON embedding_cache_stats
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);


COMMENT ON POLICY "Service role has full access to code_embeddings" 
ON code_embeddings IS 'Service role (application backend) has unrestricted access';

COMMENT ON POLICY "Service role has full access to code_patterns" 
ON code_patterns IS 'Service role (application backend) has unrestricted access';

COMMENT ON POLICY "Service role has full access to code_relationships" 
ON code_relationships IS 'Service role (application backend) has unrestricted access';

COMMENT ON POLICY "Service role has full access to embedding_cache_stats" 
ON embedding_cache_stats IS 'Service role (application backend) has unrestricted access';
