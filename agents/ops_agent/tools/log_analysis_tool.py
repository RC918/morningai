#!/usr/bin/env python3
"""
Log Analysis Tool - Log Collection and Analysis
"""
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Log entry"""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    metadata: Dict[str, Any]


@dataclass
class ErrorPattern:
    """Error pattern"""
    pattern: str
    count: int
    first_seen: datetime
    last_seen: datetime
    examples: List[str]


class LogAnalysisTool:
    """Tool for log analysis and pattern detection"""
    
    def __init__(self):
        """Initialize Log Analysis Tool"""
        self.logs: List[LogEntry] = []
        self.error_patterns: Dict[str, ErrorPattern] = {}
    
    async def search_logs(
        self,
        query: str,
        time_range: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search logs
        
        Args:
            query: Search query
            time_range: Time range (e.g., "1h", "24h")
            severity: Filter by severity
            limit: Maximum results
        
        Returns:
            Dict with search results
        """
        try:
            cutoff_time = self._parse_time_range(time_range) if time_range else None
            
            filtered_logs = []
            for log in self.logs:
                if cutoff_time and log.timestamp < cutoff_time:
                    continue
                
                if severity and log.level.value != severity:
                    continue
                
                if query and query.lower() not in log.message.lower():
                    continue
                
                filtered_logs.append(log)
                
                if len(filtered_logs) >= limit:
                    break
            
            return {
                'success': True,
                'logs': [
                    {
                        'timestamp': log.timestamp.isoformat(),
                        'level': log.level.value,
                        'message': log.message,
                        'source': log.source,
                        'metadata': log.metadata
                    }
                    for log in filtered_logs
                ],
                'total': len(filtered_logs)
            }
        
        except Exception as e:
            logger.error(f"Log search failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_error_patterns(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Analyze error patterns
        
        Args:
            time_range: Time range to analyze
        
        Returns:
            Dict with error patterns
        """
        try:
            cutoff_time = self._parse_time_range(time_range)
            
            error_logs = [
                log for log in self.logs
                if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                and log.timestamp >= cutoff_time
            ]
            
            patterns = defaultdict(list)
            for log in error_logs:
                pattern = self._extract_error_pattern(log.message)
                patterns[pattern].append(log)
            
            pattern_summaries = []
            for pattern, logs in patterns.items():
                pattern_summaries.append({
                    'pattern': pattern,
                    'count': len(logs),
                    'first_seen': min(log.timestamp for log in logs).isoformat(),
                    'last_seen': max(log.timestamp for log in logs).isoformat(),
                    'examples': [log.message for log in logs[:3]]
                })
            
            pattern_summaries.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'success': True,
                'patterns': pattern_summaries,
                'total_errors': len(error_logs),
                'unique_patterns': len(pattern_summaries)
            }
        
        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def detect_anomalies(self) -> Dict[str, Any]:
        """
        Detect anomalies in logs
        
        Returns:
            Dict with anomalies
        """
        try:
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            recent_errors = sum(
                1 for log in self.logs
                if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                and log.timestamp >= last_hour
            )
            
            day_errors = sum(
                1 for log in self.logs
                if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                and log.timestamp >= last_day
            )
            avg_errors_per_hour = day_errors / 24 if day_errors > 0 else 0
            
            anomalies = []
            if day_errors >= 10 and recent_errors > avg_errors_per_hour * 3:  # 3x threshold
                anomalies.append({
                    'type': 'error_spike',
                    'description': f'Error rate {recent_errors}/hour is 3x higher than average {avg_errors_per_hour:.1f}/hour',
                    'severity': 'high',
                    'detected_at': now.isoformat()
                })
            
            return {
                'success': True,
                'anomalies': anomalies,
                'total_anomalies': len(anomalies)
            }
        
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def add_log_entry(
        self,
        message: str,
        level: str = "info",
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a log entry
        
        Args:
            message: Log message
            level: Log level
            source: Log source
            metadata: Additional metadata
        
        Returns:
            Dict with result
        """
        try:
            log_entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel(level),
                message=message,
                source=source,
                metadata=metadata or {}
            )
            
            self.logs.append(log_entry)
            
            return {
                'success': True,
                'log_id': len(self.logs) - 1
            }
        
        except Exception as e:
            logger.error(f"Failed to add log entry: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_time_range(self, time_range: str) -> datetime:
        """Parse time range string (e.g., '1h', '24h', '7d')"""
        match = re.match(r'(\d+)([hmd])', time_range)
        if not match:
            raise ValueError(f"Invalid time range: {time_range}")
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        else:
            raise ValueError(f"Invalid time unit: {unit}")
        
        return datetime.utcnow() - delta
    
    def _extract_error_pattern(self, message: str) -> str:
        """Extract error pattern from message"""
        patterns = [
            (r'(\w+Error):', r'\1'),
            (r'(\w+Exception):', r'\1'),
            (r'Failed to (\w+)', r'Failed to \1'),
            (r'Cannot (\w+)', r'Cannot \1'),
        ]
        
        for pattern, replacement in patterns:
            match = re.search(pattern, message)
            if match:
                return re.sub(pattern, replacement, message)
        
        return message[:50]


def create_log_analysis_tool() -> LogAnalysisTool:
    """Factory function to create LogAnalysisTool instance"""
    return LogAnalysisTool()
