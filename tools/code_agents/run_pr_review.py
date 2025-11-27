#!/usr/bin/env python3
"""
PR Review CLI - Phase 2 Step A

Command-line tool for automated code review using ReviewerAgent.

Features:
- Review files from a PR or local paths
- Multiple output formats (text, json)
- Integration with CI/CD pipelines
- Exit codes for pass/fail status

Usage:
    # Review specific files
    python run_pr_review.py --files src/app.py src/utils.py
    
    # Review with JSON output
    python run_pr_review.py --files src/app.py --format json
    
    # Strict mode (fail on warnings)
    python run_pr_review.py --files src/app.py --strict
    
    # Review PR (future feature)
    python run_pr_review.py --pr 1234

Exit Codes:
    0: Review passed (no errors, or only warnings in non-strict mode)
    1: Review failed (errors found, or warnings in strict mode)
    2: Tool error (invalid arguments, missing dependencies, etc.)
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Automated code review using ReviewerAgent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review specific files
  %(prog)s --files src/app.py src/utils.py
  
  # Review with JSON output
  %(prog)s --files src/app.py --format json
  
  # Strict mode (fail on warnings)
  %(prog)s --files src/app.py --strict
  
  # Review PR (future feature)
  %(prog)s --pr 1234

Exit Codes:
  0: Review passed
  1: Review failed
  2: Tool error
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--files",
        nargs="+",
        help="File paths to review (space-separated)"
    )
    input_group.add_argument(
        "--pr",
        type=int,
        help="PR number to review (future feature)"
    )
    
    # Output options
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    # Review options
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)"
    )
    
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory (default: current directory)"
    )
    
    # Logging options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential output"
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool, quiet: bool):
    """
    Configure logging based on verbosity flags
    
    Args:
        verbose: Enable verbose logging
        quiet: Suppress non-essential output
    """
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


def validate_files(file_paths: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate that files exist and are readable
    
    Args:
        file_paths: List of file paths to validate
        
    Returns:
        Tuple of (valid_files, invalid_files)
    """
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            invalid_files.append(f"{file_path} (not found)")
        elif not os.path.isfile(file_path):
            invalid_files.append(f"{file_path} (not a file)")
        elif not os.access(file_path, os.R_OK):
            invalid_files.append(f"{file_path} (not readable)")
        else:
            valid_files.append(file_path)
    
    return valid_files, invalid_files


def review_files(
    file_paths: List[str],
    repo_root: str,
    strict: bool
) -> tuple[bool, dict]:
    """
    Review files using ReviewerAgent
    
    Args:
        file_paths: List of file paths to review
        repo_root: Repository root directory
        strict: Fail on warnings (not just errors)
        
    Returns:
        Tuple of (passed, result_dict)
    """
    try:
        from agents.reviewer_agent.reviewer_agent import ReviewerAgent
    except ImportError as e:
        logger.error(f"Failed to import ReviewerAgent: {e}")
        logger.error("Make sure you're running from the project root")
        return False, {
            "error": f"Failed to import ReviewerAgent: {e}",
            "passed": False
        }
    
    try:
        # Initialize ReviewerAgent
        agent = ReviewerAgent(repo_root=repo_root)
        logger.info(f"Reviewing {len(file_paths)} files...")
        
        # Review files
        result = agent.review_files(file_paths)
        
        # Determine pass/fail
        if strict:
            # In strict mode, fail on any warnings or errors
            passed = result.summary.get("warning", 0) == 0 and result.summary.get("error", 0) == 0
        else:
            # In normal mode, only fail on errors
            passed = result.passed
        
        # Convert result to dict
        result_dict = {
            "passed": passed,
            "summary": result.summary,
            "comments": [
                {
                    "file_path": comment.file_path,
                    "line_number": comment.line_number,
                    "severity": comment.severity,
                    "category": comment.category,
                    "message": comment.message,
                    "suggestion": comment.suggestion,
                    "code_snippet": comment.code_snippet
                }
                for comment in result.comments
            ]
        }
        
        return passed, result_dict
        
    except Exception as e:
        logger.error(f"Review failed: {e}", exc_info=True)
        return False, {
            "error": str(e),
            "passed": False
        }


def format_text_output(result: dict, strict: bool) -> str:
    """
    Format result as human-readable text
    
    Args:
        result: Review result dict
        strict: Whether strict mode was enabled
        
    Returns:
        Formatted text output
    """
    lines = []
    
    lines.append("=" * 80)
    lines.append("CODE REVIEW RESULTS")
    lines.append("=" * 80)
    
    if "error" in result:
        lines.append(f"ERROR: {result['error']}")
        return "\n".join(lines)
    
    # Status
    status = "✓ PASSED" if result["passed"] else "✗ FAILED"
    lines.append(f"Status: {status}")
    
    if strict:
        lines.append("Mode: STRICT (warnings treated as errors)")
    
    # Summary
    summary = result["summary"]
    lines.append(f"\nTotal Comments: {summary['total']}")
    lines.append(f"  Errors: {summary['error']}")
    lines.append(f"  Warnings: {summary['warning']}")
    lines.append(f"  Info: {summary['info']}")
    
    lines.append(f"\nBy Category:")
    lines.append(f"  Lint: {summary['lint']}")
    lines.append(f"  Security: {summary['security']}")
    lines.append(f"  Accessibility: {summary['accessibility']}")
    lines.append(f"  Style: {summary['style']}")
    
    # Detailed comments
    if result["comments"]:
        lines.append("\n" + "=" * 80)
        lines.append("DETAILED COMMENTS:")
        lines.append("-" * 80)
        
        # Group by file
        by_file = {}
        for comment in result["comments"]:
            file_path = comment["file_path"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(comment)
        
        for file_path, comments in by_file.items():
            lines.append(f"\n{file_path}:")
            
            for comment in comments:
                severity_icon = {
                    'error': '✗',
                    'warning': '⚠',
                    'info': 'ℹ'
                }.get(comment["severity"], '•')
                
                line_info = f":{comment['line_number']}" if comment["line_number"] else ""
                lines.append(f"  {severity_icon} [{comment['category'].upper()}]{line_info}")
                lines.append(f"    {comment['message']}")
                
                if comment["suggestion"]:
                    lines.append(f"    💡 Suggestion: {comment['suggestion']}")
                
                if comment["code_snippet"]:
                    lines.append(f"    Code: {comment['code_snippet']}")
                
                lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


def format_json_output(result: dict) -> str:
    """
    Format result as JSON
    
    Args:
        result: Review result dict
        
    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)


def main() -> int:
    """
    Main entry point
    
    Returns:
        Exit code (0=success, 1=review failed, 2=tool error)
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging(args.verbose, args.quiet)
        
        # Handle PR review (future feature)
        if args.pr:
            logger.error("PR review is not yet implemented (Phase 2 Step B)")
            logger.error("Please use --files to review specific files")
            return 2
        
        # Validate files
        valid_files, invalid_files = validate_files(args.files)
        
        if invalid_files:
            logger.error("Invalid files:")
            for invalid_file in invalid_files:
                logger.error(f"  - {invalid_file}")
            return 2
        
        if not valid_files:
            logger.error("No valid files to review")
            return 2
        
        # Review files
        passed, result = review_files(
            file_paths=valid_files,
            repo_root=args.repo_root,
            strict=args.strict
        )
        
        # Format output
        if args.format == "json":
            output = format_json_output(result)
        else:
            output = format_text_output(result, args.strict)
        
        # Print output
        print(output)
        
        # Return exit code
        if "error" in result:
            return 2
        elif passed:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
