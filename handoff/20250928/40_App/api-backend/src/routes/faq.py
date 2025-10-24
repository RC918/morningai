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
from typing import Optional
import sys
import asyncio
from functools import wraps
from src.middleware.auth_middleware import jwt_required, admin_required
from src.middleware.rate_limit import rate_limit

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

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise RuntimeError("REDIS_URL environment variable is required but not set")

redis_client = Redis.from_url(
    redis_url, 
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
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(10, description="Results per page", ge=1, le=100)
    category: Optional[str] = Field(None, description="Filter by category")
    sort_by: Optional[str] = Field(None, description="Sort field (created_at, updated_at)")
    sort_order: str = Field("desc", description="Sort order (asc, desc)")
    
    @field_validator('q')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('query cannot be empty')
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v and v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be asc or desc')
        return v.lower() if v else 'desc'

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
    """Generate Redis cache key from parameters
    
    Key naming convention:
    - faq:search:{hash} for search queries
    - faq:item:{id} for individual FAQ items
    - faq:categories for category list
    - faq:stats for statistics
    """
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    return f"faq:{prefix}:{param_hash}"

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
    """Invalidate cache keys matching pattern
    
    Examples:
    - invalidate_cache_pattern("search") -> deletes all faq:search:* keys
    - invalidate_cache_pattern("item") -> deletes all faq:item:* keys
    """
    try:
        keys = list(redis_client.scan_iter(f"faq:{pattern}*"))
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching faq:{pattern}*")
            if sentry_sdk:
                sentry_sdk.add_breadcrumb(
                    category='cache',
                    message=f'Cache invalidation: {len(keys)} keys',
                    level='info',
                    data={'pattern': f'faq:{pattern}*', 'count': len(keys)}
                )
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

@bp.route("/search", methods=["GET"])
@rate_limit
@jwt_required
@async_route
async def search_faqs():
    """Search FAQs with semantic and keyword search
    
    Query Parameters:
        q (str): Search query (required)
        page (int): Page number (default: 1, min: 1)
        page_size (int): Results per page (default: 10, min: 1, max: 100)
        category (str): Filter by category (optional)
        sort_by (str): Sort field - created_at, updated_at (optional)
        sort_order (str): Sort order - asc, desc (default: desc)
    
    Returns:
        200: Search results with FAQs in {data: ...} format
        400: Invalid request parameters
        422: Validation error with detailed field errors
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
        sort_by = request.args.get('sort_by')
        sort_order = request.args.get('sort_order', 'desc')
        
        validated = FAQSearchRequest(
            q=query, 
            page=page, 
            page_size=page_size, 
            category=category,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
    except ValidationError as e:
        error_details = json.loads(e.json())
        return jsonify({
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": error_details
            }
        }), 422
    except ValueError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": str(e)
            }
        }), 400
    
    cache_key = generate_cache_key(
        "search", 
        q=validated.q, 
        page=validated.page,
        page_size=validated.page_size, 
        category=validated.category,
        sort_by=validated.sort_by,
        sort_order=validated.sort_order
    )
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='cache',
                message='FAQ search cache hit',
                level='info',
                data={'cache_key': cache_key, 'ttl': CACHE_TTL}
            )
        return jsonify({"data": cached_result, "cached": True}), 200
    
    try:
        search_tool = FAQSearchTool()
        limit = validated.page_size
        offset = (validated.page - 1) * validated.page_size
        
        result = await search_tool.search(
            query=validated.q,
            limit=limit + offset + 1,
            category=validated.category
        )
        
        if not result.get('success'):
            return jsonify({
                "error": {
                    "code": "search_failed",
                    "message": result.get('error', 'Search failed')
                }
            }), 500
        
        all_results = result.get('results', [])
        paginated_results = all_results[offset:offset + limit]
        has_more = len(all_results) > offset + limit
        
        response_data = {
            "query": validated.q,
            "results": paginated_results,
            "pagination": {
                "page": validated.page,
                "page_size": validated.page_size,
                "total_results": len(paginated_results),
                "has_more": has_more
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, response_data)
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ search completed',
                level='info',
                data={
                    'query': validated.q, 
                    'count': len(paginated_results),
                    'page': validated.page,
                    'cache_miss': True
                }
            )
        
        return jsonify({"data": response_data, "cached": False}), 200
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.exception(
            f"FAQ search error [{error_type}]: {error_msg}",
            extra={
                'query': validated.q,
                'page': validated.page,
                'category': validated.category,
                'error_type': error_type,
                'error_details': error_msg
            }
        )
        
        if sentry_sdk:
            sentry_sdk.set_context("faq_search", {
                "query": validated.q,
                "page": validated.page,
                "page_size": validated.page_size,
                "category": validated.category,
                "sort_by": validated.sort_by,
                "error_type": error_type
            })
            sentry_sdk.capture_exception(e)
        
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An error occurred while searching FAQs",
                "details": error_msg if os.getenv('DEBUG') == 'true' else None
            }
        }), 500

@bp.route("/<faq_id>", methods=["GET"])
@rate_limit
@jwt_required
@async_route
async def get_faq(faq_id):
    """Get FAQ by ID
    
    Args:
        faq_id (str): FAQ UUID
    
    Returns:
        200: FAQ details in {data: ...} format
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
    
    cache_key = generate_cache_key("item", id=faq_id)
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        return jsonify({"data": cached_result, "cached": True}), 200
    
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
        
        response_data = {
            "faq": result.get('faq'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, response_data)
        
        return jsonify({"data": response_data, "cached": False}), 200
        
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
@rate_limit
@admin_required
@async_route
async def create_faq():
    """Create new FAQ (Admin only)
    
    Request Body:
        question (str): FAQ question (required)
        answer (str): FAQ answer (required)
        category (str): FAQ category (optional)
        tags (list): FAQ tags (optional)
    
    Returns:
        201: FAQ created in {data: ...} format
        400: Invalid request
        422: Validation error
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
                "code": "validation_error",
                "message": "Request validation failed",
                "details": error_details
            }
        }), 422
    
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
        
        invalidate_cache_pattern("search:")
        invalidate_cache_pattern("categories:")
        
        faq = result.get('faq', {})
        faq_id = faq.get('id') if faq else None
        
        response_data = {
            "faq_id": faq_id,
            "message": "FAQ created successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ created',
                level='info',
                data={'faq_id': faq_id}
            )
        
        return jsonify({"data": response_data}), 201
        
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
@rate_limit
@admin_required
@async_route
async def update_faq(faq_id):
    """Update FAQ (Admin only)
    
    Args:
        faq_id (str): FAQ UUID
    
    Request Body:
        question (str): FAQ question (optional)
        answer (str): FAQ answer (optional)
        category (str): FAQ category (optional)
        tags (list): FAQ tags (optional)
    
    Returns:
        200: FAQ updated in {data: ...} format
        400: Invalid request
        404: FAQ not found
        422: Validation error
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
                "code": "validation_error",
                "message": "Request validation failed",
                "details": error_details
            }
        }), 422
    
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
        
        invalidate_cache_pattern("search:")
        invalidate_cache_pattern("item:")
        
        response_data = {
            "faq_id": faq_id,
            "message": "FAQ updated successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ updated',
                level='info',
                data={'faq_id': faq_id}
            )
        
        return jsonify({"data": response_data}), 200
        
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
@rate_limit
@admin_required
@async_route
async def delete_faq(faq_id):
    """Delete FAQ (Admin only)
    
    Args:
        faq_id (str): FAQ UUID
    
    Returns:
        200: FAQ deleted in {data: ...} format
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
        
        invalidate_cache_pattern("search:")
        invalidate_cache_pattern("item:")
        
        response_data = {
            "faq_id": faq_id,
            "message": "FAQ deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='faq',
                message='FAQ deleted',
                level='info',
                data={'faq_id': faq_id}
            )
        
        return jsonify({"data": response_data}), 200
        
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
@rate_limit
@jwt_required
@async_route
async def get_categories():
    """Get all FAQ categories
    
    Returns:
        200: List of categories in {data: ...} format
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
        return jsonify({"data": cached_result, "cached": True}), 200
    
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
        
        response_data = {
            "categories": result.get('categories', []),
            "count": result.get('count', 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, response_data, ttl=600)
        
        return jsonify({"data": response_data, "cached": False}), 200
        
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

@bp.route("/health", methods=["GET"])
@jwt_required
@async_route
async def health_check():
    """Database health check endpoint
    
    Returns:
        200: Health check passed
        503: Health check failed
    """
    health_status = {
        "service": "faq",
        "status": "unknown",
        "checks": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    health_status["checks"]["faq_agent"] = {
        "available": FAQ_AGENT_AVAILABLE,
        "status": "ok" if FAQ_AGENT_AVAILABLE else "unavailable"
    }
    
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "ok"}
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    if FAQ_AGENT_AVAILABLE:
        try:
            from agents.faq_agent.tools import FAQSearchTool
            search_tool = FAQSearchTool()
            
            test_result = await search_tool.search(query="test", limit=1, threshold=0.0)
            
            if test_result.get('success'):
                health_status["checks"]["database"] = {
                    "status": "ok",
                    "table_accessible": True,
                    "rpc_function": "match_faqs"
                }
            else:
                error_msg = test_result.get('error', 'Unknown error')
                health_status["checks"]["database"] = {
                    "status": "error",
                    "table_accessible": False,
                    "error": error_msg,
                    "hint": "Check if 'match_faqs' RPC function and 'faqs' table exist in Supabase"
                }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "hint": "Check Supabase connection string and pgvector extension"
            }
    
    all_ok = all(
        check.get("status") == "ok" 
        for check in health_status["checks"].values()
    )
    health_status["status"] = "healthy" if all_ok else "degraded"
    
    status_code = 200 if all_ok else 503
    
    if sentry_sdk and not all_ok:
        sentry_sdk.add_breadcrumb(
            category='health',
            message='FAQ service health check failed',
            level='warning',
            data=health_status["checks"]
        )
    
    return jsonify(health_status), status_code

@bp.route("/stats", methods=["GET"])
@rate_limit
@jwt_required
@async_route
async def get_stats():
    """Get FAQ statistics
    
    Returns:
        200: FAQ statistics in {data: ...} format
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
        return jsonify({"data": cached_result, "cached": True}), 200
    
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
        
        response_data = {
            "stats": result.get('stats', {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        set_cached_result(cache_key, response_data, ttl=60)
        
        return jsonify({"data": response_data, "cached": False}), 200
        
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
