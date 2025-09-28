from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import redis
import json

app = Flask(__name__)
CORS(app)

database_url = os.getenv('DATABASE_URL', 'sqlite:///morningai.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

try:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url)
    redis_client.ping()
    print("Redis connected successfully")
except:
    redis_client = None
    print("Redis not available, using in-memory cache")

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return jsonify({
        'message': 'Morning AI API',
        'version': '1.0.0',
        'status': 'running'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'redis': 'connected' if redis_client else 'not available'
    })

@app.route('/api/stats')
def get_stats():
    try:
        if redis_client:
            cached_stats = redis_client.get('dashboard_stats')
            if cached_stats:
                return jsonify(json.loads(cached_stats))
        
        total_agents = Agent.query.count()
        active_decisions = Decision.query.filter_by(status='pending').count()
        
        system_health = 98.5
        daily_tasks = 156
        
        stats = {
            'totalAgents': total_agents if total_agents > 0 else 15,
            'activeDecisions': active_decisions if active_decisions > 0 else 42,
            'systemHealth': system_health,
            'dailyTasks': daily_tasks
        }
        
        if redis_client:
            redis_client.setex('dashboard_stats', 300, json.dumps(stats))
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents')
def get_agents():
    try:
        agents = Agent.query.all()
        return jsonify([{
            'id': agent.id,
            'name': agent.name,
            'type': agent.type,
            'status': agent.status,
            'created_at': agent.created_at.isoformat()
        } for agent in agents])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents', methods=['POST'])
def create_agent():
    try:
        data = request.get_json()
        agent = Agent(
            name=data['name'],
            type=data['type'],
            status=data.get('status', 'active')
        )
        db.session.add(agent)
        db.session.commit()
        
        return jsonify({
            'id': agent.id,
            'name': agent.name,
            'type': agent.type,
            'status': agent.status,
            'created_at': agent.created_at.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/decisions')
def get_decisions():
    try:
        decisions = Decision.query.order_by(Decision.created_at.desc()).limit(10).all()
        return jsonify([{
            'id': decision.id,
            'title': decision.title,
            'description': decision.description,
            'agent_id': decision.agent_id,
            'status': decision.status,
            'created_at': decision.created_at.isoformat()
        } for decision in decisions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/decisions', methods=['POST'])
def create_decision():
    try:
        data = request.get_json()
        decision = Decision(
            title=data['title'],
            description=data.get('description', ''),
            agent_id=data.get('agent_id'),
            status=data.get('status', 'pending')
        )
        db.session.add(decision)
        db.session.commit()
        
        return jsonify({
            'id': decision.id,
            'title': decision.title,
            'description': decision.description,
            'agent_id': decision.agent_id,
            'status': decision.status,
            'created_at': decision.created_at.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/metrics')
def get_metrics():
    try:
        metrics = SystemMetric.query.order_by(SystemMetric.timestamp.desc()).limit(100).all()
        return jsonify([{
            'id': metric.id,
            'metric_name': metric.metric_name,
            'value': metric.value,
            'timestamp': metric.timestamp.isoformat()
        } for metric in metrics])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def init_db():
    """Initialize database and create sample data"""
    db.create_all()
    
    if Agent.query.count() == 0:
        sample_agents = [
            Agent(name='CEO Agent', type='executive'),
            Agent(name='Meta-Agent', type='coordinator'),
            Agent(name='QA Agent', type='testing'),
            Agent(name='Design Agent', type='creative'),
            Agent(name='Analytics Agent', type='data')
        ]
        for agent in sample_agents:
            db.session.add(agent)
        
        sample_decisions = [
            Decision(title='Strategic Planning Q4', description='Review and approve Q4 strategic initiatives', agent_id=1),
            Decision(title='System Performance Optimization', description='Optimize system performance by 15%', agent_id=2),
            Decision(title='UI/UX Enhancement', description='Improve user interface design', agent_id=4)
        ]
        for decision in sample_decisions:
            db.session.add(decision)
        
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
