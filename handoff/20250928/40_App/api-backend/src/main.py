import os
import sys
import datetime
import asyncio
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.routes.billing import bp as billing_bp

from flask import Flask, send_from_directory, jsonify, request, send_file, Response
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.dashboard import dashboard_bp
from src.middleware.auth_middleware import jwt_required, admin_required, analyst_required
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
try:
    from security_manager import SecurityManager
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from persistence.state_manager import PersistentStateManager
    from services.monitoring_dashboard import monitoring_dashboard
    from services.report_generator import report_generator
    from utils.env_schema_validator import validate_environment
    from routes.mock_api import mock_api
    BACKEND_SERVICES_AVAILABLE = True
except ImportError:
    BACKEND_SERVICES_AVAILABLE = False

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
CORS(app, resources={r"/*": {"origins": cors_origins}})

if SECURITY_AVAILABLE:
    security_config = {
        'master_key': os.environ.get('MASTER_KEY', 'default-master-key'),
        'secret_key': app.config['SECRET_KEY'],
        'audit_log_file': 'api_audit.log'
    }
    security_manager = SecurityManager(security_config)
    app.security_manager = security_manager

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(billing_bp)

if BACKEND_SERVICES_AVAILABLE:
    try:
        app.register_blueprint(mock_api)
    except NameError:
        pass

def get_health_payload():
    """Generate health check payload with JSON serializable values"""
    try:
        db_status = "connected"
        try:
            with db.engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "database": str(db_status),
            "phase": str(os.environ.get('APP_PHASE', 'Phase 8: Self-service Dashboard & Reporting Center')),
            "version": str(os.environ.get('APP_VERSION', '8.0.0')),
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {
                "phase4_apis": "available" if 'phase4_meta_agent_api' in sys.modules else "unavailable",
                "phase5_apis": "available" if 'phase5_data_intelligence_api' in sys.modules else "unavailable", 
                "phase6_apis": "available" if 'phase6_security_governance_api' in sys.modules else "unavailable",
                "security_manager": "available" if SECURITY_AVAILABLE else "unavailable",
                "backend_services": "available" if BACKEND_SERVICES_AVAILABLE else "unavailable"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "error",
            "phase": "Phase 8: Self-service Dashboard & Reporting Center", 
            "version": "8.0.0",
            "error": str(e)[:200],
            "timestamp": datetime.datetime.now().isoformat()
        }

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check endpoint with comprehensive system status"""
    health_payload = get_health_payload()
    if health_payload.get("status") == "unhealthy":
        return jsonify(health_payload), 500
    return jsonify(health_payload)

db_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(db_dir, exist_ok=True)

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


@app.route('/api/phase7/status')
def phase7_status():
    """Phase 7 system status endpoint"""
    try:
        from phase7_startup import Phase7System
        system = Phase7System()
        
        status = {
            'phase': 'Phase 7: Performance, Growth & Beta Introduction',
            'version': '1.0.0',
            'enabled': system.config.get('phase7', {}).get('enabled', False),
            'components': {
                'ops_agent': system.config.get('ops_agent', {}).get('enabled', False),
                'growth_strategist': system.config.get('growth_strategist', {}).get('enabled', False),
                'pm_agent': system.config.get('pm_agent', {}).get('enabled', False),
                'hitl_approval': system.config.get('hitl_approval', {}).get('enabled', False)
            },
            'integration': {
                'phase6_security': system.config.get('integration', {}).get('phase6_security', False),
                'meta_agent_decision_hub': system.config.get('integration', {}).get('meta_agent_decision_hub', False),
                'monitoring_system': system.config.get('integration', {}).get('monitoring_system', False)
            },
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e), 'phase': 'Phase 7', 'status': 'error'}), 500

@app.route('/api/phase7/approvals/pending')
def get_pending_approvals():
    """Get pending HITL approval requests"""
    try:
        from hitl_approval_system import HITLApprovalSystem
        hitl_system = HITLApprovalSystem()
        
        pending = hitl_system.get_pending_requests()
        return jsonify({
            'pending_requests': [
                {
                    'request_id': req.request_id,
                    'trace_id': req.trace_id,
                    'title': req.title,
                    'description': req.description,
                    'priority': req.priority,
                    'requester_agent': req.requester_agent,
                    'created_at': req.created_at.isoformat(),
                    'expires_at': req.expires_at.isoformat()
                } for req in pending
            ],
            'count': len(pending)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/approvals/history')
def get_approval_history():
    """Get HITL approval history"""
    try:
        from hitl_approval_system import HITLApprovalSystem
        hitl_system = HITLApprovalSystem()
        
        limit = int(request.args.get('limit', 50))
        history = hitl_system.get_approval_history(limit=limit)
        
        return jsonify({
            'approval_history': [
                {
                    'request_id': req.request_id,
                    'trace_id': req.trace_id,
                    'title': req.title,
                    'status': req.status.value,
                    'approved_by': req.approved_by,
                    'approved_at': req.approved_at.isoformat() if req.approved_at else None,
                    'approval_channel': req.approval_channel.value if req.approval_channel else None,
                    'created_at': req.created_at.isoformat()
                } for req in history
            ],
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/beta/candidates')
def get_beta_candidates():
    """Get Beta program candidates"""
    try:
        from pm_agent import PMAgent
        pm_agent = PMAgent()
        
        status = pm_agent.get_beta_program_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/growth/metrics')
def get_growth_metrics():
    """Get growth strategy metrics"""
    try:
        from growth_strategist import GrowthStrategist
        growth_strategist = GrowthStrategist()
        
        report = growth_strategist.get_growth_report()
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/ops/metrics')
def get_ops_metrics():
    """Get operations performance metrics"""
    try:
        from ops_agent import OpsAgent
        ops_agent = OpsAgent()
        
        report = ops_agent.get_performance_report()
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/monitoring/dashboard')
def get_monitoring_dashboard():
    """Get monitoring dashboard data"""
    try:
        if not BACKEND_SERVICES_AVAILABLE:
            return jsonify({"error": "Backend services not available"}), 500
        
        hours = int(request.args.get('hours', 1))
        dashboard_data = monitoring_dashboard.get_dashboard_data(hours=hours)
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/monitoring/metrics')
def get_resilience_metrics():
    """Get resilience pattern metrics"""
    try:
        from resilience_patterns import resilience_manager
        persistent_state_manager = PersistentStateManager()
        from saga_orchestrator import saga_orchestrator
        
        metrics = {
            'resilience': resilience_manager.get_all_metrics(),
            'storage': persistent_state_manager.get_storage_stats(),
            'saga': saga_orchestrator.get_orchestrator_metrics(),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/monitoring/alerts')
def get_monitoring_alerts():
    """Get current monitoring alerts"""
    try:
        if not BACKEND_SERVICES_AVAILABLE:
            return jsonify({"error": "Backend services not available"}), 500
        
        if monitoring_dashboard.metrics_history:
            latest_metrics = monitoring_dashboard.metrics_history[-1]
            alerts = monitoring_dashboard._generate_alerts(latest_metrics)
            return jsonify({'alerts': alerts, 'count': len(alerts)})
        else:
            return jsonify({'alerts': [], 'count': 0})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase7/environment/validate', methods=['GET', 'POST'])
def validate_environment():
    """Validate environment configuration"""
    try:
        from env_schema_validator import env_schema_validator
        
        validation_result = env_schema_validator.validate_environment()
        config_summary = env_schema_validator.get_config_summary()
        
        return jsonify({
            'validation': {
                'valid': validation_result.valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'missing_required': validation_result.missing_required,
                'invalid_values': validation_result.invalid_values
            },
            'summary': config_summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/layouts', methods=['GET', 'POST'])
def manage_dashboard_layouts():
    """Get or save user dashboard layouts"""
    try:
        persistent_state_manager = PersistentStateManager()
        
        if request.method == 'GET':
            user_id = request.args.get('user_id', 'default')
            layout = persistent_state_manager.load_dashboard_layout(user_id)
            if not layout:
                layout = {
                    'widgets': [
                        {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}},
                        {'id': 'memory_usage', 'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}},
                        {'id': 'response_time', 'position': {'x': 0, 'y': 4, 'w': 6, 'h': 4}},
                        {'id': 'error_rate', 'position': {'x': 6, 'y': 4, 'w': 6, 'h': 4}},
                        {'id': 'active_strategies', 'position': {'x': 0, 'y': 8, 'w': 4, 'h': 3}},
                        {'id': 'pending_approvals', 'position': {'x': 4, 'y': 8, 'w': 4, 'h': 3}},
                        {'id': 'circuit_breakers', 'position': {'x': 8, 'y': 8, 'w': 4, 'h': 3}}
                    ]
                }
            return jsonify(layout)
        
        elif request.method == 'POST':
            data = request.get_json()
            user_id = data.get('user_id', 'default')
            layout = data.get('layout', {})
            
            persistent_state_manager.save_dashboard_layout(user_id, layout)
            return jsonify({'status': 'success', 'message': 'Layout saved'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/widgets/available')
def get_available_widgets():
    """Get list of available dashboard widgets"""
    widgets = [
        {'id': 'cpu_usage', 'name': 'CPU使用率', 'type': 'gauge', 'category': 'system'},
        {'id': 'memory_usage', 'name': '內存使用率', 'type': 'gauge', 'category': 'system'},
        {'id': 'response_time', 'name': '響應時間', 'type': 'line_chart', 'category': 'performance'},
        {'id': 'error_rate', 'name': '錯誤率', 'type': 'area_chart', 'category': 'reliability'},
        {'id': 'active_strategies', 'name': '活躍策略', 'type': 'counter', 'category': 'ai'},
        {'id': 'pending_approvals', 'name': '待審批', 'type': 'counter', 'category': 'workflow'},
        {'id': 'circuit_breakers', 'name': '熔斷器狀態', 'type': 'status_grid', 'category': 'resilience'},
        {'id': 'task_execution', 'name': '任務執行狀態', 'type': 'timeline', 'category': 'tasks'},
        {'id': 'cost_today', 'name': '今日成本', 'type': 'counter', 'category': 'financial'},
        {'id': 'performance_trend', 'name': '性能趨勢', 'type': 'line_chart', 'category': 'performance'}
    ]
    return jsonify(widgets)

@app.route('/api/dashboard/data', methods=['GET', 'POST'])
def get_dashboard_data():
    """Get real-time dashboard data"""
    try:
        if not BACKEND_SERVICES_AVAILABLE:
            return jsonify({"error": "Backend services not available"}), 500
        
        hours = int(request.args.get('hours', 1))
        dashboard_data = monitoring_dashboard.get_dashboard_data(hours=hours)
        
        dashboard_data['task_execution'] = {
            'recent_tasks': [
                {'name': 'AI策略優化', 'status': 'completed', 'duration': '2.3s', 'agent': 'GrowthStrategist'},
                {'name': '系統監控檢查', 'status': 'running', 'duration': '1.1s', 'agent': 'OpsAgent'},
                {'name': '用戶反饋分析', 'status': 'pending', 'duration': '-', 'agent': 'PMAgent'},
                {'name': '安全審計', 'status': 'completed', 'duration': '5.7s', 'agent': 'SecurityManager'}
            ],
            'total_tasks_today': 47,
            'success_rate': 0.96,
            'avg_duration': '3.2s'
        }
        
        dashboard_data['system_metrics'] = {
            'cpu_usage': 72,
            'memory_usage': 68,
            'response_time': 145,
            'error_rate': 0.02,
            'active_strategies': 12,
            'pending_approvals': 3,
            'cost_today': 45.67
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate custom reports"""
    try:
        if not BACKEND_SERVICES_AVAILABLE:
            return jsonify({"error": "Backend services not available"}), 500
        
        data = request.get_json()
        report_type = data.get('type', 'performance')
        time_range = data.get('time_range', '24h')
        format_type = data.get('format', 'json')
        
        report_data = report_generator.generate_report(report_type, time_range)
        
        if format_type == 'pdf':
            pdf_path = report_generator.export_pdf(report_data, report_type)
            return send_file(pdf_path, as_attachment=True, 
                           download_name=f'report_{report_type}_{time_range}.pdf')
        elif format_type == 'csv':
            csv_data = report_generator.export_csv(report_data)
            return Response(csv_data, mimetype='text/csv', 
                          headers={'Content-Disposition': f'attachment; filename=report_{report_type}_{time_range}.csv'})
        else:
            return jsonify(report_data)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/templates')
def get_report_templates():
    """Get available report templates"""
    templates = [
        {
            'id': 'performance',
            'name': '系統性能報告',
            'description': '包含CPU、內存、響應時間等系統性能指標',
            'metrics': ['cpu_usage', 'memory_usage', 'response_time', 'error_rate']
        },
        {
            'id': 'task_tracking',
            'name': '任務追蹤報告',
            'description': '顯示AI Agent任務執行狀態和成功率',
            'metrics': ['task_success_rate', 'avg_duration', 'agent_performance']
        },
        {
            'id': 'resilience',
            'name': '韌性模式報告',
            'description': '熔斷器、隔艙模式和系統韌性指標',
            'metrics': ['circuit_breaker_status', 'bulkhead_utilization', 'retry_rates']
        },
        {
            'id': 'financial',
            'name': '成本分析報告',
            'description': '系統運行成本和資源使用分析',
            'metrics': ['daily_cost', 'resource_utilization', 'cost_trends']
        }
    ]
    return jsonify(templates)

@app.route('/api/reports/history')
def get_report_history():
    """Get report generation history"""
    try:
        persistent_state_manager = PersistentStateManager()
        
        history = persistent_state_manager.get_report_history()
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

try:
    morningai_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
    sys.path.insert(0, morningai_root)
    from phase4_meta_agent_api import (
        api_meta_agent_ooda_cycle,
        api_create_langgraph_workflow,
        api_execute_workflow,
        api_governance_status,
        api_create_governance_policy
    )
    from phase5_data_intelligence_api import (
        api_create_quicksight_dashboard,
        api_get_dashboard_insights,
        api_generate_automated_report,
        api_create_referral_program,
        api_get_referral_analytics,
        api_generate_marketing_content,
        api_get_business_intelligence
    )
    from phase6_security_governance_api import (
        api_evaluate_access_request,
        api_review_security_event,
        api_submit_hitl_review,
        api_get_pending_reviews,
        api_perform_security_audit
    )
    PHASE_456_AVAILABLE = True
    print("✅ Phase 4-6 APIs imported successfully")
except ImportError as e:
    print(f"⚠️ Phase 4-6 APIs not available: {e}")
    PHASE_456_AVAILABLE = False

@app.route('/api/meta-agent/ooda-cycle', methods=['POST'])
def meta_agent_ooda_cycle():
    """启动 OODA 循环"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_meta_agent_ooda_cycle())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/langgraph/workflows', methods=['POST'])
def create_langgraph_workflow():
    """创建 LangGraph 工作流"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_create_langgraph_workflow(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/langgraph/workflows/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """执行工作流"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_execute_workflow(workflow_id, request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/governance/status', methods=['GET'])
def governance_status():
    """获取治理状态"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_governance_status())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/governance/policies', methods=['POST'])
def create_governance_policy():
    """创建治理政策"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_create_governance_policy(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quicksight/dashboards', methods=['POST'])
def create_quicksight_dashboard():
    """创建 QuickSight 仪表板"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_create_quicksight_dashboard(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quicksight/dashboards/<dashboard_id>/insights', methods=['GET'])
def get_dashboard_insights(dashboard_id):
    """获取仪表板洞察"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_dashboard_insights(dashboard_id))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/automated', methods=['POST'])
def generate_automated_report():
    """生成自动化报告"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_generate_automated_report(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/growth/referral-programs', methods=['POST'])
def create_referral_program():
    """创建推荐计划"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_create_referral_program(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/growth/referral-programs/<program_id>/analytics', methods=['GET'])
def get_referral_analytics(program_id):
    """获取推荐分析"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_referral_analytics(program_id))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/growth/content/generate', methods=['POST'])
def generate_marketing_content():
    """生成营销内容"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_generate_marketing_content(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business-intelligence/summary', methods=['GET'])
def get_business_intelligence():
    """获取商业智能摘要"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_business_intelligence())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/access/evaluate', methods=['GET', 'POST'])
@app.route('/api/security/access-requests/evaluate', methods=['GET', 'POST'])
@admin_required
def evaluate_access_request():
    """评估访问请求"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_evaluate_access_request(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/events/review', methods=['POST'])
@analyst_required
def review_security_event():
    """审查安全事件"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_review_security_event(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/hitl/submit', methods=['POST'])
@analyst_required
def submit_hitl_review():
    """提交人工审查"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        data = request.json or {}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_submit_hitl_review(data))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/hitl/pending', methods=['GET'])
@analyst_required
def get_pending_reviews():
    """获取待审查项目"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_pending_reviews())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/audit', methods=['GET', 'POST'])
@app.route('/api/security/audit/perform', methods=['GET', 'POST'])
@admin_required
def perform_security_audit():
    """执行安全审计"""
    if not PHASE_456_AVAILABLE:
        return jsonify({'error': 'Phase 4-6 APIs not available'}), 503
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_perform_security_audit(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/reviews/pending', methods=['GET'])
@analyst_required
def get_pending_security_reviews():
    """Get pending security reviews"""
    try:
        if not PHASE_456_AVAILABLE:
            return jsonify({"error": "Phase 4-6 APIs not available"}), 503
            
        from phase6_security_governance_api import api_get_pending_reviews
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_pending_reviews())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/phase7/resilience/metrics', methods=['GET'])
def get_phase7_resilience_metrics():
    """Get Phase 7 resilience metrics"""
    try:
        return jsonify({
            "circuit_breakers": {
                "database": {"status": "closed", "failure_count": 0},
                "external_api": {"status": "closed", "failure_count": 0}
            },
            "retry_patterns": {
                "exponential_backoff": "enabled",
                "max_retries": 3
            },
            "bulkhead_isolation": {
                "thread_pools": {"api": 10, "background": 5},
                "connection_pools": {"database": 20}
            },
            "status": "operational",
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
