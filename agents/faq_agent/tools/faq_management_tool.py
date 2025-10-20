"""
FAQ Management Tool - Create, update, and delete FAQs
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client
from .embedding_tool import EmbeddingTool


class FAQManagementTool:
    """Tool for managing FAQ lifecycle"""
    
    def __init__(
        self,
        supabase_url: str = None,
        supabase_key: str = None,
        embedding_tool: EmbeddingTool = None
    ):
        """
        Initialize FAQ management tool
        
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
    
    async def create_faq(
        self,
        question: str,
        answer: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new FAQ
        
        Args:
            question: FAQ question
            answer: FAQ answer
            category: Category name (optional)
            tags: List of tags (optional)
            metadata: Additional metadata (optional)
            created_by: Creator user ID (optional)
        
        Returns:
            {
                'success': bool,
                'faq': Dict,  # Created FAQ with ID
                'error': str
            }
        """
        try:
            emb_result = await self.embedding_tool.generate_embedding(question)
            
            if not emb_result['success']:
                return {
                    'success': False,
                    'error': f"Failed to generate embedding: {emb_result.get('error')}"
                }
            
            faq_data = {
                'question': question,
                'answer': answer,
                'embedding': emb_result['embedding'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if category:
                faq_data['category'] = category
            if tags:
                faq_data['tags'] = tags
            if metadata:
                faq_data['metadata'] = metadata
            if created_by:
                faq_data['created_by'] = created_by
            
            response = self.client.table('faqs').insert(faq_data).execute()
            
            return {
                'success': True,
                'faq': response.data[0] if response.data else None,
                'message': 'FAQ created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_faq(
        self,
        faq_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing FAQ
        
        Args:
            faq_id: UUID of the FAQ
            question: New question (optional)
            answer: New answer (optional)
            category: New category (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)
        
        Returns:
            {
                'success': bool,
                'faq': Dict,  # Updated FAQ
                'error': str
            }
        """
        try:
            update_data = {
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if question:
                emb_result = await self.embedding_tool.generate_embedding(question)
                
                if not emb_result['success']:
                    return {
                        'success': False,
                        'error': f"Failed to generate embedding: {emb_result.get('error')}"
                    }
                
                update_data['question'] = question
                update_data['embedding'] = emb_result['embedding']
            
            if answer is not None:
                update_data['answer'] = answer
            if category is not None:
                update_data['category'] = category
            if tags is not None:
                update_data['tags'] = tags
            if metadata is not None:
                update_data['metadata'] = metadata
            
            response = self.client.table('faqs') \
                .update(update_data) \
                .eq('id', faq_id) \
                .execute()
            
            if not response.data:
                return {
                    'success': False,
                    'error': f'FAQ with ID {faq_id} not found'
                }
            
            return {
                'success': True,
                'faq': response.data[0],
                'message': 'FAQ updated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'faq_id': faq_id
            }
    
    async def delete_faq(self, faq_id: str) -> Dict[str, Any]:
        """
        Delete a FAQ
        
        Args:
            faq_id: UUID of the FAQ
        
        Returns:
            {
                'success': bool,
                'message': str,
                'error': str
            }
        """
        try:
            response = self.client.table('faqs') \
                .delete() \
                .eq('id', faq_id) \
                .execute()
            
            if not response.data:
                return {
                    'success': False,
                    'error': f'FAQ with ID {faq_id} not found'
                }
            
            return {
                'success': True,
                'message': 'FAQ deleted successfully',
                'deleted_id': faq_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'faq_id': faq_id
            }
    
    async def bulk_create_faqs(
        self,
        faqs: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Create multiple FAQs in bulk
        
        Args:
            faqs: List of FAQ dicts with 'question', 'answer', etc.
            batch_size: Number of FAQs to process per batch
        
        Returns:
            {
                'success': bool,
                'created_count': int,
                'failed_count': int,
                'failed_indices': List[int],
                'error': str
            }
        """
        try:
            questions = [faq['question'] for faq in faqs]
            
            emb_result = await self.embedding_tool.generate_embeddings_batch(
                questions,
                batch_size=batch_size
            )
            
            if not emb_result['success']:
                return {
                    'success': False,
                    'error': f"Failed to generate embeddings: {emb_result.get('error')}"
                }
            
            faq_data_list = []
            failed_indices = []
            
            for i, faq in enumerate(faqs):
                if emb_result['embeddings'][i] is None:
                    failed_indices.append(i)
                    continue
                
                faq_data = {
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'embedding': emb_result['embeddings'][i],
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if 'category' in faq:
                    faq_data['category'] = faq['category']
                if 'tags' in faq:
                    faq_data['tags'] = faq['tags']
                if 'metadata' in faq:
                    faq_data['metadata'] = faq['metadata']
                if 'created_by' in faq:
                    faq_data['created_by'] = faq['created_by']
                
                faq_data_list.append(faq_data)
            
            created_count = 0
            for i in range(0, len(faq_data_list), batch_size):
                batch = faq_data_list[i:i + batch_size]
                
                try:
                    response = self.client.table('faqs').insert(batch).execute()
                    created_count += len(response.data) if response.data else 0
                except Exception as e:
                    for j in range(len(batch)):
                        failed_indices.append(i + j)
            
            return {
                'success': len(failed_indices) == 0,
                'created_count': created_count,
                'failed_count': len(failed_indices),
                'total': len(faqs),
                'failed_indices': failed_indices,
                'message': f'Created {created_count}/{len(faqs)} FAQs'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_categories(self) -> Dict[str, Any]:
        """
        Get all FAQ categories
        
        Returns:
            {
                'success': bool,
                'categories': List[Dict],
                'error': str
            }
        """
        try:
            response = self.client.table('faq_categories') \
                .select('*') \
                .execute()
            
            return {
                'success': True,
                'categories': response.data,
                'count': len(response.data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent_category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new FAQ category
        
        Args:
            name: Category name
            description: Category description (optional)
            parent_category_id: Parent category UUID (optional)
        
        Returns:
            {
                'success': bool,
                'category': Dict,
                'error': str
            }
        """
        try:
            category_data = {
                'name': name,
                'created_at': datetime.utcnow().isoformat()
            }
            
            if description:
                category_data['description'] = description
            if parent_category_id:
                category_data['parent_category_id'] = parent_category_id
            
            response = self.client.table('faq_categories') \
                .insert(category_data) \
                .execute()
            
            return {
                'success': True,
                'category': response.data[0] if response.data else None,
                'message': 'Category created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get FAQ statistics
        
        Returns:
            {
                'success': bool,
                'stats': Dict,
                'error': str
            }
        """
        try:
            total_response = self.client.table('faqs') \
                .select('id', count='exact') \
                .execute()
            
            category_response = self.client.table('faqs') \
                .select('category') \
                .execute()
            
            categories = {}
            for faq in category_response.data:
                cat = faq.get('category', 'uncategorized')
                categories[cat] = categories.get(cat, 0) + 1
            
            popular_response = self.client.table('faqs') \
                .select('question, view_count') \
                .order('view_count', desc=True) \
                .limit(5) \
                .execute()
            
            helpful_response = self.client.table('faqs') \
                .select('question, helpful_count') \
                .order('helpful_count', desc=True) \
                .limit(5) \
                .execute()
            
            return {
                'success': True,
                'stats': {
                    'total_faqs': total_response.count,
                    'by_category': categories,
                    'most_viewed': popular_response.data,
                    'most_helpful': helpful_response.data
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def create_faq_management_tool(
    supabase_url: str = None,
    supabase_key: str = None,
    embedding_tool: EmbeddingTool = None
) -> FAQManagementTool:
    """
    Factory function to create a FAQManagementTool instance
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        embedding_tool: EmbeddingTool instance
    
    Returns:
        FAQManagementTool instance
    """
    return FAQManagementTool(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        embedding_tool=embedding_tool
    )
