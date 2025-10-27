#!/usr/bin/env python3
"""
Redis TLS Configuration Validator

Validates that Redis connections use TLS encryption in production environments.
This script checks:
1. Environment variables are properly configured
2. Redis URLs use secure protocols (rediss:// or HTTPS)
3. Helper function enforces TLS in production
4. All production code uses the secure helper function

Usage:
    python scripts/validate_redis_tls.py
    
Exit codes:
    0: All checks passed
    1: Validation failed
"""

import os
import sys
import logging
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../handoff/20250928/40_App/api-backend/src'))

from utils.redis_config import get_secure_redis_url, is_redis_tls_enabled, get_redis_connection_info

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisSecurityValidator:
    """Validates Redis security configuration"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []
    
    def validate_environment_variables(self) -> bool:
        """Validate environment variable configuration"""
        logger.info("🔍 Validating environment variables...")
        
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
        upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        redis_url = os.getenv("REDIS_URL")
        environment = os.getenv("ENVIRONMENT", "development")
        testing = os.getenv("TESTING")
        
        if upstash_url and upstash_token:
            self.passed_checks.append("✅ Upstash Redis configured (HTTPS/TLS enabled)")
            if not upstash_url.startswith("https://"):
                self.errors.append("❌ UPSTASH_REDIS_REST_URL must use HTTPS")
                return False
        elif redis_url:
            if redis_url.startswith("rediss://"):
                self.passed_checks.append("✅ Redis URL uses TLS (rediss://)")
            elif redis_url.startswith("redis://localhost") and (testing == "true" or environment == "development"):
                self.warnings.append("⚠️ Using local Redis without TLS (development/testing only)")
            elif redis_url.startswith("redis://"):
                if environment == "production":
                    self.errors.append("❌ Redis URL must use TLS (rediss://) in production")
                    return False
                else:
                    self.warnings.append("⚠️ Redis URL does not use TLS (not recommended for production)")
        else:
            if environment == "production":
                self.errors.append("❌ No Redis configuration found (UPSTASH_REDIS_REST_URL or REDIS_URL required)")
                return False
            else:
                self.warnings.append("⚠️ No Redis configuration found")
        
        return True
    
    def validate_helper_function(self) -> bool:
        """Validate helper function behavior"""
        logger.info("🔍 Validating helper function...")
        
        try:
            tls_enabled = is_redis_tls_enabled()
            if tls_enabled:
                self.passed_checks.append("✅ Redis TLS is enabled")
            else:
                environment = os.getenv("ENVIRONMENT", "development")
                testing = os.getenv("TESTING")
                if environment == "production" and testing != "true":
                    self.errors.append("❌ Redis TLS is not enabled in production")
                    return False
                else:
                    self.warnings.append("⚠️ Redis TLS is not enabled (development/testing only)")
            
            conn_info = get_redis_connection_info()
            logger.info(f"📊 Connection info: {conn_info}")
            
            if conn_info['secure']:
                self.passed_checks.append(f"✅ Secure connection: {conn_info['type']} ({conn_info['protocol']})")
            else:
                if conn_info.get('local_dev'):
                    self.warnings.append("⚠️ Using local development Redis (not secure)")
                else:
                    self.errors.append("❌ Insecure Redis connection detected")
                    return False
            
            try:
                redis_url = get_secure_redis_url(allow_local=os.getenv("TESTING") == "true")
                logger.info(f"✅ Helper function returned: {redis_url[:30]}...")
                self.passed_checks.append("✅ Helper function works correctly")
            except ValueError as e:
                self.errors.append(f"❌ Helper function failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Helper function validation failed: {e}")
            return False
    
    def validate_production_code(self) -> bool:
        """Validate that production code uses secure Redis helper"""
        logger.info("🔍 Validating production code...")
        
        production_files = [
            "orchestrator/redis_queue/worker.py",
            "orchestrator/governance/cost_tracker.py",
            "orchestrator/api/main.py",
            "agents/ops_agent/worker.py",
            "orchestrator/integrations/ops_agent_client.py",
            "meta_agent_decision_hub.py"
        ]
        
        repo_root = os.path.join(os.path.dirname(__file__), '..')
        
        for file_path in production_files:
            full_path = os.path.join(repo_root, file_path)
            if not os.path.exists(full_path):
                self.warnings.append(f"⚠️ File not found: {file_path}")
                continue
            
            with open(full_path, 'r') as f:
                content = f.read()
            
            if 'get_secure_redis_url' in content:
                self.passed_checks.append(f"✅ {file_path} uses secure Redis helper")
            else:
                if 'redis://localhost' in content and 'get_secure_redis_url' not in content:
                    self.errors.append(f"❌ {file_path} has hardcoded redis://localhost without using helper")
                    return False
        
        return True
    
    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        logger.info("=" * 60)
        logger.info("🔒 Redis TLS Configuration Validator")
        logger.info("=" * 60)
        
        checks = [
            ("Environment Variables", self.validate_environment_variables),
            ("Helper Function", self.validate_helper_function),
            ("Production Code", self.validate_production_code)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            logger.info(f"\n📋 Running check: {check_name}")
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ Check failed with exception: {e}")
                self.errors.append(f"❌ {check_name} check failed: {e}")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 Validation Summary")
        logger.info("=" * 60)
        
        if self.passed_checks:
            logger.info("\n✅ Passed Checks:")
            for check in self.passed_checks:
                logger.info(f"  {check}")
        
        if self.warnings:
            logger.info("\n⚠️ Warnings:")
            for warning in self.warnings:
                logger.warning(f"  {warning}")
        
        if self.errors:
            logger.info("\n❌ Errors:")
            for error in self.errors:
                logger.error(f"  {error}")
        
        logger.info("\n" + "=" * 60)
        if self.errors:
            logger.error("❌ VALIDATION FAILED")
            logger.info("=" * 60)
            return False
        elif self.warnings:
            logger.warning("⚠️ VALIDATION PASSED WITH WARNINGS")
            logger.info("=" * 60)
            return True
        else:
            logger.info("✅ ALL CHECKS PASSED")
            logger.info("=" * 60)
            return True


def main():
    """Main entry point"""
    validator = RedisSecurityValidator()
    
    try:
        success = validator.run_all_checks()
        validator.print_summary()
        
        if success:
            logger.info("\n🎉 Redis TLS configuration is valid!")
            sys.exit(0)
        else:
            logger.error("\n💥 Redis TLS configuration validation failed!")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n💥 Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
