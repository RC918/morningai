import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from redis import Redis, ConnectionError as RedisConnectionError
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from pydantic import BaseModel, Field, ValidationError, field_validator
import sys
import asyncio
from functools import wraps
from ..middleware.auth_middleware import jwt_required

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))

try:
    from agents.faq_agent.tools import FAQSearchTool, FAQManagementTool
    FAQ_AGENT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"FAQ Agent not available: {e}")
    FAQ_AGENT_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN and SENTRY_DSN.strip():
    try:
        import sentry_sdk
    except ImportError:
        sentry_sdk = None
else:
    sentry_sdk = None

bp = Blueprint("faq", __name__, url_prefix="/api/faq")

retry = Retry(ExponentialBackoff(base=1, cap=10), retries=3)
redis_client = Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"), 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=30,
    retry=retry,
    retry_on_timeout=True
)

CACHE_TTL = int(os.getenv("FAQ_CACHE_TTL", "300"))
OPENAI_MAX_DAILY_COST = float(os.getenv("OPENAI_MAX_DAILY_COST", "20.0"))

class FAQSearchRequest(BaseModel):
    """Request model for FAQ search"""
    q: str = Field(..., description="Search query")
    page: int = Field(1, description="Page number (1-indexed)", ge=1)
    page_size: int = Field(10, description="Items per page", ge=1, le=100)
    category: str = Field(None, description="Filter by category")
    
    @field_validator('q')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('query cannot be empty')
        return v

class FAQCreateRequest(BaseModel):
    """Request model for creating FAQ"""
    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")
    category: str = Field(None, description="FAQ category")
    tags: list = Field([], description="FAQ tags")
    
    @field_validator('question', 'answer')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('field cannot be empty')
        return v

class FAQUpdateRequest(BaseModel):
    """Request model for updating FAQ"""
    question: str = Field(None, description="FAQ question")
    answer: str = Field(None, description="FAQ answer")
    category: str = Field(None, description="FAQ category")
    tags: list = Field(None, description="FAQ tags")

def async_route(f):
    """Decorator to run async functions in Flask routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return decorated_function

def generate_cache_key(prefix: str, **params) -> str:
    """Generate Redis cache key from parameters"""
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    return f"faq:cache:{prefix}:{param_hash}"

def get_cached_result(cache_key: str):
    """Get cached result from Redis"""
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit: {cache_key}")
            return json.loads(cached)
        return None
    except RedisConnectionError as e:
        logger.warning(f"Redis connection error, skipping cache: {e}")
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None

def set_cached_result(cache_key: str, result: dict, ttl: int = CACHE_TTL):
    """Set cached result in Redis"""
    try:
        redis_client.setex(cache_key, ttl, json.dumps(result))
        logger.info(f"Cached result: {cache_key} (TTL: {ttl}s)")
    except RedisConnectionError as e:
        logger.warning(f"Redis connection error, skipping cache: {e}")
    except Exception as e:
        logger.error(f"Cache set error: {e}")

def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern"""
    try:
        keys = list(redis_client.scan_iter(f"faq:cache:{pattern}*"))
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

@bp.route("/search", methods=["GET"])
@jwt_required
@async_route
async def search_faqs():
    """Search FAQs with semantic and keyword search
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Query Parameters:
        q (str): Search query (required)
        page (int): Page number (default: 1)
        page_size (int): Items per page (default: 10, max: 100)
        category (str): Filter by category (optional)
    
    Returns:
        200: {"data": {...}, "cached": bool}
        400: Invalid request parameters
        401: Unauthorized
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    try:
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        category = request.args.get('category')
        
        validated = FAQSearchRequest(q=query, page=page, page_size=page_size, category=category)
        
    except ValidationError as e:
        error_details = json.loads(e.json())
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": error_details
            }
        }), 400
    except ValueError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": str(e)
            }
        }), 400
    
    cache_key = generate_cache_key("search", q=validated.q, page=validated.page, page_size=validated.page_size, category=validated.category)
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        return jsonify({
            "data": cached_result,
            "cached": True
        }), 200
    
    try:
        search_tool = FAQSearchTool()
        offset = (validated.page - 1) * validated.page_size
        result = await search_tool.search(
            query=validated.q,
            limit=validated.page_size,
            offset=offset,
            category=validated.category
        )
        
        if not result.get('success'):
            return jsonify({
                "error": {
                    "code": "search_failed",
                    "message": result.get('error', 'Search failed')
                }
            }), 500
        
        data = {
            "query": validated.q,
            "results": result.get('results', []),
            "count": result.get('count', 0),
            "page": validated.page,
            "page_size": validated.page_size,
            "total_pages": (result.get('count', 0) + validated.page_size - 1) // validated.page_size,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, data)
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ search completed',
                level='info',
                data={'query': validated.q, 'count': data['count'], 'user_id': request.current_user.get('user_id')}
            )
        
        return jsonify({
            "data": data,
            "cached": False
        }), 200
        
    except Exception as e:
        logger.exception(f"FAQ search error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while searching FAQs"
            }
        }), 500

@bp.route("/<faq_id>", methods=["GET"])
@jwt_required
@async_route
async def get_faq(faq_id):
    """Get FAQ by ID
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Args:
        faq_id (str): FAQ UUID
    
    Returns:
        200: {"data": {...}, "cached": bool}
        401: Unauthorized
        404: FAQ not found
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    cache_key = generate_cache_key("faq", id=faq_id)
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        return jsonify({
            "data": cached_result,
            "cached": True
        }), 200
    
    try:
        mgmt_tool = FAQManagementTool()
        result = await mgmt_tool.get_faq(faq_id)
        
        if not result.get('success'):
            error_msg = result.get('error', '')
            if 'not found' in error_msg.lower():
                return jsonify({
                    "error": {
                        "code": "not_found",
                        "message": f"FAQ {faq_id} not found"
                    }
                }), 404
            else:
                return jsonify({
                    "error": {
                        "code": "fetch_failed",
                        "message": error_msg
                    }
                }), 500
        
        data = {
            "faq": result.get('faq'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, data)
        
        return jsonify({
            "data": data,
            "cached": False
        }), 200
        
    except Exception as e:
        logger.exception(f"Get FAQ error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while fetching FAQ"
            }
        }), 500

@bp.route("", methods=["POST"])
@jwt_required
@async_route
async def create_faq():
    """Create new FAQ
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Request Body:
        question (str): FAQ question (required)
        answer (str): FAQ answer (required)
        category (str): FAQ category (optional)
        tags (list): FAQ tags (optional)
    
    Returns:
        201: {"data": {...}, "cached": false}
        400: Invalid request
        401: Unauthorized
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    try:
        payload = request.get_json(silent=True) or {}
        validated = FAQCreateRequest(**payload)
        
    except ValidationError as e:
        error_details = json.loads(e.json())
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": error_details
            }
        }), 400
    
    try:
        mgmt_tool = FAQManagementTool()
        result = await mgmt_tool.create_faq(
            question=validated.question,
            answer=validated.answer,
            category=validated.category,
            tags=validated.tags
        )
        
        if not result.get('success'):
            return jsonify({
                "error": {
                    "code": "create_failed",
                    "message": result.get('error', 'Failed to create FAQ')
                }
            }), 500
        
        invalidate_cache_pattern("search")
        invalidate_cache_pattern("categories")
        
        faq = result.get('faq', {})
        faq_id = faq.get('id') if faq else None
        
        data = {
            "faq_id": faq_id,
            "message": "FAQ created successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ created',
                level='info',
                data={'faq_id': data['faq_id'], 'user_id': request.current_user.get('user_id')}
            )
        
        return jsonify({
            "data": data,
            "cached": False
        }), 201
        
    except Exception as e:
        logger.exception(f"Create FAQ error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while creating FAQ"
            }
        }), 500

@bp.route("/<faq_id>", methods=["PUT"])
@jwt_required
@async_route
async def update_faq(faq_id):
    """Update FAQ
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Args:
        faq_id (str): FAQ UUID
    
    Request Body:
        question (str): FAQ question (optional)
        answer (str): FAQ answer (optional)
        category (str): FAQ category (optional)
        tags (list): FAQ tags (optional)
    
    Returns:
        200: {"data": {...}, "cached": false}
        400: Invalid request
        401: Unauthorized
        404: FAQ not found
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    try:
        payload = request.get_json(silent=True) or {}
        validated = FAQUpdateRequest(**payload)
        
    except ValidationError as e:
        error_details = json.loads(e.json())
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": error_details
            }
        }), 400
    
    updates = {}
    if validated.question is not None:
        updates['question'] = validated.question
    if validated.answer is not None:
        updates['answer'] = validated.answer
    if validated.category is not None:
        updates['category'] = validated.category
    if validated.tags is not None:
        updates['tags'] = validated.tags
    
    if not updates:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "No fields to update"
            }
        }), 400
    
    try:
        mgmt_tool = FAQManagementTool()
        result = await mgmt_tool.update_faq(faq_id, **updates)
        
        if not result.get('success'):
            error_msg = result.get('error', '')
            if 'not found' in error_msg.lower():
                return jsonify({
                    "error": {
                        "code": "not_found",
                        "message": f"FAQ {faq_id} not found"
                    }
                }), 404
            else:
                return jsonify({
                    "error": {
                        "code": "update_failed",
                        "message": error_msg
                    }
                }), 500
        
        invalidate_cache_pattern("search")
        invalidate_cache_pattern(f"faq")
        
        data = {
            "faq_id": faq_id,
            "message": "FAQ updated successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ updated',
                level='info',
                data={'faq_id': faq_id, 'user_id': request.current_user.get('user_id')}
            )
        
        return jsonify({
            "data": data,
            "cached": False
        }), 200
        
    except Exception as e:
        logger.exception(f"Update FAQ error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while updating FAQ"
            }
        }), 500

@bp.route("/<faq_id>", methods=["DELETE"])
@jwt_required
@async_route
async def delete_faq(faq_id):
    """Delete FAQ
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Args:
        faq_id (str): FAQ UUID
    
    Returns:
        200: {"data": {...}, "cached": false}
        401: Unauthorized
        404: FAQ not found
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    try:
        mgmt_tool = FAQManagementTool()
        result = await mgmt_tool.delete_faq(faq_id)
        
        if not result.get('success'):
            error_msg = result.get('error', '')
            if 'not found' in error_msg.lower():
                return jsonify({
                    "error": {
                        "code": "not_found",
                        "message": f"FAQ {faq_id} not found"
                    }
                }), 404
            else:
                return jsonify({
                    "error": {
                        "code": "delete_failed",
                        "message": error_msg
                    }
                }), 500
        
        invalidate_cache_pattern("search")
        invalidate_cache_pattern(f"faq")
        
        data = {
            "faq_id": faq_id,
            "message": "FAQ deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ deleted',
                level='info',
                data={'faq_id': faq_id, 'user_id': request.current_user.get('user_id')}
            )
        
        return jsonify({
            "data": data,
            "cached": False
        }), 200
        
    except Exception as e:
        logger.exception(f"Delete FAQ error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while deleting FAQ"
            }
        }), 500

@bp.route("/categories", methods=["GET"])
@jwt_required
@async_route
async def get_categories():
    """Get all FAQ categories
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Returns:
        200: {"data": {...}, "cached": bool}
        401: Unauthorized
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    cache_key = generate_cache_key("categories")
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        return jsonify({
            "data": cached_result,
            "cached": True
        }), 200
    
    try:
        mgmt_tool = FAQManagementTool()
        result = await mgmt_tool.get_categories()
        
        if not result.get('success'):
            return jsonify({
                "error": {
                    "code": "fetch_failed",
                    "message": result.get('error', 'Failed to fetch categories')
                }
            }), 500
        
        data = {
            "categories": result.get('categories', []),
            "count": result.get('count', 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, data, ttl=600)
        
        return jsonify({
            "data": data,
            "cached": False
        }), 200
        
    except Exception as e:
        logger.exception(f"Get categories error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while fetching categories"
            }
        }), 500

@bp.route("/stats", methods=["GET"])
@jwt_required
@async_route
async def get_stats():
    """Get FAQ statistics
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Returns:
        200: {"data": {...}, "cached": bool}
        401: Unauthorized
        500: Server error
        503: Service unavailable
    """
    if not FAQ_AGENT_AVAILABLE:
        return jsonify({
            "error": {
                "code": "service_unavailable",
                "message": "FAQ service is not available"
            }
        }), 503
    
    cache_key = generate_cache_key("stats")
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        return jsonify({
            "data": cached_result,
            "cached": True
        }), 200
    
    try:
        mgmt_tool = FAQManagementTool()
        result = await mgmt_tool.get_stats()
        
        if not result.get('success'):
            return jsonify({
                "error": {
                    "code": "fetch_failed",
                    "message": result.get('error', 'Failed to fetch stats')
                }
            }), 500
        
        data = {
            "stats": result.get('stats', {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, data, ttl=60)
        
        return jsonify({
            "data": data,
            "cached": False
        }), 200
        
    except Exception as e:
        logger.exception(f"Get stats error: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while fetching stats"
            }
        }), 500
