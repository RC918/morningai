"""
FAQ Search Tool - Semantic search for FAQ questions
"""

import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from .embedding_tool import EmbeddingTool


class FAQSearchTool:
    """Tool for searching FAQs using semantic similarity"""
    
    def __init__(
        self,
        supabase_url: str = None,
        supabase_key: str = None,
        embedding_tool: EmbeddingTool = None
    ):
        """
        Initialize FAQ search tool
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            embedding_tool: EmbeddingTool instance (creates new if None)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.embedding_tool = embedding_tool or EmbeddingTool()
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for FAQs using semantic similarity
        
        Args:
            query: User question
            limit: Maximum number of results
            threshold: Minimum similarity score (0-1)
            category: Filter by category (optional)
            tags: Filter by tags (optional)
        
        Returns:
            {
                'success': bool,
                'results': List[Dict],  # FAQ matches
                'query': str,
                'count': int,
                'error': str
            }
        """
        try:
            emb_result = await self.embedding_tool.generate_embedding(query)
            
            if not emb_result['success']:
                return {
                    'success': False,
                    'error': f"Failed to generate embedding: {emb_result.get('error')}"
                }
            
            query_embedding = emb_result['embedding']
            
            rpc_params = {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': limit
            }
            
            if category:
                rpc_params['filter_category'] = category
            
            response = self.client.rpc('match_faqs', rpc_params).execute()
            
            results = response.data if response.data else []
            
            if tags and results:
                results = [
                    r for r in results 
                    if r.get('tags') and any(tag in r['tags'] for tag in tags)
                ]
            
            await self._log_search(
                query=query,
                query_embedding=query_embedding,
                results=results
            )
            
            return {
                'success': True,
                'results': results,
                'query': query,
                'count': len(results),
                'threshold': threshold
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search FAQs by keywords (text search)
        
        Args:
            keywords: List of keywords to search
            limit: Maximum number of results
            category: Filter by category (optional)
        
        Returns:
            Similar to search()
        """
        try:
            search_query = ' & '.join(keywords)
            
            query = self.client.table('faqs') \
                .select('*') \
                .text_search('question', search_query, config='english') \
                .limit(limit)
            
            if category:
                query = query.eq('category', category)
            
            response = query.execute()
            
            results = response.data if response.data else []
            
            return {
                'success': True,
                'results': results,
                'keywords': keywords,
                'count': len(results),
                'search_type': 'keyword'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'keywords': keywords
            }
    
    async def get_faq_by_id(self, faq_id: str) -> Dict[str, Any]:
        """
        Get a specific FAQ by ID
        
        Args:
            faq_id: UUID of the FAQ
        
        Returns:
            {
                'success': bool,
                'faq': Dict,
                'error': str
            }
        """
        try:
            response = self.client.table('faqs') \
                .select('*') \
                .eq('id', faq_id) \
                .single() \
                .execute()
            
            self.client.table('faqs') \
                .update({'view_count': response.data['view_count'] + 1}) \
                .eq('id', faq_id) \
                .execute()
            
            return {
                'success': True,
                'faq': response.data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'faq_id': faq_id
            }
    
    async def get_popular_faqs(
        self,
        limit: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get most viewed FAQs
        
        Args:
            limit: Maximum number of results
            category: Filter by category (optional)
        
        Returns:
            Similar to search()
        """
        try:
            query = self.client.table('faqs') \
                .select('*') \
                .order('view_count', desc=True) \
                .limit(limit)
            
            if category:
                query = query.eq('category', category)
            
            response = query.execute()
            
            return {
                'success': True,
                'results': response.data,
                'count': len(response.data),
                'sort_by': 'view_count'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_helpful_faqs(
        self,
        limit: int = 10,
        min_votes: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get most helpful FAQs based on user feedback
        
        Args:
            limit: Maximum number of results
            min_votes: Minimum number of total votes
            category: Filter by category (optional)
        
        Returns:
            Similar to search()
        """
        try:
            query = self.client.table('faqs') \
                .select('*') \
                .gte('helpful_count', min_votes) \
                .order('helpful_count', desc=True) \
                .limit(limit)
            
            if category:
                query = query.eq('category', category)
            
            response = query.execute()
            
            return {
                'success': True,
                'results': response.data,
                'count': len(response.data),
                'sort_by': 'helpful_count'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def record_feedback(
        self,
        faq_id: str,
        feedback: str,  # 'helpful' or 'not_helpful'
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback for a FAQ
        
        Args:
            faq_id: UUID of the FAQ
            feedback: 'helpful' or 'not_helpful'
            user_id: User ID (optional)
        
        Returns:
            {
                'success': bool,
                'message': str,
                'error': str
            }
        """
        try:
            if feedback not in ['helpful', 'not_helpful']:
                return {
                    'success': False,
                    'error': 'Invalid feedback value. Use "helpful" or "not_helpful"'
                }
            
            faq_response = self.client.table('faqs') \
                .select('helpful_count, not_helpful_count') \
                .eq('id', faq_id) \
                .single() \
                .execute()
            
            if feedback == 'helpful':
                new_count = faq_response.data['helpful_count'] + 1
                self.client.table('faqs') \
                    .update({'helpful_count': new_count}) \
                    .eq('id', faq_id) \
                    .execute()
            else:
                new_count = faq_response.data['not_helpful_count'] + 1
                self.client.table('faqs') \
                    .update({'not_helpful_count': new_count}) \
                    .eq('id', faq_id) \
                    .execute()
            
            return {
                'success': True,
                'message': f'Feedback recorded: {feedback}',
                'faq_id': faq_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'faq_id': faq_id
            }
    
    async def _log_search(
        self,
        query: str,
        query_embedding: List[float],
        results: List[Dict]
    ) -> None:
        """
        Log search query to history
        
        Args:
            query: User query
            query_embedding: Query embedding vector
            results: Search results
        """
        try:
            log_data = {
                'query': query,
                'query_embedding': query_embedding,
                'result_count': len(results)
            }
            
            if results:
                log_data['matched_faq_id'] = results[0].get('id')
                log_data['similarity_score'] = results[0].get('similarity', 0)
            
            self.client.table('faq_search_history').insert(log_data).execute()
            
        except Exception:
            pass


def create_faq_search_tool(
    supabase_url: str = None,
    supabase_key: str = None,
    embedding_tool: EmbeddingTool = None
) -> FAQSearchTool:
    """
    Factory function to create a FAQSearchTool instance
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        embedding_tool: EmbeddingTool instance
    
    Returns:
        FAQSearchTool instance
    """
    return FAQSearchTool(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        embedding_tool=embedding_tool
    )
