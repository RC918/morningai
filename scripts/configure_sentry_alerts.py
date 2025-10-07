#!/usr/bin/env python3
"""
Sentry Alert Rules Configuration Script

This script automatically creates alert rules in Sentry for:
1. Web: High frequency errors (>10 in 5min)
2. Worker: Job failures (3 consecutive failures)

Usage:
    export SENTRY_AUTH_TOKEN="your-token"
    export SENTRY_ORG_SLUG="your-org"
    export SENTRY_PROJECT_SLUG="morningai"
    export SLACK_WEBHOOK_URL="your-slack-webhook"
    
    python scripts/configure_sentry_alerts.py --dry-run
    python scripts/configure_sentry_alerts.py
"""

import os
import sys
import argparse
import requests
import json
from typing import Dict, List, Optional


class SentryAlertConfigurator:
    def __init__(self, auth_token: str, org_slug: str, project_slug: str):
        self.auth_token = auth_token
        self.org_slug = org_slug
        self.project_slug = project_slug
        self.base_url = "https://sentry.io/api/0"
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def create_web_error_alert(self, slack_webhook: Optional[str] = None, dry_run: bool = False) -> Dict:
        """Create alert rule for high frequency web errors"""
        rule_config = {
            "name": "Web - High Frequency Errors",
            "environment": "production",
            "actionMatch": "all",
            "filterMatch": "all",
            "conditions": [
                {
                    "id": "sentry.rules.conditions.first_seen_event.FirstSeenEventCondition"
                },
                {
                    "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
                    "interval": "5m",
                    "value": 10
                }
            ],
            "filters": [
                {
                    "id": "sentry.rules.filters.issue_occurrences.IssueOccurrencesFilter",
                    "value": 1
                }
            ],
            "actions": [
                {
                    "id": "sentry.mail.actions.NotifyEmailAction",
                    "targetType": "IssueOwners"
                }
            ],
            "frequency": 30
        }
        
        if slack_webhook:
            rule_config["actions"].append({
                "id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
                "workspace": slack_webhook,
                "channel": "#oncall"
            })
        
        if dry_run:
            print("DRY RUN - Would create Web Error Alert:")
            print(json.dumps(rule_config, indent=2))
            return {"dry_run": True, "config": rule_config}
        
        url = f"{self.base_url}/projects/{self.org_slug}/{self.project_slug}/rules/"
        response = requests.post(url, headers=self.headers, json=rule_config)
        response.raise_for_status()
        return response.json()
    
    def create_worker_failure_alert(self, slack_webhook: Optional[str] = None, dry_run: bool = False) -> Dict:
        """Create alert rule for worker job failures"""
        rule_config = {
            "name": "Worker - Job Failures",
            "environment": "production",
            "actionMatch": "all",
            "filterMatch": "all",
            "conditions": [
                {
                    "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
                    "interval": "15m",
                    "value": 3
                }
            ],
            "filters": [
                {
                    "id": "sentry.rules.filters.tagged_event.TaggedEventFilter",
                    "key": "worker",
                    "match": "eq",
                    "value": "true"
                }
            ],
            "actions": [
                {
                    "id": "sentry.mail.actions.NotifyEmailAction",
                    "targetType": "IssueOwners"
                }
            ],
            "frequency": 30
        }
        
        if slack_webhook:
            rule_config["actions"].append({
                "id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
                "workspace": slack_webhook,
                "channel": "#oncall"
            })
        
        if dry_run:
            print("DRY RUN - Would create Worker Failure Alert:")
            print(json.dumps(rule_config, indent=2))
            return {"dry_run": True, "config": rule_config}
        
        url = f"{self.base_url}/projects/{self.org_slug}/{self.project_slug}/rules/"
        response = requests.post(url, headers=self.headers, json=rule_config)
        response.raise_for_status()
        return response.json()
    
    def list_existing_rules(self) -> List[Dict]:
        """List all existing alert rules"""
        url = f"{self.base_url}/projects/{self.org_slug}/{self.project_slug}/rules/"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


def main():
    parser = argparse.ArgumentParser(description="Configure Sentry alert rules")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating")
    parser.add_argument("--list", action="store_true", help="List existing alert rules")
    args = parser.parse_args()
    
    auth_token = os.environ.get("SENTRY_AUTH_TOKEN")
    org_slug = os.environ.get("SENTRY_ORG_SLUG")
    project_slug = os.environ.get("SENTRY_PROJECT_SLUG", "morningai")
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not auth_token:
        print("ERROR: SENTRY_AUTH_TOKEN environment variable is required")
        sys.exit(1)
    
    if not org_slug:
        print("ERROR: SENTRY_ORG_SLUG environment variable is required")
        sys.exit(1)
    
    configurator = SentryAlertConfigurator(auth_token, org_slug, project_slug)
    
    if args.list:
        print("Existing alert rules:")
        rules = configurator.list_existing_rules()
        for rule in rules:
            print(f"  - {rule['name']} (ID: {rule['id']})")
        return
    
    print("Creating Sentry alert rules...")
    print(f"Organization: {org_slug}")
    print(f"Project: {project_slug}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    print("1. Creating Web Error Alert...")
    web_result = configurator.create_web_error_alert(slack_webhook, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"   ✓ Created: {web_result.get('name')} (ID: {web_result.get('id')})")
        print(f"   URL: https://sentry.io/organizations/{org_slug}/alerts/rules/{project_slug}/{web_result.get('id')}/")
    print()
    
    print("2. Creating Worker Failure Alert...")
    worker_result = configurator.create_worker_failure_alert(slack_webhook, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"   ✓ Created: {worker_result.get('name')} (ID: {worker_result.get('id')})")
        print(f"   URL: https://sentry.io/organizations/{org_slug}/alerts/rules/{project_slug}/{worker_result.get('id')}/")
    print()
    
    if args.dry_run:
        print("✓ Dry run completed. Run without --dry-run to create the rules.")
    else:
        print("✓ Alert rules created successfully!")
        print("\nNext steps:")
        print("1. Test the alerts by triggering errors")
        print("2. Update docs/sentry-alerts.md with the rule URLs")
        print("3. Configure Slack/Email notification channels in Sentry UI if needed")


if __name__ == "__main__":
    main()
