#!/usr/bin/env python3
"""
Deployment Verification Script

Verifies that all required environment variables and paths are correctly configured
before deploying to production.

Usage:
    python scripts/verify_deployment.py
    
Exit codes:
    0: All checks passed
    1: One or more checks failed
"""
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class DeploymentVerifier:
    """Verify deployment configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def check_redis_url(self):
        """Verify REDIS_URL is set"""
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            self.errors.append("REDIS_URL environment variable is not set")
            logger.error("❌ REDIS_URL not set - backend will fail to start")
            return False
        
        if redis_url.startswith('redis://localhost'):
            self.warnings.append("REDIS_URL points to localhost - this will fail in production")
            logger.warning("⚠️  REDIS_URL points to localhost")
        else:
            logger.info(f"✅ REDIS_URL is set: {redis_url.split('@')[-1] if '@' in redis_url else redis_url.split('//')[1].split('/')[0]}")
        
        return True
    
    def check_orchestrator_path(self):
        """Verify orchestrator path exists"""
        orchestrator_path = os.getenv('ORCHESTRATOR_PATH')
        
        if not orchestrator_path:
            script_dir = Path(__file__).parent.parent
            orchestrator_path = script_dir / '..' / 'orchestrator'
            logger.info(f"ORCHESTRATOR_PATH not set, using fallback: {orchestrator_path}")
        
        if not Path(orchestrator_path).exists():
            self.errors.append(f"Orchestrator path does not exist: {orchestrator_path}")
            logger.error(f"❌ Orchestrator path not found: {orchestrator_path}")
            return False
        
        logger.info(f"✅ Orchestrator path exists: {orchestrator_path}")
        return True
    
    def check_database_url(self):
        """Verify DATABASE_URL is set"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.errors.append("DATABASE_URL environment variable is not set")
            logger.error("❌ DATABASE_URL not set")
            return False
        
        logger.info("✅ DATABASE_URL is set")
        return True
    
    def check_sentry_dsn(self):
        """Verify SENTRY_DSN is set (optional but recommended)"""
        sentry_dsn = os.getenv('SENTRY_DSN')
        if not sentry_dsn:
            self.warnings.append("SENTRY_DSN not set - error tracking will be disabled")
            logger.warning("⚠️  SENTRY_DSN not set - error tracking disabled")
            return False
        
        logger.info("✅ SENTRY_DSN is set")
        return True
    
    def check_jwt_secret(self):
        """Verify JWT_SECRET_KEY is set"""
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not jwt_secret:
            self.errors.append("JWT_SECRET_KEY environment variable is not set")
            logger.error("❌ JWT_SECRET_KEY not set")
            return False
        
        if len(jwt_secret) < 32:
            self.warnings.append("JWT_SECRET_KEY is too short (should be at least 32 characters)")
            logger.warning("⚠️  JWT_SECRET_KEY is too short")
        
        logger.info("✅ JWT_SECRET_KEY is set")
        return True
    
    def run_all_checks(self):
        """Run all verification checks"""
        logger.info("=" * 60)
        logger.info("Starting deployment verification...")
        logger.info("=" * 60)
        
        checks = [
            ("Redis Configuration", self.check_redis_url),
            ("Orchestrator Path", self.check_orchestrator_path),
            ("Database Configuration", self.check_database_url),
            ("Sentry Configuration", self.check_sentry_dsn),
            ("JWT Secret", self.check_jwt_secret),
        ]
        
        for check_name, check_func in checks:
            logger.info(f"\nChecking: {check_name}")
            check_func()
        
        logger.info("\n" + "=" * 60)
        logger.info("Verification Summary")
        logger.info("=" * 60)
        
        if self.errors:
            logger.error(f"\n❌ {len(self.errors)} ERROR(S) FOUND:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning(f"\n⚠️  {len(self.warnings)} WARNING(S):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            logger.info("\n✅ All checks passed! Ready for deployment.")
            return 0
        elif not self.errors:
            logger.info("\n✅ All critical checks passed. Review warnings before deploying.")
            return 0
        else:
            logger.error("\n❌ Deployment verification FAILED. Fix errors before deploying.")
            return 1


def main():
    """Main entry point"""
    verifier = DeploymentVerifier()
    exit_code = verifier.run_all_checks()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
