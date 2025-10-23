#!/usr/bin/env python3
"""
Redis TTL cleanup script for cost tracking keys

This script adds TTL (Time To Live) to Redis keys used for cost tracking
to prevent unlimited accumulation of keys.

Default TTLs:
- Daily cost keys: 30 days
- Hourly cost keys: 7 days
- Task cost keys: 3 days

Usage:
    python scripts/cleanup_redis_cost_keys.py [--dry-run] [--verbose]
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'handoff/20250928/40_App/orchestrator'))

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  redis package not available. Install with: pip install redis")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisCostKeyCleaner:
    """Cleanup Redis cost tracking keys with TTL"""
    
    DEFAULT_TTLS = {
        'daily': 30 * 24 * 3600,   # 30 days
        'hourly': 7 * 24 * 3600,    # 7 days
        'task': 3 * 24 * 3600       # 3 days
    }
    
    def __init__(self, redis_url=None, dry_run=False):
        self.dry_run = dry_run
        
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not available")
        
        redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info(f"Connected to Redis: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def scan_cost_keys(self, pattern='cost:*'):
        """Scan for cost tracking keys"""
        keys = []
        cursor = 0
        
        while True:
            cursor, batch = self.redis_client.scan(cursor, match=pattern, count=100)
            keys.extend([k.decode('utf-8') if isinstance(k, bytes) else k for k in batch])
            
            if cursor == 0:
                break
        
        logger.info(f"Found {len(keys)} cost tracking keys")
        return keys
    
    def get_key_period(self, key):
        """Determine the period type from key name"""
        if ':daily:' in key:
            return 'daily'
        elif ':hourly:' in key:
            return 'hourly'
        elif ':task:' in key:
            return 'task'
        else:
            return None
    
    def set_ttl(self, key, ttl_seconds):
        """Set TTL for a key"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would set TTL {ttl_seconds}s for key: {key}")
            return True
        
        try:
            self.redis_client.expire(key, ttl_seconds)
            logger.debug(f"Set TTL {ttl_seconds}s for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set TTL for key {key}: {e}")
            return False
    
    def cleanup_keys(self):
        """Cleanup all cost tracking keys"""
        keys = self.scan_cost_keys()
        
        stats = {
            'total': len(keys),
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'by_period': {'daily': 0, 'hourly': 0, 'task': 0, 'unknown': 0}
        }
        
        for key in keys:
            period = self.get_key_period(key)
            
            if period is None:
                logger.warning(f"Unknown period for key: {key}")
                stats['skipped'] += 1
                stats['by_period']['unknown'] += 1
                continue
            
            ttl = self.DEFAULT_TTLS.get(period)
            if ttl is None:
                logger.warning(f"No TTL configured for period: {period}")
                stats['skipped'] += 1
                continue
            
            current_ttl = self.redis_client.ttl(key)
            
            if current_ttl == -1:
                if self.set_ttl(key, ttl):
                    stats['updated'] += 1
                    stats['by_period'][period] += 1
                else:
                    stats['errors'] += 1
            else:
                logger.debug(f"Key {key} already has TTL: {current_ttl}s")
                stats['skipped'] += 1
        
        return stats
    
    def get_statistics(self):
        """Get statistics about cost tracking keys"""
        keys = self.scan_cost_keys()
        
        stats = {
            'total_keys': len(keys),
            'keys_with_ttl': 0,
            'keys_without_ttl': 0,
            'by_period': {'daily': 0, 'hourly': 0, 'task': 0, 'unknown': 0},
            'total_memory_bytes': 0
        }
        
        for key in keys:
            period = self.get_key_period(key)
            if period:
                stats['by_period'][period] += 1
            else:
                stats['by_period']['unknown'] += 1
            
            ttl = self.redis_client.ttl(key)
            if ttl == -1:
                stats['keys_without_ttl'] += 1
            else:
                stats['keys_with_ttl'] += 1
            
            try:
                memory = self.redis_client.memory_usage(key)
                if memory:
                    stats['total_memory_bytes'] += memory
            except Exception:
                pass
        
        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup Redis cost tracking keys with TTL'
    )
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--redis-url', help='Redis connection URL (default: from REDIS_URL env var)')
    parser.add_argument('--stats-only', action='store_true', help='Only show statistics without cleanup')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not REDIS_AVAILABLE:
        print("❌ redis package not available. Install with: pip install redis")
        sys.exit(1)
    
    try:
        cleaner = RedisCostKeyCleaner(redis_url=args.redis_url, dry_run=args.dry_run)
        
        if args.stats_only:
            print("📊 Cost Tracking Keys Statistics")
            print("=" * 50)
            stats = cleaner.get_statistics()
            print(f"Total keys: {stats['total_keys']}")
            print(f"Keys with TTL: {stats['keys_with_ttl']}")
            print(f"Keys without TTL: {stats['keys_without_ttl']}")
            print(f"\nBy period:")
            for period, count in stats['by_period'].items():
                print(f"  {period}: {count}")
            print(f"\nTotal memory: {stats['total_memory_bytes'] / 1024:.2f} KB")
        else:
            print("🧹 Cleaning up Redis cost tracking keys...")
            if args.dry_run:
                print("⚠️  DRY RUN MODE - No changes will be made")
            print()
            
            stats = cleaner.cleanup_keys()
            
            print("\n✅ Cleanup completed!")
            print("=" * 50)
            print(f"Total keys scanned: {stats['total']}")
            print(f"Keys updated: {stats['updated']}")
            print(f"Keys skipped: {stats['skipped']}")
            print(f"Errors: {stats['errors']}")
            print(f"\nUpdated by period:")
            for period, count in stats['by_period'].items():
                if count > 0:
                    ttl_days = RedisCostKeyCleaner.DEFAULT_TTLS.get(period, 0) / 86400
                    print(f"  {period}: {count} keys (TTL: {ttl_days:.0f} days)")
            
            if args.dry_run:
                print("\n⚠️  This was a dry run. Run without --dry-run to apply changes.")
    
    except Exception as e:
        logger.exception("Cleanup failed")
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
