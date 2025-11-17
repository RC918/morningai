#!/usr/bin/env python3
"""
Agent Evaluation Runner

Runs evaluation tasks against the AI agent and measures performance metrics.
"""

import json
import argparse
import time
import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from orchestrator_client import OrchestratorClient, MockOrchestratorClient
from github_client import GitHubClient, MockGitHubClient


class EvaluationRunner:
    """Runs evaluation tasks and collects results."""
    
    def __init__(
        self,
        dataset_path: str,
        output_path: str,
        redis_url: Optional[str] = None,
        github_token: Optional[str] = None,
        use_mock: bool = False
    ):
        self.dataset_path = Path(dataset_path)
        self.output_path = Path(output_path)
        self.results = []
        self.use_mock = use_mock
        
        if use_mock:
            self.orchestrator = MockOrchestratorClient()
            print("⚠️  Using mock orchestrator (no real task execution)")
        else:
            redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            try:
                self.orchestrator = OrchestratorClient(redis_url)
                print(f"✅ Connected to orchestrator via Redis")
            except Exception as e:
                print(f"⚠️  Failed to connect to orchestrator: {e}")
                print("   Falling back to mock mode")
                self.orchestrator = MockOrchestratorClient()
                self.use_mock = True
        
        if use_mock:
            self.github = MockGitHubClient()
        else:
            try:
                self.github = GitHubClient(github_token)
                print(f"✅ GitHub client initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize GitHub client: {e}")
                print("   Falling back to mock GitHub client")
                self.github = MockGitHubClient()
    
    def load_dataset(self) -> List[Dict]:
        """Load test cases from JSONL file."""
        tasks = []
        with open(self.dataset_path, 'r') as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        
        self._validate_dataset(tasks)
        return tasks
    
    def _validate_dataset(self, tasks: List[Dict]):
        """Validate that all affected_files exist and contain no wildcards."""
        errors = []
        warnings = []
        
        repo_root = Path(__file__).parent.parent.parent
        
        for task in tasks:
            task_id = task.get('id', 'unknown')
            task_type = task.get('type', 'unknown')
            affected_files = task.get('input', {}).get('affected_files', [])
            
            for file_path in affected_files:
                if re.search(r'[*?\\[\\]]', file_path):
                    errors.append(f"Task {task_id}: File path contains wildcards: {file_path}")
                    continue
                
                full_path = repo_root / file_path
                if not full_path.exists():
                    if task_type in ['feature', 'test']:
                        warnings.append(f"Task {task_id}: File does not exist (will be created): {file_path}")
                    else:
                        errors.append(f"Task {task_id}: File does not exist: {file_path}")
        
        if warnings:
            print(f"⚠️  Dataset validation warnings ({len(warnings)} files will be created by tasks)")
        
        if errors:
            error_msg = "Dataset validation failed:\n" + "\n".join(errors)
            raise ValueError(error_msg)
    
    def run_task(self, task: Dict) -> Dict:
        """
        Run a single evaluation task.
        
        1. Submit task to the agent orchestrator
        2. Monitor execution
        3. Collect results (PR URL, CI status, etc.)
        4. Evaluate against expected outcomes
        """
        print(f"Running task {task['id']}: {task['description']}")
        
        start_time = time.time()
        task_id = task["id"]
        description = task["description"]
        repo = task["input"].get("repo", "RC918/morningai")
        
        result = {
            "task_id": task_id,
            "task_type": task["type"],
            "description": description,
            "difficulty": task["difficulty"],
            "estimated_time_minutes": task["estimated_time_minutes"],
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "status": "failed",
            "pr_created": False,
            "pr_url": None,
            "ci_passed": False,
            "correctness_score": 0.0,
            "correctness_criteria_met": [],
            "errors": [],
            "notes": "",
            "orchestrator_mode": "mock" if self.use_mock else "real"
        }
        
        try:
            # Submit task to orchestrator
            submitted = self.orchestrator.submit_task(
                task_id=task_id,
                description=description,
                repo=repo,
                timeout=600
            )
            
            if not submitted:
                result["errors"].append("Failed to submit task to orchestrator")
                result["status"] = "failed"
                return result
            
            success, task_result = self.orchestrator.wait_for_completion(
                task_id=task_id,
                timeout=600,
                poll_interval=10
            )
            
            if not success:
                result["errors"].append(task_result.get("error", "Task failed or timed out"))
                result["status"] = "failed"
                return result
            
            result["status"] = "completed"
            result["pr_url"] = task_result.get("pr_url", "")
            result["pr_created"] = bool(result["pr_url"])
            
            if result["pr_url"]:
                ci_status = self.github.check_pr_ci_status(result["pr_url"])
                result["ci_passed"] = ci_status["ci_passed"]
                result["ci_checks_total"] = ci_status["total_checks"]
                result["ci_checks_passed"] = ci_status["passed_checks"]
                result["ci_checks_failed"] = ci_status["failed_checks"]
                result["ci_checks_pending"] = ci_status["pending_checks"]
                result["ci_check_details"] = ci_status["check_details"]
                
                if ci_status["error"]:
                    result["notes"] += f" CI check warning: {ci_status['error']}"
            else:
                ci_state = task_result.get("ci_state", "unknown")
                result["ci_passed"] = ci_state == "success"
            
            expected = task.get("expected_outcome", {})
            criteria_met = []
            
            if expected.get("pr_created") == result["pr_created"]:
                criteria_met.append("pr_created")
            
            if expected.get("ci_passed") == result["ci_passed"]:
                criteria_met.append("ci_passed")
            
            result["correctness_criteria_met"] = criteria_met
            
            expected_criteria = expected.get("correctness_criteria", [])
            if expected_criteria:
                if result["pr_created"] and result["ci_passed"]:
                    result["correctness_score"] = 0.9
                elif result["pr_created"]:
                    result["correctness_score"] = 0.5
                else:
                    result["correctness_score"] = 0.1
            else:
                result["correctness_score"] = 0.0
            
            result["notes"] = f"Task executed via {'mock' if self.use_mock else 'real'} orchestrator"
            
        except Exception as e:
            result["errors"].append(f"Exception during task execution: {str(e)}")
            result["status"] = "error"
            result["notes"] = f"Unexpected error: {str(e)}"
        
        finally:
            end_time = time.time()
            result["end_time"] = datetime.utcnow().isoformat()
            result["duration_seconds"] = end_time - start_time
            
            try:
                self.orchestrator.cleanup_task(task_id)
            except:
                pass
        
        return result
    
    def run_evaluation(self, max_tasks: Optional[int] = None, task_id: Optional[str] = None):
        """Run evaluation on all tasks or specific task."""
        tasks = self.load_dataset()
        
        if task_id:
            tasks = [t for t in tasks if t['id'] == task_id]
            if not tasks:
                raise ValueError(f"Task {task_id} not found in dataset")
        
        if max_tasks:
            tasks = tasks[:max_tasks]
        
        print(f"Running evaluation on {len(tasks)} tasks...")
        
        for task in tasks:
            result = self.run_task(task)
            self.results.append(result)
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            "evaluation_date": datetime.utcnow().isoformat(),
            "dataset": str(self.dataset_path),
            "total_tasks": len(self.results),
            "results": self.results
        }
        
        with open(self.output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {self.output_path}")
    
    def print_summary(self):
        """Print evaluation summary."""
        total = len(self.results)
        completed = sum(1 for r in self.results if r['status'] == 'completed')
        pr_created = sum(1 for r in self.results if r['pr_created'])
        ci_passed = sum(1 for r in self.results if r['ci_passed'])
        
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Total tasks:        {total}")
        print(f"Completed:          {completed} ({completed/total*100:.1f}%)")
        print(f"PRs created:        {pr_created} ({pr_created/total*100:.1f}%)")
        print(f"CI passed:          {ci_passed} ({ci_passed/total*100:.1f}%)")
        print("="*60)
        
        if self.results and self.results[0].get('orchestrator_mode') == 'mock':
            print("\n⚠️  NOTE: Evaluation ran in mock mode (no real orchestrator execution).")
            print("   Set REDIS_URL environment variable to connect to real orchestrator.")


def main():
    parser = argparse.ArgumentParser(description="Run agent evaluation")
    parser.add_argument(
        "--dataset",
        default="dataset.jsonl",
        help="Path to dataset file (default: dataset.jsonl)"
    )
    parser.add_argument(
        "--output",
        default="results/latest.json",
        help="Path to output file (default: results/latest.json)"
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        help="Maximum number of tasks to run (default: all)"
    )
    parser.add_argument(
        "--task-id",
        help="Run specific task by ID"
    )
    parser.add_argument(
        "--redis-url",
        help="Redis URL for orchestrator connection (default: from REDIS_URL env)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock orchestrator (no real task execution)"
    )
    parser.add_argument(
        "--github-token",
        help="GitHub personal access token (default: from GITHUB_TOKEN env)"
    )
    
    args = parser.parse_args()
    
    runner = EvaluationRunner(
        args.dataset,
        args.output,
        redis_url=args.redis_url,
        github_token=args.github_token,
        use_mock=args.mock
    )
    runner.run_evaluation(max_tasks=args.max_tasks, task_id=args.task_id)


if __name__ == "__main__":
    main()
