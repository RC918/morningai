#!/usr/bin/env python3
"""
Worker Optimization Analysis Script
Analyzes Worker performance and provides optimization recommendations
"""
import os
import sys
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from orchestrator.task_queue.redis_queue import create_redis_queue


class WorkerOptimizationAnalyzer:
    """Analyzes Worker performance and provides recommendations"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.queue = None
        self.metrics = {
            "queue_depth": [],
            "task_processing_times": [],
            "error_rates": [],
            "throughput": []
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.queue = await create_redis_queue(redis_url=self.redis_url)
        print(f"✓ Connected to Redis at {self.redis_url}")
    
    async def analyze_queue_health(self) -> Dict[str, Any]:
        """Analyze queue health metrics"""
        print("\n📊 Analyzing Queue Health...")
        
        stats = await self.queue.get_queue_stats()
        
        pending = stats.get("pending_tasks", 0)
        processing = stats.get("processing_tasks", 0)
        total = stats.get("total_tasks", 0)
        
        health_score = 100
        issues = []
        recommendations = []
        
        if pending > 100:
            health_score -= 30
            issues.append(f"High queue depth: {pending} pending tasks")
            recommendations.append("Consider scaling Worker instances")
            recommendations.append("Increase WORKER_POLL_INTERVAL to process faster")
        
        if processing > 10:
            health_score -= 20
            issues.append(f"Many tasks in processing: {processing}")
            recommendations.append("Check for stuck tasks")
            recommendations.append("Implement task timeout mechanism")
        
        if pending == 0 and processing == 0:
            recommendations.append("Queue is healthy - consider reducing Worker resources")
        
        result = {
            "health_score": max(0, health_score),
            "stats": stats,
            "issues": issues,
            "recommendations": recommendations
        }
        
        print(f"  Health Score: {result['health_score']}/100")
        print(f"  Pending: {pending}, Processing: {processing}, Total: {total}")
        
        return result
    
    async def analyze_task_distribution(self) -> Dict[str, Any]:
        """Analyze task type distribution"""
        print("\n📈 Analyzing Task Distribution...")
        
        stats = await self.queue.get_queue_stats()
        
        recommendations = []
        
        pending = stats.get("pending_tasks", 0)
        processing = stats.get("processing_tasks", 0)
        total = stats.get("total_tasks", 0)
        
        if pending > total * 0.8:
            recommendations.append("Most tasks are pending - Worker may be slow or stopped")
        
        if processing > 5:
            recommendations.append("Many tasks in processing - check for stuck tasks")
        
        result = {
            "type_distribution": {"info": "Task type tracking not available in current implementation"},
            "status_distribution": {
                "pending": pending,
                "processing": processing,
                "completed_or_failed": total - pending - processing
            },
            "priority_distribution": {"info": "Priority tracking not available in current implementation"},
            "total_tasks": total,
            "recommendations": recommendations
        }
        
        print(f"  Total Tasks: {total}")
        print(f"  Pending: {pending}, Processing: {processing}")
        
        return result
    
    async def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
        """Analyze performance bottlenecks"""
        print("\n🔍 Analyzing Performance Bottlenecks...")
        
        bottlenecks = []
        recommendations = []
        
        start_time = time.time()
        stats = await self.queue.get_queue_stats()
        stats_latency = (time.time() - start_time) * 1000
        
        if stats_latency > 100:
            bottlenecks.append(f"High Redis latency: {stats_latency:.2f}ms")
            recommendations.append("Consider Redis connection pooling")
            recommendations.append("Check Redis server location (use same region)")
        
        stats = await self.queue.get_queue_stats()
        total_tasks = stats.get("total_tasks", 0)
        
        if total_tasks > 1000:
            bottlenecks.append(f"Large task count: {total_tasks}")
            recommendations.append("Implement task archiving")
            recommendations.append("Set TTL for completed tasks")
        
        result = {
            "bottlenecks": bottlenecks,
            "metrics": {
                "stats_latency_ms": stats_latency,
                "task_count": total_tasks
            },
            "recommendations": recommendations
        }
        
        print(f"  Stats Latency: {stats_latency:.2f}ms")
        print(f"  Task Count: {total_tasks}")
        print(f"  Bottlenecks Found: {len(bottlenecks)}")
        
        return result
    
    async def analyze_resource_optimization(self) -> Dict[str, Any]:
        """Analyze resource optimization opportunities"""
        print("\n⚡ Analyzing Resource Optimization...")
        
        stats = await self.queue.get_queue_stats()
        
        optimizations = []
        estimated_savings = {}
        
        pending = stats.get("pending_tasks", 0)
        processing = stats.get("processing_tasks", 0)
        total = stats.get("total_tasks", 0)
        
        if pending < 10 and processing < 2:
            optimizations.append("Low utilization - reduce Worker instances")
            estimated_savings["worker_cost"] = "30-50%"
        
        if total > 500:
            optimizations.append("Archive old completed tasks")
            estimated_savings["redis_memory"] = "20-40%"
        
        result = {
            "optimizations": optimizations,
            "estimated_savings": estimated_savings,
            "current_utilization": {
                "pending": pending,
                "processing": processing,
                "total": total
            }
        }
        
        print(f"  Optimization Opportunities: {len(optimizations)}")
        print(f"  Potential Savings: {estimated_savings}")
        
        return result
    
    async def analyze_security_posture(self) -> Dict[str, Any]:
        """Analyze security posture"""
        print("\n🔒 Analyzing Security Posture...")
        
        issues = []
        recommendations = []
        
        redis_url = os.getenv("REDIS_URL", "")
        if "localhost" in redis_url or "127.0.0.1" in redis_url:
            issues.append("Redis URL points to localhost (not production-ready)")
            recommendations.append("Use managed Redis service (e.g., Redis Cloud, AWS ElastiCache)")
        
        if not redis_url.startswith("rediss://"):
            issues.append("Redis connection not using TLS")
            recommendations.append("Enable TLS for Redis connections")
        
        vercel_token = os.getenv("VERCEL_TOKEN", "")
        if not vercel_token:
            issues.append("VERCEL_TOKEN not set")
            recommendations.append("Configure VERCEL_TOKEN in environment variables")
        
        jwt_secret = os.getenv("ORCHESTRATOR_JWT_SECRET", "")
        if not jwt_secret or len(jwt_secret) < 32:
            issues.append("JWT secret too short or missing")
            recommendations.append("Use strong JWT secret (>= 32 characters)")
        
        result = {
            "security_score": max(0, 100 - len(issues) * 20),
            "issues": issues,
            "recommendations": recommendations
        }
        
        print(f"  Security Score: {result['security_score']}/100")
        print(f"  Issues Found: {len(issues)}")
        
        return result
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        print("\n" + "="*60)
        print("🚀 Worker Optimization Analysis Report")
        print("="*60)
        
        queue_health = await self.analyze_queue_health()
        task_distribution = await self.analyze_task_distribution()
        bottlenecks = await self.analyze_performance_bottlenecks()
        resource_optimization = await self.analyze_resource_optimization()
        security = await self.analyze_security_posture()
        
        overall_score = (
            queue_health["health_score"] * 0.3 +
            (100 - len(bottlenecks["bottlenecks"]) * 20) * 0.3 +
            (100 - len(resource_optimization["optimizations"]) * 15) * 0.2 +
            security["security_score"] * 0.2
        )
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": max(0, min(100, overall_score)),
            "queue_health": queue_health,
            "task_distribution": task_distribution,
            "performance_bottlenecks": bottlenecks,
            "resource_optimization": resource_optimization,
            "security_posture": security,
            "summary": {
                "total_issues": (
                    len(queue_health["issues"]) +
                    len(bottlenecks["bottlenecks"]) +
                    len(security["issues"])
                ),
                "total_recommendations": (
                    len(queue_health["recommendations"]) +
                    len(task_distribution["recommendations"]) +
                    len(bottlenecks["recommendations"]) +
                    len(resource_optimization["optimizations"]) +
                    len(security["recommendations"])
                ),
                "production_ready": overall_score >= 70
            }
        }
        
        print("\n" + "="*60)
        print("📋 Summary")
        print("="*60)
        print(f"  Overall Score: {report['overall_score']:.1f}/100")
        print(f"  Total Issues: {report['summary']['total_issues']}")
        print(f"  Total Recommendations: {report['summary']['total_recommendations']}")
        print(f"  Production Ready: {'✓ YES' if report['summary']['production_ready'] else '✗ NO'}")
        
        if not report['summary']['production_ready']:
            print("\n⚠️  WARNING: System is NOT production-ready!")
            print("   Please address the issues above before deploying.")
        else:
            print("\n✓ System is production-ready!")
            print("  Consider implementing recommendations for optimal performance.")
        
        return report
    
    async def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save report to file"""
        if filename is None:
            filename = f"worker_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(project_root, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Report saved to: {filepath}")


async def main():
    """Main entry point"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    analyzer = WorkerOptimizationAnalyzer(redis_url)
    
    try:
        await analyzer.initialize()
        report = await analyzer.generate_report()
        await analyzer.save_report(report)
        
        return 0 if report['summary']['production_ready'] else 1
    
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
