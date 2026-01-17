"""Agent Governance Framework"""
from pathlib import Path
import sys
import logging

logger = logging.getLogger(__name__)

repo_root = Path(__file__).resolve().parent
for _ in range(8):  # Limit search depth to avoid infinite loop
    if (repo_root / 'common').exists():
        break
    repo_root = repo_root.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Use try/except for each import to allow partial imports
# This ensures ai_policy can be imported even if other modules fail
__all__ = []

try:
    from .policy_guard import PolicyGuard, guarded
    __all__.extend(['PolicyGuard', 'guarded'])
except ImportError as e:
    logger.warning(f"Failed to import policy_guard: {e}")
    PolicyGuard = None
    guarded = None

try:
    from .cost_tracker import CostTracker, CostBudgetExceeded, get_cost_tracker
    __all__.extend(['CostTracker', 'CostBudgetExceeded', 'get_cost_tracker'])
except ImportError as e:
    logger.warning(f"Failed to import cost_tracker: {e}")
    CostTracker = None
    CostBudgetExceeded = None
    get_cost_tracker = None

try:
    from .reputation_engine import ReputationEngine, get_reputation_engine
    __all__.extend(['ReputationEngine', 'get_reputation_engine'])
except ImportError as e:
    logger.warning(f"Failed to import reputation_engine: {e}")
    ReputationEngine = None
    get_reputation_engine = None

try:
    from .permission_checker import PermissionChecker, PermissionDenied, get_permission_checker
    __all__.extend(['PermissionChecker', 'PermissionDenied', 'get_permission_checker'])
except ImportError as e:
    logger.warning(f"Failed to import permission_checker: {e}")
    PermissionChecker = None
    PermissionDenied = None
    get_permission_checker = None

try:
    from .violation_detector import ViolationDetector, ViolationError, get_violation_detector
    __all__.extend(['ViolationDetector', 'ViolationError', 'get_violation_detector'])
except ImportError as e:
    logger.warning(f"Failed to import violation_detector: {e}")
    ViolationDetector = None
    ViolationError = None
    get_violation_detector = None

try:
    from .ai_policy import (
        AIPolicy,
        AIPolicyManager,
        PolicyType,
        PolicyScope,
        PolicyStatus,
        get_ai_policy_manager,
        DEFAULT_POLICY_TEMPLATES
    )
    __all__.extend([
        'AIPolicy',
        'AIPolicyManager',
        'PolicyType',
        'PolicyScope',
        'PolicyStatus',
        'get_ai_policy_manager',
        'DEFAULT_POLICY_TEMPLATES',
    ])
except ImportError as e:
    logger.warning(f"Failed to import ai_policy: {e}")
    AIPolicy = None
    AIPolicyManager = None
    PolicyType = None
    PolicyScope = None
    PolicyStatus = None
    get_ai_policy_manager = None
    DEFAULT_POLICY_TEMPLATES = None

try:
    from .changeset_significance import (
        check_value_gate,
        get_changeset_hash,
        analyze_diff,
        calculate_significance_score,
        SignificanceResult,
        ChangeType,
    )
    __all__.extend([
        'check_value_gate',
        'get_changeset_hash',
        'analyze_diff',
        'calculate_significance_score',
        'SignificanceResult',
        'ChangeType',
    ])
except ImportError as e:
    logger.warning(f"Failed to import changeset_significance: {e}")
    check_value_gate = None
    get_changeset_hash = None
    analyze_diff = None
    calculate_significance_score = None
    SignificanceResult = None
    ChangeType = None

try:
    from .pr_deduplication import (
        check_pr_deduplication,
        record_pr_creation,
        cleanup_old_records,
        get_recent_pr_count,
        DeduplicationResult,
        PRRecord,
    )
    __all__.extend([
        'check_pr_deduplication',
        'record_pr_creation',
        'cleanup_old_records',
        'get_recent_pr_count',
        'DeduplicationResult',
        'PRRecord',
    ])
except ImportError as e:
    logger.warning(f"Failed to import pr_deduplication: {e}")
    check_pr_deduplication = None
    record_pr_creation = None
    cleanup_old_records = None
    get_recent_pr_count = None
    DeduplicationResult = None
    PRRecord = None

try:
    from .drift_detector import (
        DriftDetector,
        DriftDetectedError,
        DriftEvent,
        DriftType,
        DriftSeverity,
        DriftValidationResult,
        get_drift_detector,
        observe_response,
        reset_drift_detector,
    )
    __all__.extend([
        'DriftDetector',
        'DriftDetectedError',
        'DriftEvent',
        'DriftType',
        'DriftSeverity',
        'DriftValidationResult',
        'get_drift_detector',
        'observe_response',
        'reset_drift_detector',
    ])
except ImportError as e:
    logger.warning(f"Failed to import drift_detector: {e}")
    DriftDetector = None
    DriftDetectedError = None
    DriftEvent = None
    DriftType = None
    DriftSeverity = None
    DriftValidationResult = None
    get_drift_detector = None
    observe_response = None
    reset_drift_detector = None

try:
    from .health_alerter import (
        HealthAlertService,
        get_health_alert_service,
        reset_health_alert_service,
    )
    __all__.extend([
        'HealthAlertService',
        'get_health_alert_service',
        'reset_health_alert_service',
    ])
except ImportError as e:
    logger.warning(f"Failed to import health_alerter: {e}")
    HealthAlertService = None
    get_health_alert_service = None
    reset_health_alert_service = None

try:
    from .degradation_types import (
        DegradationSeverity,
        DegradationRecommendation,
        SEVERITY_MULTIPLIERS,
    )
    __all__.extend([
        'DegradationSeverity',
        'DegradationRecommendation',
        'SEVERITY_MULTIPLIERS',
    ])
except ImportError as e:
    logger.warning(f"Failed to import degradation_types: {e}")
    DegradationSeverity = None
    DegradationRecommendation = None
    SEVERITY_MULTIPLIERS = None

try:
    from .degradation_advisor import (
        DegradationPolicy,
        DegradationAdvisor,
        get_degradation_advisor,
        reset_degradation_advisor,
    )
    __all__.extend([
        'DegradationPolicy',
        'DegradationAdvisor',
        'get_degradation_advisor',
        'reset_degradation_advisor',
    ])
except ImportError as e:
    logger.warning(f"Failed to import degradation_advisor: {e}")
    DegradationPolicy = None
    DegradationAdvisor = None
    get_degradation_advisor = None
    reset_degradation_advisor = None

try:
    from .content_safety_scanner import (
        ContentSafetyScanner,
        ContentSafetyCategory,
        ContentRiskLevel,
        ContentSafetyAction,
        ContentSafetyFinding,
        ContentSafetyScanResult,
        get_content_safety_scanner,
        reset_content_safety_scanner,
        scan_content,
    )
    __all__.extend([
        'ContentSafetyScanner',
        'ContentSafetyCategory',
        'ContentRiskLevel',
        'ContentSafetyAction',
        'ContentSafetyFinding',
        'ContentSafetyScanResult',
        'get_content_safety_scanner',
        'reset_content_safety_scanner',
        'scan_content',
    ])
except ImportError as e:
    logger.warning(f"Failed to import content_safety_scanner: {e}")
    ContentSafetyScanner = None
    ContentSafetyCategory = None
    ContentRiskLevel = None
    ContentSafetyAction = None
    ContentSafetyFinding = None
    ContentSafetyScanResult = None
    get_content_safety_scanner = None
    reset_content_safety_scanner = None
    scan_content = None

try:
    from .pii_scanner import (
        PIIScanner,
        PIICategory,
        PIIRiskLevel,
        PIIAction,
        PIIFinding,
        PIIScanResult,
        get_pii_scanner,
        reset_pii_scanner,
        scan_for_pii,
    )
    __all__.extend([
        'PIIScanner',
        'PIICategory',
        'PIIRiskLevel',
        'PIIAction',
        'PIIFinding',
        'PIIScanResult',
        'get_pii_scanner',
        'reset_pii_scanner',
        'scan_for_pii',
    ])
except ImportError as e:
    logger.warning(f"Failed to import pii_scanner: {e}")
    PIIScanner = None
    PIICategory = None
    PIIRiskLevel = None
    PIIAction = None
    PIIFinding = None
    PIIScanResult = None
    get_pii_scanner = None
    reset_pii_scanner = None
    scan_for_pii = None

try:
    from .principal_context import (
        PrincipalContext,
        AgentType,
        CapabilityType,
        PrincipalContextManager,
        UNKNOWN_PRINCIPAL,
        DEFAULT_CAPABILITIES,
        create_principal_context,
        get_principal_from_context,
    )
    __all__.extend([
        'PrincipalContext',
        'AgentType',
        'CapabilityType',
        'PrincipalContextManager',
        'UNKNOWN_PRINCIPAL',
        'DEFAULT_CAPABILITIES',
        'create_principal_context',
        'get_principal_from_context',
    ])
except ImportError as e:
    logger.warning(f"Failed to import principal_context: {e}")
    PrincipalContext = None
    AgentType = None
    CapabilityType = None
    PrincipalContextManager = None
    UNKNOWN_PRINCIPAL = None
    DEFAULT_CAPABILITIES = None
    create_principal_context = None
    get_principal_from_context = None

try:
    from .routing_policy_evolver import (
        RoutingPolicyEvolver,
        RoutingPolicyChange,
        ChangeType,
        ChangeStatus,
        ChangeReason,
        get_routing_policy_evolver,
        reset_routing_policy_evolver,
    )
    __all__.extend([
        'RoutingPolicyEvolver',
        'RoutingPolicyChange',
        'ChangeType',
        'ChangeStatus',
        'ChangeReason',
        'get_routing_policy_evolver',
        'reset_routing_policy_evolver',
    ])
except ImportError as e:
    logger.warning(f"Failed to import routing_policy_evolver: {e}")
    RoutingPolicyEvolver = None
    RoutingPolicyChange = None
    ChangeType = None
    ChangeStatus = None
    ChangeReason = None
    get_routing_policy_evolver = None
    reset_routing_policy_evolver = None

try:
    from .safety_metrics import (
        SafetyMetricsCollector,
        SafetyMetricType,
        SafetyDecisionEvent,
        SafetyOverrideRequest,
        get_safety_metrics_collector,
        reset_safety_metrics_collector,
    )
    __all__.extend([
        'SafetyMetricsCollector',
        'SafetyMetricType',
        'SafetyDecisionEvent',
        'SafetyOverrideRequest',
        'get_safety_metrics_collector',
        'reset_safety_metrics_collector',
    ])
except ImportError as e:
    logger.warning(f"Failed to import safety_metrics: {e}")
    SafetyMetricsCollector = None
    SafetyMetricType = None
    SafetyDecisionEvent = None
    SafetyOverrideRequest = None
    get_safety_metrics_collector = None
    reset_safety_metrics_collector = None

try:
    from .evidence_ledger import (
        EvidenceLedger,
        DecisionRecord,
        DecisionType,
        DecisionOutcome,
        ReasoningChain,
        ReasoningStep,
        ReasoningStepType,
        AuditQuery,
        RetentionPolicy,
        get_evidence_ledger,
        reset_evidence_ledger,
    )
    __all__.extend([
        'EvidenceLedger',
        'DecisionRecord',
        'DecisionType',
        'DecisionOutcome',
        'ReasoningChain',
        'ReasoningStep',
        'ReasoningStepType',
        'AuditQuery',
        'RetentionPolicy',
        'get_evidence_ledger',
        'reset_evidence_ledger',
    ])
except ImportError as e:
    logger.warning(f"Failed to import evidence_ledger: {e}")
    EvidenceLedger = None
    DecisionRecord = None
    DecisionType = None
    DecisionOutcome = None
    ReasoningChain = None
    ReasoningStep = None
    ReasoningStepType = None
    AuditQuery = None
    RetentionPolicy = None
    get_evidence_ledger = None
    reset_evidence_ledger = None
