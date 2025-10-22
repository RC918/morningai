#!/usr/bin/env python3
"""
Ops Agent Worker Management Dashboard
Web-based UI for managing and monitoring Ops Agent Workers
"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import subprocess
import signal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from orchestrator.task_queue.redis_queue import create_redis_queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ops Agent Worker Dashboard", version="1.0.0")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key for dashboard access"""
    expected_key = os.getenv("DASHBOARD_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Dashboard API key not configured. Set DASHBOARD_API_KEY environment variable."
        )
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

worker_process: Optional[subprocess.Popen] = None
redis_queue = None
websocket_connections: List[WebSocket] = []


class WorkerConfig(BaseModel):
    redis_url: str
    team_id: str
    poll_interval: int = 5


class WorkerCommand(BaseModel):
    action: str
    config: Optional[WorkerConfig] = None


@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    global redis_queue
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_queue = await create_redis_queue(redis_url=redis_url)
        logger.info(f"Connected to Redis at {redis_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global worker_process
    if worker_process and worker_process.poll() is None:
        worker_process.terminate()
        worker_process.wait(timeout=10)


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML"""
    return HTMLResponse(content=get_dashboard_html(), status_code=200)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "redis_connected": redis_queue is not None
    }


@app.get("/api/worker/status", dependencies=[Depends(verify_api_key)])
async def get_worker_status():
    """Get current worker status"""
    global worker_process
    
    status = "stopped"
    pid = None
    uptime = None
    cpu_percent = None
    memory_mb = None
    
    if worker_process and worker_process.poll() is None:
        status = "running"
        pid = worker_process.pid
        
        try:
            process = psutil.Process(pid)
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_mb = process.memory_info().rss / 1024 / 1024
            create_time = process.create_time()
            uptime = int(datetime.now().timestamp() - create_time)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            status = "error"
    
    return {
        "status": status,
        "pid": pid,
        "uptime_seconds": uptime,
        "cpu_percent": cpu_percent,
        "memory_mb": memory_mb,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/queue/stats", dependencies=[Depends(verify_api_key)])
async def get_queue_stats():
    """Get queue statistics"""
    if not redis_queue:
        raise HTTPException(status_code=503, detail="Redis not connected")
    
    try:
        stats = await redis_queue.get_queue_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/recent", dependencies=[Depends(verify_api_key)])
async def get_recent_tasks(limit: int = 10):
    """Get recent tasks"""
    if not redis_queue:
        raise HTTPException(status_code=503, detail="Redis not connected")
    
    try:
        all_tasks = await redis_queue.get_all_tasks()
        
        sorted_tasks = sorted(
            all_tasks,
            key=lambda t: t.created_at,
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "count": len(sorted_tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "type": task.type,
                    "status": task.status,
                    "priority": task.priority,
                    "assigned_to": task.assigned_to,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in sorted_tasks
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get recent tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/worker/start", dependencies=[Depends(verify_api_key)])
async def start_worker(config: WorkerConfig):
    """Start the worker process"""
    global worker_process
    
    if worker_process and worker_process.poll() is None:
        raise HTTPException(status_code=400, detail="Worker is already running")
    
    try:
        worker_script = os.path.join(
            os.path.dirname(__file__),
            "..",
            "worker.py"
        )
        
        vercel_token = os.getenv("VERCEL_TOKEN")
        if not vercel_token:
            raise HTTPException(
                status_code=500,
                detail="VERCEL_TOKEN not configured. Set VERCEL_TOKEN environment variable."
            )
        
        env = os.environ.copy()
        env.update({
            "REDIS_URL": config.redis_url,
            "VERCEL_TOKEN": vercel_token,
            "VERCEL_TEAM_ID": config.team_id,
            "WORKER_POLL_INTERVAL": str(config.poll_interval)
        })
        
        worker_process = subprocess.Popen(
            [sys.executable, worker_script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        await asyncio.sleep(2)
        
        if worker_process.poll() is not None:
            stdout, stderr = worker_process.communicate()
            raise HTTPException(
                status_code=500,
                detail=f"Worker failed to start: {stderr}"
            )
        
        await broadcast_message({
            "type": "worker_started",
            "pid": worker_process.pid,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "message": "Worker started successfully",
            "pid": worker_process.pid
        }
    
    except Exception as e:
        logger.error(f"Failed to start worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/worker/stop", dependencies=[Depends(verify_api_key)])
async def stop_worker():
    """Stop the worker process"""
    global worker_process
    
    if not worker_process or worker_process.poll() is not None:
        raise HTTPException(status_code=400, detail="Worker is not running")
    
    try:
        worker_process.terminate()
        
        try:
            worker_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker_process.kill()
            worker_process.wait()
        
        pid = worker_process.pid
        worker_process = None
        
        await broadcast_message({
            "type": "worker_stopped",
            "pid": pid,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "message": "Worker stopped successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to stop worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/worker/restart", dependencies=[Depends(verify_api_key)])
async def restart_worker(config: WorkerConfig):
    """Restart the worker process"""
    try:
        if worker_process and worker_process.poll() is None:
            await stop_worker()
        
        await asyncio.sleep(1)
        
        return await start_worker(config)
    
    except Exception as e:
        logger.error(f"Failed to restart worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    
    for ws in disconnected:
        websocket_connections.remove(ws)


def get_dashboard_html() -> str:
    """Generate dashboard HTML"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ops Agent Worker Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold mb-8 text-gray-800">Ops Agent Worker Dashboard</h1>
        
        <!-- Worker Control Panel -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-2xl font-semibold mb-4">Worker Control</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                    <input type="password" id="api-key" 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md"
                           placeholder="Enter Dashboard API Key">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Redis URL</label>
                    <input type="text" id="redis-url" value="redis://localhost:6379" 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Team ID</label>
                    <input type="text" id="team-id" 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Poll Interval (seconds)</label>
                    <input type="number" id="poll-interval" value="5" 
                           class="w-full px-3 py-2 border border-gray-300 rounded-md">
                </div>
            </div>
            
            <div class="flex gap-4">
                <button onclick="startWorker()" 
                        class="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-md">
                    Start Worker
                </button>
                <button onclick="stopWorker()" 
                        class="bg-red-500 hover:bg-red-600 text-white px-6 py-2 rounded-md">
                    Stop Worker
                </button>
                <button onclick="restartWorker()" 
                        class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md">
                    Restart Worker
                </button>
            </div>
        </div>
        
        <!-- Worker Status -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-2xl font-semibold mb-4">Worker Status</h2>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div class="text-center">
                    <div class="text-sm text-gray-600">Status</div>
                    <div id="worker-status" class="text-xl font-bold">-</div>
                </div>
                <div class="text-center">
                    <div class="text-sm text-gray-600">PID</div>
                    <div id="worker-pid" class="text-xl font-bold">-</div>
                </div>
                <div class="text-center">
                    <div class="text-sm text-gray-600">Uptime</div>
                    <div id="worker-uptime" class="text-xl font-bold">-</div>
                </div>
                <div class="text-center">
                    <div class="text-sm text-gray-600">CPU %</div>
                    <div id="worker-cpu" class="text-xl font-bold">-</div>
                </div>
                <div class="text-center">
                    <div class="text-sm text-gray-600">Memory (MB)</div>
                    <div id="worker-memory" class="text-xl font-bold">-</div>
                </div>
            </div>
        </div>
        
        <!-- Queue Statistics -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-2xl font-semibold mb-4">Queue Statistics</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="text-center p-4 bg-yellow-50 rounded-lg">
                    <div class="text-sm text-gray-600">Pending Tasks</div>
                    <div id="queue-pending" class="text-3xl font-bold text-yellow-600">-</div>
                </div>
                <div class="text-center p-4 bg-blue-50 rounded-lg">
                    <div class="text-sm text-gray-600">Processing Tasks</div>
                    <div id="queue-processing" class="text-3xl font-bold text-blue-600">-</div>
                </div>
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-sm text-gray-600">Total Tasks</div>
                    <div id="queue-total" class="text-3xl font-bold text-green-600">-</div>
                </div>
            </div>
        </div>
        
        <!-- Recent Tasks -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-2xl font-semibold mb-4">Recent Tasks</h2>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Task ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned To</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                        </tr>
                    </thead>
                    <tbody id="tasks-table" class="bg-white divide-y divide-gray-200">
                        <tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WebSocket message:', data);
                updateDashboard();
            };
            
            ws.onclose = () => {
                console.log('WebSocket closed, reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        function getHeaders() {
            const apiKey = document.getElementById('api-key').value;
            if (!apiKey) {
                throw new Error('API Key is required');
            }
            return {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            };
        }
        
        async function startWorker() {
            const config = {
                redis_url: document.getElementById('redis-url').value,
                team_id: document.getElementById('team-id').value,
                poll_interval: parseInt(document.getElementById('poll-interval').value)
            };
            
            try {
                const response = await fetch('/api/worker/start', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(config)
                });
                const data = await response.json();
                alert(data.message || 'Worker started');
                updateDashboard();
            } catch (error) {
                alert('Failed to start worker: ' + error);
            }
        }
        
        async function stopWorker() {
            try {
                const response = await fetch('/api/worker/stop', {
                    method: 'POST',
                    headers: getHeaders()
                });
                const data = await response.json();
                alert(data.message || 'Worker stopped');
                updateDashboard();
            } catch (error) {
                alert('Failed to stop worker: ' + error);
            }
        }
        
        async function restartWorker() {
            const config = {
                redis_url: document.getElementById('redis-url').value,
                team_id: document.getElementById('team-id').value,
                poll_interval: parseInt(document.getElementById('poll-interval').value)
            };
            
            try {
                const response = await fetch('/api/worker/restart', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(config)
                });
                const data = await response.json();
                alert(data.message || 'Worker restarted');
                updateDashboard();
            } catch (error) {
                alert('Failed to restart worker: ' + error);
            }
        }
        
        async function updateDashboard() {
            try {
                const headers = getHeaders();
                
                const statusResponse = await fetch('/api/worker/status', { headers });
                const status = await statusResponse.json();
                
                document.getElementById('worker-status').textContent = status.status;
                document.getElementById('worker-status').className = 
                    status.status === 'running' ? 'text-xl font-bold text-green-600' : 'text-xl font-bold text-red-600';
                document.getElementById('worker-pid').textContent = status.pid || '-';
                document.getElementById('worker-uptime').textContent = 
                    status.uptime_seconds ? `${Math.floor(status.uptime_seconds / 60)}m` : '-';
                document.getElementById('worker-cpu').textContent = 
                    status.cpu_percent ? status.cpu_percent.toFixed(1) : '-';
                document.getElementById('worker-memory').textContent = 
                    status.memory_mb ? status.memory_mb.toFixed(1) : '-';
                
                const queueResponse = await fetch('/api/queue/stats', { headers });
                const queue = await queueResponse.json();
                
                if (queue.success) {
                    document.getElementById('queue-pending').textContent = queue.stats.pending_tasks || 0;
                    document.getElementById('queue-processing').textContent = queue.stats.processing_tasks || 0;
                    document.getElementById('queue-total').textContent = queue.stats.total_tasks || 0;
                }
                
                const tasksResponse = await fetch('/api/tasks/recent?limit=10', { headers });
                const tasks = await tasksResponse.json();
                
                if (tasks.success) {
                    const tbody = document.getElementById('tasks-table');
                    if (tasks.tasks.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No tasks found</td></tr>';
                    } else {
                        tbody.innerHTML = tasks.tasks.map(task => `
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${task.task_id}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${task.type}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm">
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                        ${task.status === 'completed' ? 'bg-green-100 text-green-800' : 
                                          task.status === 'failed' ? 'bg-red-100 text-red-800' : 
                                          task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' : 
                                          'bg-yellow-100 text-yellow-800'}">
                                        ${task.status}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${task.priority}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${task.assigned_to || '-'}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    ${task.created_at ? new Date(task.created_at).toLocaleString() : '-'}
                                </td>
                            </tr>
                        `).join('');
                    }
                }
            } catch (error) {
                console.error('Failed to update dashboard:', error);
            }
        }
        
        connectWebSocket();
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
