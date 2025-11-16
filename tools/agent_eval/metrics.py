#!/usr/bin/env python3
"""
Agent Evaluation Metrics

Calculates performance metrics from evaluation results.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List


class MetricsCalculator:
    """Calculates agent performance metrics."""
    
    def __init__(self, results_path: str):
        self.results_path = Path(results_path)
        self.data = self.load_results()
    
    def load_results(self) -> Dict:
        """Load evaluation results from JSON file."""
        with open(self.results_path, 'r') as f:
            return json.load(f)
    
    def calculate_completion_rate(self) -> float:
        """Calculate task completion rate."""
        results = self.data['results']
        if not results:
            return 0.0
        
        completed = sum(1 for r in results if r['status'] == 'completed')
        return (completed / len(results)) * 100
    
    def calculate_correctness_rate(self) -> float:
        """Calculate correctness rate (of completed tasks)."""
        results = self.data['results']
        completed = [r for r in results if r['status'] == 'completed']
        
        if not completed:
            return 0.0
        
        correct = sum(1 for r in completed if r['ci_passed'] and r['correctness_score'] >= 0.8)
        return (correct / len(completed)) * 100
    
    def calculate_ci_pass_rate(self) -> float:
        """Calculate CI pass rate (of PRs created)."""
        results = self.data['results']
        prs_created = [r for r in results if r['pr_created']]
        
        if not prs_created:
            return 0.0
        
        ci_passed = sum(1 for r in prs_created if r['ci_passed'])
        return (ci_passed / len(prs_created)) * 100
    
    def calculate_time_efficiency(self) -> float:
        """Calculate time efficiency (actual vs estimated)."""
        results = self.data['results']
        completed = [r for r in results if r['status'] == 'completed' and r['duration_seconds']]
        
        if not completed:
            return 0.0
        
        efficiencies = []
        for r in completed:
            actual_minutes = r['duration_seconds'] / 60
            estimated_minutes = r['estimated_time_minutes']
            if estimated_minutes > 0:
                efficiency = (estimated_minutes / actual_minutes) * 100
                efficiencies.append(min(efficiency, 200))  # Cap at 200%
        
        return sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
    
    def calculate_overall_success_rate(self) -> float:
        """Calculate overall success rate (weighted combination)."""
        completion = self.calculate_completion_rate()
        correctness = self.calculate_correctness_rate()
        ci_pass = self.calculate_ci_pass_rate()
        time_eff = self.calculate_time_efficiency()
        
        overall = (
            completion * 0.3 +
            correctness * 0.4 +
            ci_pass * 0.2 +
            time_eff * 0.1
        )
        
        return overall
    
    def calculate_metrics_by_type(self) -> Dict[str, Dict]:
        """Calculate metrics broken down by task type."""
        results = self.data['results']
        types = {}
        
        for r in results:
            task_type = r['task_type']
            if task_type not in types:
                types[task_type] = []
            types[task_type].append(r)
        
        metrics_by_type = {}
        for task_type, type_results in types.items():
            completed = sum(1 for r in type_results if r['status'] == 'completed')
            pr_created = sum(1 for r in type_results if r['pr_created'])
            ci_passed = sum(1 for r in type_results if r['ci_passed'])
            
            metrics_by_type[task_type] = {
                "total": len(type_results),
                "completed": completed,
                "completion_rate": (completed / len(type_results)) * 100 if type_results else 0,
                "pr_created": pr_created,
                "ci_passed": ci_passed,
                "ci_pass_rate": (ci_passed / pr_created) * 100 if pr_created else 0
            }
        
        return metrics_by_type
    
    def calculate_metrics_by_difficulty(self) -> Dict[str, Dict]:
        """Calculate metrics broken down by difficulty."""
        results = self.data['results']
        difficulties = {}
        
        for r in results:
            difficulty = r['difficulty']
            if difficulty not in difficulties:
                difficulties[difficulty] = []
            difficulties[difficulty].append(r)
        
        metrics_by_difficulty = {}
        for difficulty, diff_results in difficulties.items():
            completed = sum(1 for r in diff_results if r['status'] == 'completed')
            pr_created = sum(1 for r in diff_results if r['pr_created'])
            ci_passed = sum(1 for r in diff_results if r['ci_passed'])
            
            metrics_by_difficulty[difficulty] = {
                "total": len(diff_results),
                "completed": completed,
                "completion_rate": (completed / len(diff_results)) * 100 if diff_results else 0,
                "pr_created": pr_created,
                "ci_passed": ci_passed,
                "ci_pass_rate": (ci_passed / pr_created) * 100 if pr_created else 0
            }
        
        return metrics_by_difficulty
    
    def print_metrics(self):
        """Print all metrics."""
        print("\n" + "="*60)
        print("AGENT PERFORMANCE METRICS")
        print("="*60)
        print(f"Evaluation Date: {self.data['evaluation_date']}")
        print(f"Total Tasks:     {self.data['total_tasks']}")
        print("="*60)
        
        print("\nOVERALL METRICS")
        print("-"*60)
        print(f"Task Completion Rate:    {self.calculate_completion_rate():.1f}%")
        print(f"Correctness Rate:        {self.calculate_correctness_rate():.1f}%")
        print(f"CI Pass Rate:            {self.calculate_ci_pass_rate():.1f}%")
        print(f"Time Efficiency:         {self.calculate_time_efficiency():.1f}%")
        print(f"Overall Success Rate:    {self.calculate_overall_success_rate():.1f}%")
        
        print("\nMETRICS BY TASK TYPE")
        print("-"*60)
        for task_type, metrics in self.calculate_metrics_by_type().items():
            print(f"\n{task_type.upper()}:")
            print(f"  Total:           {metrics['total']}")
            print(f"  Completed:       {metrics['completed']} ({metrics['completion_rate']:.1f}%)")
            print(f"  PRs Created:     {metrics['pr_created']}")
            print(f"  CI Passed:       {metrics['ci_passed']} ({metrics['ci_pass_rate']:.1f}%)")
        
        print("\nMETRICS BY DIFFICULTY")
        print("-"*60)
        for difficulty, metrics in self.calculate_metrics_by_difficulty().items():
            print(f"\n{difficulty.upper()}:")
            print(f"  Total:           {metrics['total']}")
            print(f"  Completed:       {metrics['completed']} ({metrics['completion_rate']:.1f}%)")
            print(f"  PRs Created:     {metrics['pr_created']}")
            print(f"  CI Passed:       {metrics['ci_passed']} ({metrics['ci_pass_rate']:.1f}%)")
        
        print("\n" + "="*60)
        
        if self.data['results'] and self.data['results'][0]['status'] == 'not_implemented':
            print("\n⚠️  NOTE: These are placeholder metrics.")
            print("   Evaluation harness not yet integrated with agent orchestrator.")
            print("   See tools/agent_eval/README.md for integration steps.")


def main():
    parser = argparse.ArgumentParser(description="Calculate agent evaluation metrics")
    parser.add_argument(
        "--results",
        default="results/latest.json",
        help="Path to results file (default: results/latest.json)"
    )
    
    args = parser.parse_args()
    
    calculator = MetricsCalculator(args.results)
    calculator.print_metrics()


if __name__ == "__main__":
    main()
