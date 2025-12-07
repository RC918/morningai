"""DeepWiki API - Knowledge Base Query Endpoints for Owner Console

This module provides API endpoints for querying the DeepWiki knowledge base
and retrieving session insights.

Issue: #2158
Phase: M5 - Meta Agent (Tier 5)
PR: PR 9 - DeepWiki API Endpoints
"""
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request

from src.middleware.auth_middleware import jwt_required, admin_required

logger = logging.getLogger(__name__)

# Try to import Redis client for session cache lookup
try:
    from src.utils.redis_client import get_redis_client
except ImportError:
    get_redis_client = None
    logger.debug("Redis client not available; DeepWiki session cache disabled")

# Try to import DeepWiki service
DEEPWIKI_AVAILABLE = False
try:
    import sys
    import os
    # Add orchestrator path to sys.path for DeepWiki imports
    orchestrator_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../orchestrator")
    )
    if orchestrator_path not in sys.path:
        sys.path.insert(0, orchestrator_path)

    from deepwiki.service import (
        get_deepwiki_service,
        QueryType,
    )
    DEEPWIKI_AVAILABLE = True
except ImportError as e:
    logger.warning("DeepWiki service not available: %s", e)

bp = Blueprint('deepwiki', __name__, url_prefix='/api/deepwiki')


def require_deepwiki_available(fn):
    """Decorator to check if DeepWiki is available before executing endpoint."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not DEEPWIKI_AVAILABLE:
            return jsonify({
                'error': 'DeepWiki service not available',
                'deepwiki_available': False,
            }), 503
        return fn(*args, **kwargs)
    return wrapper


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for DeepWiki API"""
    if not DEEPWIKI_AVAILABLE:
        return jsonify({
            'deepwiki_available': False,
            'status': 'unavailable',
            'timestamp': datetime.utcnow().isoformat()
        })

    try:
        deepwiki = get_deepwiki_service()
        health = deepwiki.health_check()
        return jsonify({
            'deepwiki_available': True,
            'status': health.get('status', 'unknown'),
            'components': health.get('components', {}),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.exception("DeepWiki health check failed")
        return jsonify({
            'deepwiki_available': True,
            'status': 'error',
            'error': str(e)[:100],
            'timestamp': datetime.utcnow().isoformat()
        })


@bp.route('/query', methods=['POST'])
@jwt_required
@admin_required
@require_deepwiki_available
def query_knowledge_base():
    """
    Query the DeepWiki knowledge base.

    Request body:
    - question: Natural language question or search query (required)
    - query_type: Type of query - code_question, error_lookup, pattern_search,
                  improvement_suggestion (default: code_question)
    - language: Optional language filter (e.g., 'python', 'javascript')
    - repo: Optional repository filter
    - limit: Maximum number of sources to return (default: 5, max: 10)

    Returns:
    - query_id: Unique identifier for this query
    - answer: Generated answer based on knowledge base
    - sources: List of source documents used
    - confidence: Confidence score (0-1)
    - latency_ms: Query latency in milliseconds

    Requires: Owner role
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        question = data.get('question')
        if not question or not question.strip():
            return jsonify({'error': 'Question is required'}), 400

        # Parse query type
        query_type_str = data.get('query_type', 'code_question')
        try:
            query_type = QueryType(query_type_str)
        except ValueError:
            valid_types = [qt.value for qt in QueryType]
            return jsonify({
                'error': f'Invalid query_type. Valid types: {valid_types}'
            }), 400

        language = data.get('language')
        repo = data.get('repo')
        try:
            limit = min(int(data.get('limit', 5)), 10)
        except (ValueError, TypeError):
            return jsonify({'error': 'limit must be an integer'}), 400

        deepwiki = get_deepwiki_service()
        result = deepwiki.query(
            question=question.strip(),
            query_type=query_type,
            language=language,
            repo=repo,
            limit=limit,
        )

        return jsonify({
            'query_id': result.query_id,
            'query_type': result.query_type.value,
            'question': result.question,
            'answer': result.answer,
            'sources': result.sources,
            'confidence': result.confidence,
            'latency_ms': result.latency_ms,
            'metadata': result.metadata,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception:
        logger.exception("Failed to query DeepWiki")
        return jsonify({'error': 'Failed to query knowledge base'}), 500


@bp.route('/insights/<session_id>', methods=['GET'])
@jwt_required
@admin_required
@require_deepwiki_available
def get_session_insights(session_id):
    """
    Get DeepWiki insights for a specific session.

    This endpoint retrieves pre-generated insights stored in session metadata,
    or generates new insights if not available.

    Path parameters:
    - session_id: The session ID to get insights for

    Returns:
    - session_id: Session identifier
    - insight_type: Type of insight (e.g., 'execution_analysis')
    - summary: Summary of the session analysis
    - recommendations: List of actionable recommendations
    - metrics: Session metrics (tasks completed, failed, etc.)

    Requires: Owner role
    """
    try:
        # Try to get pre-generated insights from Redis session store
        try:
            if get_redis_client is not None:
                redis_client = get_redis_client()

                # Check session store for insights
                session_key = f"dev_agent:session:{session_id}"
                session_data = redis_client.get(session_key)

                if session_data:
                    import json
                    session = json.loads(session_data)
                    insights = session.get('metadata', {}).get('deepwiki_insights')

                    if insights:
                        return jsonify({
                            'session_id': session_id,
                            'insight_type': insights.get('insight_type', 'execution_analysis'),
                            'summary': insights.get('summary', ''),
                            'recommendations': insights.get('recommendations', []),
                            'metrics': insights.get('metrics', {}),
                            'source': 'cached',
                            'timestamp': datetime.utcnow().isoformat()
                        })
        except Exception as e:
            logger.debug("Failed to get cached insights: %s", e)

        # Generate new insights if not cached
        deepwiki = get_deepwiki_service()
        insight = deepwiki.get_session_insights(session_id=session_id)

        return jsonify({
            'session_id': insight.session_id,
            'insight_type': insight.insight_type,
            'summary': insight.summary,
            'recommendations': insight.recommendations,
            'metrics': insight.metrics,
            'source': 'generated',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception:
        logger.exception("Failed to get session insights")
        return jsonify({'error': 'Failed to get session insights'}), 500


@bp.route('/error-lookup', methods=['POST'])
@jwt_required
@admin_required
@require_deepwiki_available
def lookup_error():
    """
    Look up similar past errors and their fixes.

    Request body:
    - error_text: The error message or stack trace to look up (required)
    - limit: Maximum number of results (default: 3, max: 10)

    Returns:
    - query_id: Unique identifier for this query
    - matches: List of similar past errors with fixes
    - confidence: Overall confidence score

    Requires: Owner role
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        error_text = data.get('error_text')
        if not error_text or not error_text.strip():
            return jsonify({'error': 'error_text is required'}), 400

        try:
            limit = min(int(data.get('limit', 3)), 10)
        except (ValueError, TypeError):
            return jsonify({'error': 'limit must be an integer'}), 400

        deepwiki = get_deepwiki_service()
        result = deepwiki.query(
            question=error_text.strip(),
            query_type=QueryType.ERROR_LOOKUP,
            limit=limit,
        )

        return jsonify({
            'query_id': result.query_id,
            'error_text': error_text.strip()[:200],
            'matches': result.sources,
            'answer': result.answer,
            'confidence': result.confidence,
            'latency_ms': result.latency_ms,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception:
        logger.exception("Failed to lookup error")
        return jsonify({'error': 'Failed to lookup error'}), 500


@bp.route('/patterns', methods=['POST'])
@jwt_required
@admin_required
@require_deepwiki_available
def search_patterns():
    """
    Search for relevant code patterns in the knowledge graph.

    Request body:
    - query: Search query for patterns (required)
    - language: Optional language filter (e.g., 'python', 'javascript')
    - limit: Maximum number of results (default: 5, max: 10)

    Returns:
    - query_id: Unique identifier for this query
    - patterns: List of matching code patterns
    - confidence: Overall confidence score

    Requires: Owner role
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        query = data.get('query')
        if not query or not query.strip():
            return jsonify({'error': 'query is required'}), 400

        language = data.get('language')
        try:
            limit = min(int(data.get('limit', 5)), 10)
        except (ValueError, TypeError):
            return jsonify({'error': 'limit must be an integer'}), 400

        deepwiki = get_deepwiki_service()
        result = deepwiki.query(
            question=query.strip(),
            query_type=QueryType.PATTERN_SEARCH,
            language=language,
            limit=limit,
        )

        return jsonify({
            'query_id': result.query_id,
            'query': query.strip()[:200],
            'patterns': result.sources,
            'answer': result.answer,
            'confidence': result.confidence,
            'latency_ms': result.latency_ms,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception:
        logger.exception("Failed to search patterns")
        return jsonify({'error': 'Failed to search patterns'}), 500


@bp.route('/suggestions', methods=['POST'])
@jwt_required
@admin_required
@require_deepwiki_available
def get_improvement_suggestions():
    """
    Get improvement suggestions based on context.

    Request body:
    - context: Code or error context to analyze (required)
    - language: Optional language hint (e.g., 'python', 'javascript')

    Returns:
    - query_id: Unique identifier for this query
    - suggestions: Formatted improvement suggestions
    - confidence: Confidence score

    Requires: Owner role
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        context = data.get('context')
        if not context or not context.strip():
            return jsonify({'error': 'context is required'}), 400

        language = data.get('language')

        deepwiki = get_deepwiki_service()
        result = deepwiki.query(
            question=context.strip(),
            query_type=QueryType.IMPROVEMENT_SUGGESTION,
            language=language,
        )

        return jsonify({
            'query_id': result.query_id,
            'context': context.strip()[:200] + ('...' if len(context) > 200 else ''),
            'suggestions': result.answer,
            'confidence': result.confidence,
            'latency_ms': result.latency_ms,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception:
        logger.exception("Failed to get improvement suggestions")
        return jsonify({'error': 'Failed to get improvement suggestions'}), 500
