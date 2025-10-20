"""
Embedding Tool - Generate embeddings for FAQ questions
"""

import os
from typing import Dict, Any, List
import openai


class EmbeddingTool:
    """Tool for generating text embeddings using OpenAI API"""
    
    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        """
        Initialize embedding tool
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Embedding model to use
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
    
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            {
                'success': bool,
                'embedding': List[float],  # 1536-dimensional vector
                'model': str,
                'error': str  # if success=False
            }
        """
        try:
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': 'Empty text provided'
                }
            
            response = await openai.Embedding.acreate(
                model=self.model,
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            
            return {
                'success': True,
                'embedding': embedding,
                'model': self.model,
                'dimensions': len(embedding)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum batch size (OpenAI limit is 2048)
        
        Returns:
            {
                'success': bool,
                'embeddings': List[List[float]],
                'model': str,
                'count': int,
                'failed_indices': List[int],
                'error': str
            }
        """
        try:
            if not texts:
                return {
                    'success': False,
                    'error': 'Empty text list provided'
                }
            
            embeddings = []
            failed_indices = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                try:
                    response = await openai.Embedding.acreate(
                        model=self.model,
                        input=batch
                    )
                    
                    batch_embeddings = [item['embedding'] for item in response['data']]
                    embeddings.extend(batch_embeddings)
                    
                except Exception as e:
                    failed_indices.extend(range(i, min(i + batch_size, len(texts))))
                    embeddings.extend([None] * len(batch))
            
            return {
                'success': len(failed_indices) == 0,
                'embeddings': embeddings,
                'model': self.model,
                'count': len(embeddings),
                'successful': len([e for e in embeddings if e is not None]),
                'failed_indices': failed_indices,
                'error': f'Failed to generate {len(failed_indices)} embeddings' if failed_indices else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def create_embedding_tool(api_key: str = None, model: str = "text-embedding-3-small") -> EmbeddingTool:
    """
    Factory function to create an EmbeddingTool instance
    
    Args:
        api_key: OpenAI API key
        model: Embedding model
    
    Returns:
        EmbeddingTool instance
    """
    return EmbeddingTool(api_key=api_key, model=model)
