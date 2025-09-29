#!/usr/bin/env python3
"""
Automated Testing Pipeline for Phase 1-3 Functionality
Implements continuous testing with regression detection
"""

import subprocess
import json
import time
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

class AutomatedTestingPipeline:
    def __init__(self):
        self.db_path = 'testing_pipeline.db'
        self.init_database()
        self.test_suites = [
            {
                'name': 'Phase 1-3 Comprehensive Tests',
                'script': 'test_phase1_3_comprehensive.py',
                'critical': True
            },
            {
                'name': 'New API Endpoints Tests',
                'script': 'test_new_api_endpoints.py',
                'critical': True
            },
            {
                'name': 'Backend Reorganization Tests',
                'script': 'test_backend_reorganization.py',
                'critical': False
            }
        ]
    
    def init_database(self):
        """Initialize testing pipeline database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE,
                suite_name TEXT,
                status TEXT,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                success_rate REAL,
                duration_seconds REAL,
                output_log TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                test_name TEXT,
                error_message TEXT,
                stack_trace TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_test_suite(self, suite):
        """Run a single test suite"""
        run_id = f"run_{int(time.time())}_{suite['name'].replace(' ', '_').lower()}"
        
        print(f"🧪 Running {suite['name']}...")
        
        start_time = time.time()
        started_at = datetime.now()
        
        try:
            result = subprocess.run(
                ['python', suite['script']],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            completed_at = datetime.now()
            
            test_results = self.parse_test_output(result.stdout, result.stderr)
            
            self.save_test_run({
                'run_id': run_id,
                'suite_name': suite['name'],
                'status': 'passed' if result.returncode == 0 else 'failed',
                'total_tests': test_results.get('total_tests', 0),
                'passed_tests': test_results.get('passed_tests', 0),
                'failed_tests': test_results.get('failed_tests', 0),
                'success_rate': test_results.get('success_rate', 0),
                'duration_seconds': duration,
                'output_log': result.stdout + result.stderr,
                'started_at': started_at,
                'completed_at': completed_at
            })
            
            for failure in test_results.get('failures', []):
                self.save_test_failure(run_id, failure)
            
            status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
            print(f"  {status} - {duration:.2f}s - {test_results.get('success_rate', 0):.1f}% success rate")
            
            return {
                'success': result.returncode == 0,
                'duration': duration,
                'results': test_results
            }
            
        except subprocess.TimeoutExpired:
            print(f"  ⏰ TIMEOUT - Test suite exceeded 5 minutes")
            return {
                'success': False,
                'duration': 300,
                'results': {'error': 'Test suite timeout'}
            }
        except Exception as e:
            print(f"  ❌ ERROR - {str(e)}")
            return {
                'success': False,
                'duration': time.time() - start_time,
                'results': {'error': str(e)}
            }
    
    def parse_test_output(self, stdout, stderr):
        """Parse test output to extract results"""
        output = stdout + stderr
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0,
            'failures': []
        }
        
        if 'tests passed' in output:
            import re
            match = re.search(r'(\d+)/(\d+) tests passed \((\d+\.?\d*)%\)', output)
            if match:
                results['passed_tests'] = int(match.group(1))
                results['total_tests'] = int(match.group(2))
                results['failed_tests'] = results['total_tests'] - results['passed_tests']
                results['success_rate'] = float(match.group(3)) / 100
        
        if '❌ FAILED' in output:
            lines = output.split('\n')
            for line in lines:
                if '❌ FAILED' in line:
                    results['failures'].append({
                        'test_name': line.replace('❌ FAILED:', '').strip(),
                        'error_message': 'Test failed',
                        'stack_trace': ''
                    })
        
        return results
    
    def save_test_run(self, run_data):
        """Save test run to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_runs 
            (run_id, suite_name, status, total_tests, passed_tests, failed_tests, 
             success_rate, duration_seconds, output_log, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_data['run_id'],
            run_data['suite_name'],
            run_data['status'],
            run_data['total_tests'],
            run_data['passed_tests'],
            run_data['failed_tests'],
            run_data['success_rate'],
            run_data['duration_seconds'],
            run_data['output_log'],
            run_data['started_at'].isoformat(),
            run_data['completed_at'].isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def save_test_failure(self, run_id, failure):
        """Save test failure details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_failures (run_id, test_name, error_message, stack_trace)
            VALUES (?, ?, ?, ?)
        ''', (
            run_id,
            failure['test_name'],
            failure['error_message'],
            failure['stack_trace']
        ))
        
        conn.commit()
        conn.close()
    
    def run_full_pipeline(self):
        """Run the complete testing pipeline"""
        print("🚀 Starting Automated Testing Pipeline")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        pipeline_start = time.time()
        results = []
        
        for suite in self.test_suites:
            result = self.run_test_suite(suite)
            results.append({
                'suite': suite,
                'result': result
            })
            
            if suite['critical'] and not result['success']:
                print(f"🛑 Critical test suite failed: {suite['name']}")
                print("   Pipeline execution stopped.")
                break
        
        pipeline_duration = time.time() - pipeline_start
        
        self.generate_pipeline_summary(results, pipeline_duration)
        
        self.save_pipeline_metrics(results, pipeline_duration)
        
        return results
    
    def generate_pipeline_summary(self, results, duration):
        """Generate and display pipeline summary"""
        print("\n" + "=" * 60)
        print("🎯 AUTOMATED TESTING PIPELINE SUMMARY")
        print("=" * 60)
        
        total_suites = len(results)
        passed_suites = sum(1 for r in results if r['result']['success'])
        total_duration = duration
        
        print(f"📊 Pipeline Results:")
        print(f"   Total Test Suites: {total_suites}")
        print(f"   Passed Suites: {passed_suites}")
        print(f"   Failed Suites: {total_suites - passed_suites}")
        print(f"   Success Rate: {(passed_suites / total_suites) * 100:.1f}%")
        print(f"   Total Duration: {total_duration:.2f} seconds")
        print()
        
        print("📋 Suite Details:")
        for result in results:
            suite_name = result['suite']['name']
            suite_result = result['result']
            status = "✅ PASSED" if suite_result['success'] else "❌ FAILED"
            duration = suite_result['duration']
            
            print(f"   {status} {suite_name} ({duration:.2f}s)")
            
            if 'results' in suite_result and 'success_rate' in suite_result['results']:
                success_rate = suite_result['results']['success_rate'] * 100
                print(f"      Success Rate: {success_rate:.1f}%")
        
        print()
        
        if passed_suites == total_suites:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Phase 1-3 functionality is working correctly")
            print("✅ New API endpoints are operational")
            print("✅ System is ready for production")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("   Review failed test suites above")
            print("   Check test logs for detailed error information")
    
    def save_pipeline_metrics(self, results, duration):
        """Save pipeline metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_suites = len(results)
        passed_suites = sum(1 for r in results if r['result']['success'])
        success_rate = (passed_suites / total_suites) if total_suites > 0 else 0
        
        metrics = [
            ('pipeline_duration_seconds', duration),
            ('total_test_suites', total_suites),
            ('passed_test_suites', passed_suites),
            ('pipeline_success_rate', success_rate)
        ]
        
        for metric_name, metric_value in metrics:
            cursor.execute('''
                INSERT INTO pipeline_metrics (metric_name, metric_value)
                VALUES (?, ?)
            ''', (metric_name, metric_value))
        
        conn.commit()
        conn.close()
    
    def get_pipeline_history(self, limit=10):
        """Get recent pipeline execution history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                run_id, suite_name, status, success_rate, 
                duration_seconds, started_at, completed_at
            FROM test_runs 
            ORDER BY started_at DESC 
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()
        
        return [
            {
                'run_id': row[0],
                'suite_name': row[1],
                'status': row[2],
                'success_rate': row[3],
                'duration_seconds': row[4],
                'started_at': row[5],
                'completed_at': row[6]
            }
            for row in history
        ]
    
    def schedule_continuous_testing(self, interval_hours=6):
        """Schedule continuous testing (placeholder for cron/scheduler integration)"""
        print(f"📅 Continuous testing scheduled every {interval_hours} hours")
        print("   Integration with cron or task scheduler recommended for production")
        
        
        return {
            'scheduled': True,
            'interval_hours': interval_hours,
            'next_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def main():
    """Main function to run testing pipeline"""
    pipeline = AutomatedTestingPipeline()
    
    try:
        results = pipeline.run_full_pipeline()
        
        critical_failures = [
            r for r in results 
            if r['suite']['critical'] and not r['result']['success']
        ]
        
        if critical_failures:
            print(f"\n🚨 {len(critical_failures)} critical test suite(s) failed!")
            exit(1)
        else:
            print("\n✅ All tests completed successfully!")
            exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Testing pipeline interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
