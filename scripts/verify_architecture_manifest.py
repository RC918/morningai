#!/usr/bin/env python3
"""
Architecture Manifest Verification Script

This script validates:
1. All paths in architecture-manifest.yaml exist in the repository
2. Documentation files don't use invalid path aliases (hallucinations)
3. External links use HTTPS
4. External links are not broken (optional, with --check-links flag)

Usage:
    python scripts/verify_architecture_manifest.py [--check-links] [--verbose]

Exit codes:
    0 - All checks passed
    1 - Validation errors found
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)


# =============================================================================
# Link Security Check Patterns (exported for testing)
# =============================================================================

# Pattern matches http:// followed by a domain (not localhost/127.0.0.1/0.0.0.0)
HTTP_INSECURE_LINK_PATTERN = r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+'
HTTP_INSECURE_LINK_RE = re.compile(HTTP_INSECURE_LINK_PATTERN)

# Patterns to exclude (code examples, internal services, formatting examples)
# Note: Using lookahead to ensure we match the exact domain, not just a prefix
# (e.g., http://example.com.evil.com should NOT be excluded)
# The lookahead includes common URL delimiters and trailing punctuation in docs
EXCLUDED_HTTP_PATTERNS = (
    r"http://example\.com(?=[/:?#'\")\]>]|$)",  # Example URLs in code (exact domain)
    r"http://mcp-server(?=[/:?#'\")\]>]|$)",    # Internal MCP server (exact hostname)
    r'http://`',                                 # Protocol mismatch formatting examples
    r'http://\$',                                # Variable URLs in code examples
)
EXCLUDED_HTTP_PATTERN_RE = re.compile('|'.join(EXCLUDED_HTTP_PATTERNS))


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'


class ManifestVerifier:
    def __init__(self, repo_root: Path, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.checks_passed = 0

    def log_pass(self, message: str) -> None:
        self.checks_passed += 1
        print(f"{Colors.GREEN}✓{Colors.NC} {message}")

    def log_fail(self, message: str) -> None:
        self.errors.append(message)
        print(f"{Colors.RED}✗{Colors.NC} {message}")

    def log_warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")

    def log_verbose(self, message: str) -> None:
        if self.verbose:
            print(f"  → {message}")

    def load_manifest(self) -> Optional[dict]:
        manifest_path = self.repo_root / "config" / "architecture-manifest.yaml"
        if not manifest_path.exists():
            self.log_fail(f"Architecture manifest not found: {manifest_path}")
            return None

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.log_fail(f"Failed to parse architecture manifest: {e}")
            return None

    def verify_required_paths(self, manifest: dict) -> None:
        print("\n1. Verifying required paths from manifest...")

        key_paths = manifest.get("key_paths", {})
        required_paths = key_paths.get("required", [])

        for path in required_paths:
            full_path = self.repo_root / path
            if full_path.exists():
                self.log_pass(f"Path exists: {path}")
            else:
                self.log_fail(f"Required path does not exist: {path}")

    def verify_service_paths(self, manifest: dict) -> None:
        print("\n2. Verifying service paths and entrypoints...")

        services = manifest.get("services", {})

        for service_id, service in services.items():
            service_path = service.get("path")
            if service_path:
                full_path = self.repo_root / service_path
                if full_path.exists():
                    self.log_pass(f"Service '{service_id}' path exists: {service_path}")
                else:
                    self.log_fail(f"Service '{service_id}' path does not exist: {service_path}")

            entrypoint = service.get("entrypoint")
            if entrypoint and service_path:
                entrypoint_path = self.repo_root / service_path / entrypoint
                if entrypoint_path.exists():
                    self.log_pass(f"Service '{service_id}' entrypoint exists: {entrypoint}")
                else:
                    self.log_fail(f"Service '{service_id}' entrypoint does not exist: {service_path}/{entrypoint}")

            package_json = service.get("package_json")
            if package_json:
                package_path = self.repo_root / package_json
                if package_path.exists():
                    self.log_pass(f"Service '{service_id}' package.json exists")
                else:
                    self.log_fail(f"Service '{service_id}' package.json does not exist: {package_json}")

            requirements = service.get("requirements")
            if requirements:
                req_path = self.repo_root / requirements
                if req_path.exists():
                    self.log_pass(f"Service '{service_id}' requirements.txt exists")
                else:
                    self.log_fail(f"Service '{service_id}' requirements.txt does not exist: {requirements}")

    def check_docs_for_invalid_aliases(self, manifest: dict) -> None:
        print("\n3. Checking documentation for invalid path aliases (hallucinations)...")

        key_paths = manifest.get("key_paths", {})
        invalid_aliases = key_paths.get("invalid_aliases", [])

        if not invalid_aliases:
            self.log_warn("No invalid aliases defined in manifest")
            return

        docs_dir = self.repo_root / "docs"
        if not docs_dir.exists():
            self.log_warn("docs/ directory not found")
            return

        alias_patterns = []
        for alias in invalid_aliases:
            path = alias.get("path", "")
            correct = alias.get("correct", "")
            escaped_path = re.escape(path)
            alias_patterns.append((path, correct, re.compile(rf'(?:^|[`"\'\s/])({escaped_path})(?:[`"\'\s/]|$)', re.MULTILINE)))

        files_checked = 0
        issues_found = 0

        for md_file in docs_dir.rglob("*.md"):
            files_checked += 1
            try:
                content = md_file.read_text(encoding='utf-8')
                relative_path = md_file.relative_to(self.repo_root)

                for alias_path, correct_path, pattern in alias_patterns:
                    matches = pattern.findall(content)
                    if matches:
                        issues_found += 1
                        self.log_fail(
                            f"Invalid path alias '{alias_path}' found in {relative_path} "
                            f"(should be '{correct_path}')"
                        )
                        self.log_verbose(f"Found {len(matches)} occurrence(s)")
            except Exception as e:
                self.log_warn(f"Could not read {md_file}: {e}")

        if issues_found == 0:
            self.log_pass(f"No invalid path aliases found in {files_checked} documentation files")

    def check_link_security(self, manifest: dict) -> None:
        print("\n4. Checking documentation for insecure (HTTP) links...")

        docs_dir = self.repo_root / "docs"
        if not docs_dir.exists():
            self.log_warn("docs/ directory not found")
            return

        files_checked = 0
        insecure_links = []

        for md_file in docs_dir.rglob("*.md"):
            files_checked += 1
            try:
                content = md_file.read_text(encoding='utf-8')
                relative_path = md_file.relative_to(self.repo_root)

                matches = HTTP_INSECURE_LINK_RE.findall(content)
                for match in matches:
                    # Skip excluded patterns (code examples, internal services)
                    if EXCLUDED_HTTP_PATTERN_RE.search(match):
                        continue
                    insecure_links.append((relative_path, match))
            except Exception as e:
                self.log_warn(f"Could not read {md_file}: {e}")

        if insecure_links:
            for file_path, link in insecure_links:
                self.log_fail(f"Insecure HTTP link in {file_path}: {link}")
        else:
            self.log_pass(f"No insecure HTTP links found in {files_checked} documentation files")

    def check_link_freshness(self, check_links: bool = False) -> None:
        print("\n5. Checking link freshness...")

        if not check_links:
            self.log_warn("Link freshness check skipped (use --check-links to enable)")
            return

        try:
            import requests
        except ImportError:
            self.log_warn("requests library not available, skipping link freshness check")
            return

        docs_dir = self.repo_root / "docs"
        if not docs_dir.exists():
            self.log_warn("docs/ directory not found")
            return

        url_pattern = re.compile(r'https?://[^\s\)>\]"\']+')

        excluded_domains = [
            'localhost',
            '127.0.0.1',
            'vercel.app',
            'render.com',
            'supabase.co',
            'upstash.io',
            'sentry.io',
            'github.com/RC918/morningai/pull',
            'github.com/RC918/morningai/issues',
            'app.devin.ai',
        ]

        urls_checked = set()
        broken_links = []

        for md_file in docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                relative_path = md_file.relative_to(self.repo_root)

                matches = url_pattern.findall(content)
                for url in matches:
                    url = url.rstrip('.,;:')

                    if url in urls_checked:
                        continue

                    is_excluded = any(domain in url for domain in excluded_domains)
                    if is_excluded:
                        continue

                    urls_checked.add(url)

                    try:
                        response = requests.head(url, timeout=10, allow_redirects=True)
                        if response.status_code >= 400:
                            broken_links.append((relative_path, url, response.status_code))
                            self.log_verbose(f"Broken link: {url} (status: {response.status_code})")
                    except requests.RequestException as e:
                        broken_links.append((relative_path, url, str(e)))
                        self.log_verbose(f"Failed to check: {url} ({e})")
            except Exception as e:
                self.log_warn(f"Could not read {md_file}: {e}")

        if broken_links:
            for file_path, url, status in broken_links:
                self.log_fail(f"Broken link in {file_path}: {url} (status: {status})")
        else:
            self.log_pass(f"All {len(urls_checked)} external links are valid")

    def print_summary(self) -> int:
        print("\n" + "=" * 50)
        print("Architecture Manifest Verification Summary")
        print("=" * 50)

        total_checks = self.checks_passed + len(self.errors) + len(self.warnings)
        print(f"Total checks: {total_checks}")
        print(f"{Colors.GREEN}Passed: {self.checks_passed}{Colors.NC}")
        print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.NC}")
        print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.NC}")
        print()

        if self.errors:
            print(f"{Colors.RED}❌ Verification FAILED{Colors.NC}")
            print("Please fix the errors above before proceeding.")
            return 1
        elif self.warnings:
            print(f"{Colors.YELLOW}⚠️  Verification PASSED with warnings{Colors.NC}")
            print("Consider addressing the warnings above.")
            return 0
        else:
            print(f"{Colors.GREEN}✅ Verification PASSED{Colors.NC}")
            print("All checks passed successfully!")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="Verify architecture manifest against repository state"
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Enable link freshness checking (requires network access)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    print("=" * 50)
    print("Architecture Manifest Verification")
    print("=" * 50)

    verifier = ManifestVerifier(repo_root, verbose=args.verbose)

    manifest = verifier.load_manifest()
    if manifest is None:
        return 1

    verifier.verify_required_paths(manifest)
    verifier.verify_service_paths(manifest)
    verifier.check_docs_for_invalid_aliases(manifest)
    verifier.check_link_security(manifest)
    verifier.check_link_freshness(check_links=args.check_links)

    return verifier.print_summary()


if __name__ == "__main__":
    sys.exit(main())
