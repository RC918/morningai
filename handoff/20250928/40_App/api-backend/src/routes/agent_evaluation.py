"""
Agent Evaluation API Routes

Provides endpoints for fetching and displaying agent evaluation results
from the Phase 1 evaluation framework.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required, roles_required

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

bp = Blueprint("agent_evaluation", __name__, url_prefix="/api/agent-evaluation")


def _fetch_evaluation_results_from_github(limit: int = 10) -> List[Dict]:
    """
    Fetch evaluation results from GitHub Actions artifacts.
    
    Args:
        limit: Maximum number of evaluation runs to fetch
        
    Returns:
        List of evaluation result dictionaries
    """
    try:
        from github import Github, GithubException
        
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.warning("GITHUB_TOKEN not set, returning empty results")
            return []
        
        repo_name = os.getenv('GITHUB_REPO', 'RC918/morningai')
        
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        workflow = repo.get_workflow('agent-evaluation.yml')
        runs = workflow.get_runs(status='completed')
        
        results = []
        count = 0
        
        for run in runs:
            if count >= limit:
                break
            
            try:
                artifacts = run.get_artifacts()
                
                for artifact in artifacts:
                    if artifact.name == 'evaluation-results':
                        
                        result = {
                            'id': f"{run.created_at.strftime('%Y-%m-%d')}-{run.id}",
                            'date': run.created_at.isoformat(),
                            'run_id': run.id,
                            'run_url': run.html_url,
                            'status': run.conclusion,
                            'artifact_url': artifact.archive_download_url,
                            'total_tasks': 0,
                            'completed': 0,
                            'pr_created': 0,
                            'ci_passed': 0,
                            'planner_accuracy': 0.0,
                            'self_healing_rate': 0.0,
                            'duration_seconds': 0
                        }
                        
                        results.append(result)
                        count += 1
                        break
                        
            except GithubException as e:
                logger.warning(f"Failed to fetch artifacts for run {run.id}: {e}")
                continue
        
        return results
        
    except ImportError:
        logger.error("PyGithub not installed. Install with: pip install PyGithub")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch evaluation results from GitHub: {e}")
        return []


def _calculate_aggregated_metrics(results: List[Dict]) -> Dict:
    """
    Calculate aggregated metrics from evaluation results.
    
    Args:
        results: List of evaluation result dictionaries
        
    Returns:
        Dictionary with aggregated metrics
    """
    if not results:
        return {
            'planner_accuracy': 0.0,
            'self_healing_rate': 0.0,
            'total_tasks': 0,
            'completed': 0,
            'completion_rate': 0.0,
            'ci_pass_rate': 0.0
        }
    
    latest = results[0] if results else {}
    
    return {
        'planner_accuracy': latest.get('planner_accuracy', 0.0),
        'self_healing_rate': latest.get('self_healing_rate', 0.0),
        'total_tasks': latest.get('total_tasks', 0),
        'completed': latest.get('completed', 0),
        'completion_rate': (latest.get('completed', 0) / latest.get('total_tasks', 1)) * 100 if latest.get('total_tasks', 0) > 0 else 0.0,
        'ci_pass_rate': (latest.get('ci_passed', 0) / latest.get('completed', 1)) * 100 if latest.get('completed', 0) > 0 else 0.0
    }


@bp.route("/results", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_evaluation_results():
    """
    Get agent evaluation results.
    
    Query Parameters:
        limit: Maximum number of evaluation runs to return (default: 10)
        
    Returns:
        JSON response with evaluation results and aggregated metrics
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if limit < 1 or limit > 100:
            return jsonify({
                'error': {
                    'code': 'invalid_parameter',
                    'message': 'limit must be between 1 and 100'
                }
            }), 400
        
        evaluations = _fetch_evaluation_results_from_github(limit=limit)
        
        latest_metrics = _calculate_aggregated_metrics(evaluations)
        
        return jsonify({
            'evaluations': evaluations,
            'latest': latest_metrics,
            'count': len(evaluations),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get evaluation results: {e}")
        return jsonify({
            'error': {
                'code': 'internal_error',
                'message': 'Failed to fetch evaluation results'
            }
        }), 500


@bp.route("/metrics", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_evaluation_metrics():
    """
    Get current agent evaluation metrics.
    
    Returns:
        JSON response with current metrics (Planner Accuracy, Self-Healing Rate, etc.)
    """
    try:
        evaluations = _fetch_evaluation_results_from_github(limit=1)
        
        if not evaluations:
            return jsonify({
                'metrics': {
                    'planner_accuracy': 0.0,
                    'self_healing_rate': 0.0,
                    'completion_rate': 0.0,
                    'ci_pass_rate': 0.0
                },
                'targets': {
                    'planner_accuracy': 70.0,
                    'self_healing_rate': 50.0,
                    'completion_rate': 80.0,
                    'ci_pass_rate': 90.0
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        latest = evaluations[0]
        
        metrics = {
            'planner_accuracy': latest.get('planner_accuracy', 0.0),
            'self_healing_rate': latest.get('self_healing_rate', 0.0),
            'completion_rate': (latest.get('completed', 0) / latest.get('total_tasks', 1)) * 100 if latest.get('total_tasks', 0) > 0 else 0.0,
            'ci_pass_rate': (latest.get('ci_passed', 0) / latest.get('completed', 1)) * 100 if latest.get('completed', 0) > 0 else 0.0
        }
        
        return jsonify({
            'metrics': metrics,
            'targets': {
                'planner_accuracy': 70.0,
                'self_healing_rate': 50.0,
                'completion_rate': 80.0,
                'ci_pass_rate': 90.0
            },
            'last_evaluation': latest.get('date'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get evaluation metrics: {e}")
        return jsonify({
            'error': {
                'code': 'internal_error',
                'message': 'Failed to fetch evaluation metrics'
            }
        }), 500


@bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for agent evaluation API."""
    return jsonify({
        'status': 'healthy',
        'service': 'agent-evaluation',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200
