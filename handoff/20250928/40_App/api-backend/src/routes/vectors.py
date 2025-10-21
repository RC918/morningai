"""
Vector Visualization API Routes

Provides endpoints for pgvector space visualization and memory drift analysis.
"""
import os
import logging
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from src.middleware.auth_middleware import jwt_required
from src.utils.i18n import i18n, translate

logger = logging.getLogger(__name__)

bp = Blueprint('vectors', __name__, url_prefix='/api/vectors')


_DB_POOL = None

def _get_db_pool():
    global _DB_POOL
    if _DB_POOL is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        _DB_POOL = ThreadedConnectionPool(minconn=1, maxconn=int(os.getenv("DB_POOL_MAX", "10")), dsn=database_url)
    return _DB_POOL


def get_db_connection():
    pool = _get_db_pool()
    return pool.getconn()


def release_db_connection(conn):
    try:
        _get_db_pool().putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


@bp.route('/visualize', methods=['GET'])
@jwt_required
def visualize_vectors():
    """
    Generate vector space visualization using t-SNE or PCA
    
    Query params:
        - method: 'tsne' or 'pca' (default: tsne)
        - limit: number of vectors to visualize (default: 1000)
        - source: filter by source (optional)
        - dimensions: 2 or 3 (default: 2)
    
    Returns:
        Plotly JSON figure
    """
    method = request.args.get('method', 'tsne').lower()
    limit = int(request.args.get('limit', 1000))
    source = request.args.get('source')
    dimensions = int(request.args.get('dimensions', 2))
    
    if limit > 5000:
        return jsonify({"error": "Limit cannot exceed 5000"}), 400
    
    if dimensions not in [2, 3]:
        return jsonify({"error": "Dimensions must be 2 or 3"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                id,
                embedding,
                source,
                category,
                text_preview,
                query_count,
                created_at
            FROM vector_visualization
        """
        
        params = []
        if source:
            query += " WHERE source = %s"
            params.append(source)
        
        query += " ORDER BY query_count DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if len(results) == 0:
            return i18n.error_response(
                "not_found",
                404,
                message=translate("vector.no_vectors")
            )
        
        vectors = []
        metadata = []
        
        for row in results:
            if row['embedding']:
                vectors.append(row['embedding'])
                metadata.append({
                    'id': row['id'],
                    'source': row['source'] or 'unknown',
                    'category': row['category'] or 'uncategorized',
                    'text': (row['text_preview'] or '')[:100],
                    'query_count': row['query_count'] or 0,
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })
        
        if len(vectors) < 2:
            return i18n.error_response(
                "invalid_parameter",
                400,
                message=translate("vector.insufficient", count=2)
            )
        
        embeddings_array = np.array(vectors)
        
        if method == 'tsne':
            reducer = TSNE(n_components=dimensions, random_state=42, perplexity=min(30, len(vectors) - 1))
            reduced = reducer.fit_transform(embeddings_array)
        elif method == 'pca':
            reducer = PCA(n_components=dimensions, random_state=42)
            reduced = reducer.fit_transform(embeddings_array)
        else:
            return jsonify({"error": "Method must be 'tsne' or 'pca'"}), 400
        
        df = pd.DataFrame({
            'x': reduced[:, 0],
            'y': reduced[:, 1],
            'source': [m['source'] for m in metadata],
            'category': [m['category'] for m in metadata],
            'text': [m['text'] for m in metadata],
            'query_count': [m['query_count'] for m in metadata],
            'id': [m['id'] for m in metadata]
        })
        
        if dimensions == 3:
            df['z'] = reduced[:, 2]
        
        if dimensions == 2:
            fig = px.scatter(
                df,
                x='x',
                y='y',
                color='source',
                size='query_count',
                hover_data=['text', 'category', 'id'],
                title=f'Vector Space Visualization ({method.upper()}, {len(vectors)} vectors)',
                labels={'x': f'{method.upper()} 1', 'y': f'{method.upper()} 2'}
            )
        else:
            fig = px.scatter_3d(
                df,
                x='x',
                y='y',
                z='z',
                color='source',
                size='query_count',
                hover_data=['text', 'category', 'id'],
                title=f'Vector Space Visualization ({method.upper()}, {len(vectors)} vectors)',
                labels={'x': f'{method.upper()} 1', 'y': f'{method.upper()} 2', 'z': f'{method.upper()} 3'}
            )
        
        fig.update_layout(
            height=600,
            hovermode='closest'
        )
        
        cursor.close()
        release_db_connection(conn)
        
        return jsonify({
            "data": {
                "figure": fig.to_json(),
                "vector_count": len(vectors),
                "method": method,
                "dimensions": dimensions,
                "cached": False
            },
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Failed to visualize vectors: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route('/clusters', methods=['GET'])
@jwt_required
def get_clusters():
    """
    Get vector clusters
    
    Query params:
        - sample_size: number of vectors to sample (default: 1000)
        - min_cluster_size: minimum cluster size (default: 5)
    
    Returns:
        List of clusters with statistics
    """
    sample_size = int(request.args.get('sample_size', 1000))
    min_cluster_size = int(request.args.get('min_cluster_size', 5))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM get_vector_clusters(%s, %s)",
            (sample_size, min_cluster_size)
        )
        
        results = cursor.fetchall()
        
        clusters = [dict(row) for row in results]
        
        cursor.close()
        release_db_connection(conn)
        
        return jsonify({
            "data": {
                "clusters": clusters,
                "cluster_count": len(clusters),
                "sample_size": sample_size,
                "min_cluster_size": min_cluster_size
            },
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Failed to get clusters: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route('/drift', methods=['GET'])
@jwt_required
def detect_drift():
    """
    Detect memory drift
    
    Query params:
        - lookback_days: number of days to look back (default: 7)
    
    Returns:
        Memory drift analysis by source
    """
    lookback_days = int(request.args.get('lookback_days', 7))
    
    if lookback_days < 1 or lookback_days > 90:
        return jsonify({"error": "lookback_days must be between 1 and 90"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM detect_memory_drift(%s)",
            (lookback_days,)
        )
        
        results = cursor.fetchall()
        
        drift_analysis = [dict(row) for row in results]
        
        high_drift = [d for d in drift_analysis if d['status'] in ['HIGH_GROWTH', 'HIGH_DECLINE']]
        moderate_drift = [d for d in drift_analysis if d['status'] == 'MODERATE_DRIFT']
        stable = [d for d in drift_analysis if d['status'] == 'STABLE']
        
        cursor.close()
        release_db_connection(conn)
        
        return jsonify({
            "data": {
                "drift_analysis": drift_analysis,
                "summary": {
                    "total_sources": len(drift_analysis),
                    "high_drift_count": len(high_drift),
                    "moderate_drift_count": len(moderate_drift),
                    "stable_count": len(stable)
                },
                "lookback_days": lookback_days
            },
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Failed to detect drift: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route('/statistics', methods=['GET'])
@jwt_required
def get_statistics():
    """
    Get vector statistics by source
    
    Returns:
        Statistics for all vector sources
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM vector_statistics")
        
        results = cursor.fetchall()
        
        statistics = [dict(row) for row in results]
        
        for stat in statistics:
            if stat.get('oldest_vector'):
                stat['oldest_vector'] = stat['oldest_vector'].isoformat()
            if stat.get('newest_vector'):
                stat['newest_vector'] = stat['newest_vector'].isoformat()
        
        cursor.close()
        release_db_connection(conn)
        
        return jsonify({
            "data": {
                "statistics": statistics,
                "total_sources": len(statistics)
            },
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route('/refresh', methods=['POST'])
@jwt_required
def refresh_visualization():
    """
    Refresh vector visualization materialized view
    
    Returns:
        Success status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT refresh_vector_viz()")
        conn.commit()
        
        cursor.close()
        release_db_connection(conn)
        
        return jsonify({
            "data": {
                "status": "success",
                "message": "Vector visualization refreshed"
            },
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Failed to refresh visualization: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
