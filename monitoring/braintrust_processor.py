"""
Braintrust Trace Processing Service

Receives traces from Vercel and processes them for monitoring and cost analysis.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Braintrust Trace Processor")


class TraceProcessor:
    """Process and store Vercel traces"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable required")
        
        self.cost_alert_threshold = float(os.getenv("COST_ALERT_THRESHOLD", "10.0"))
        self.latency_alert_threshold = float(os.getenv("LATENCY_ALERT_THRESHOLD", "500.0"))
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def calculate_llm_cost(self, model: str, tokens: int) -> float:
        """Calculate LLM cost based on model and token count"""
        pricing = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-4-turbo": {"input": 0.01 / 1000, "output": 0.03 / 1000},
            "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
        }
        
        if model not in pricing:
            model = "gpt-4"
        
        return tokens * pricing[model]["input"]
    
    def extract_metrics(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from trace data"""
        metadata = trace_data.get("metadata", {})
        
        metrics = {
            "timestamp": trace_data.get("timestamp", datetime.utcnow().isoformat()),
            "trace_id": trace_data.get("id", "unknown"),
            "duration_ms": trace_data.get("duration", 0),
            "status": trace_data.get("status", "unknown"),
            "url": trace_data.get("url", ""),
            "method": trace_data.get("method", ""),
            "llm_model": metadata.get("model", "unknown"),
            "llm_tokens": metadata.get("tokens", 0),
            "llm_cost": 0.0,
            "error": trace_data.get("error"),
            "user_agent": trace_data.get("user_agent"),
        }
        
        if metrics["llm_tokens"] > 0:
            metrics["llm_cost"] = self.calculate_llm_cost(
                metrics["llm_model"], 
                metrics["llm_tokens"]
            )
        
        return metrics
    
    async def save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to database"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trace_metrics (
                        timestamp, trace_id, duration_ms, status, url, method,
                        llm_model, llm_tokens, llm_cost, error, user_agent
                    ) VALUES (
                        %(timestamp)s, %(trace_id)s, %(duration_ms)s, %(status)s,
                        %(url)s, %(method)s, %(llm_model)s, %(llm_tokens)s,
                        %(llm_cost)s, %(error)s, %(user_agent)s
                    )
                    ON CONFLICT (trace_id) DO UPDATE SET
                        duration_ms = EXCLUDED.duration_ms,
                        status = EXCLUDED.status,
                        llm_cost = EXCLUDED.llm_cost
                """, metrics)
                conn.commit()
                
                logger.info(f"Saved metrics for trace {metrics['trace_id']}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save metrics: {e}")
            raise
        finally:
            conn.close()
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check if metrics trigger any alerts"""
        alerts = []
        
        if metrics["llm_cost"] > self.cost_alert_threshold:
            alerts.append({
                "type": "high_cost",
                "message": f"High LLM cost detected: ${metrics['llm_cost']:.2f}",
                "severity": "warning",
                "trace_id": metrics["trace_id"],
                "value": metrics["llm_cost"]
            })
        
        if metrics["duration_ms"] > self.latency_alert_threshold:
            alerts.append({
                "type": "high_latency",
                "message": f"High latency detected: {metrics['duration_ms']}ms",
                "severity": "warning",
                "trace_id": metrics["trace_id"],
                "value": metrics["duration_ms"]
            })
        
        if metrics["error"]:
            alerts.append({
                "type": "error",
                "message": f"Error in trace: {metrics['error']}",
                "severity": "error",
                "trace_id": metrics["trace_id"],
                "value": metrics["error"]
            })
        
        for alert in alerts:
            await self.send_alert(alert)
        
        return alerts
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification"""
        logger.warning(f"ALERT: {alert['message']}", extra=alert)
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alerts (
                        type, message, severity, trace_id, value, timestamp
                    ) VALUES (
                        %(type)s, %(message)s, %(severity)s, %(trace_id)s,
                        %(value)s, NOW()
                    )
                """, alert)
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save alert: {e}")
        finally:
            conn.close()


processor = TraceProcessor()


@app.post("/webhook/vercel-trace")
async def process_vercel_trace(request: Request):
    """
    Webhook endpoint for Vercel trace data
    """
    try:
        data = await request.json()
        
        metrics = processor.extract_metrics(data)
        
        await processor.save_metrics(metrics)
        
        alerts = await processor.check_alerts(metrics)
        
        return JSONResponse({
            "status": "ok",
            "trace_id": metrics["trace_id"],
            "alerts": len(alerts)
        })
    
    except Exception as e:
        logger.error(f"Failed to process trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = processor.get_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/metrics/summary")
async def get_metrics_summary(hours: int = 24):
    """Get metrics summary for the last N hours"""
    conn = processor.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_traces,
                    AVG(duration_ms) as avg_duration,
                    MAX(duration_ms) as max_duration,
                    SUM(llm_tokens) as total_tokens,
                    SUM(llm_cost) as total_cost,
                    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as error_count
                FROM trace_metrics
                WHERE timestamp > NOW() - INTERVAL '%s hours'
            """, (hours,))
            
            result = cursor.fetchone()
            
            return {
                "period_hours": hours,
                "summary": dict(result) if result else {}
            }
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/alerts/recent")
async def get_recent_alerts(limit: int = 100):
    """Get recent alerts"""
    conn = processor.get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM alerts
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            
            return {
                "count": len(results),
                "alerts": [dict(row) for row in results]
            }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
