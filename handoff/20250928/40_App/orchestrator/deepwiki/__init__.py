"""
DeepWiki Knowledge Base Service - Issue #1824

Provides code query and knowledge retrieval capabilities by integrating:
- Knowledge Graph patterns (bug/fix patterns)
- Error-fix pairs from past failures
- Code embeddings for semantic search
- Session insights for improvement suggestions

Feature Flag: ENABLE_DEEPWIKI (default: False)
"""

from deepwiki.service import DeepWikiService, get_deepwiki_service

__all__ = ["DeepWikiService", "get_deepwiki_service"]
