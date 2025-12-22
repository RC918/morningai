"""
Tests for graph.py orchestrator functions
"""
import pytest
import os
import sys
import uuid
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graph import (
    planner, execute, main,
    make_topic_slug, validate_faq_content, is_protected_path,
    DocIssue, DocIssueLevel,
    CORE_DOCS_PROTECTED, GENERATED_DOCS_PATH, MAX_SLUG_LENGTH,
    LABEL_ORCHESTRATOR_DOCS, LABEL_ORCHESTRATOR_DOCS_TEST, LABEL_ORCHESTRATOR_APPROVED
)


class TestPlanner:
    """Test planner function"""
    
    @patch('graph.save_text')
    def test_planner_returns_steps(self, mock_save):
        """Test planner returns correct steps"""
        goal = "Create FAQ documentation"
        
        steps = planner(goal)
        
        assert isinstance(steps, list)
        assert len(steps) == 4
        assert "analyze" in steps
        assert "patch" in steps
        assert "open PR" in steps
        assert "check CI" in steps
        
        mock_save.assert_called_once_with("goal", goal)
    
    @patch('graph.save_text')
    def test_planner_saves_goal_to_memory(self, mock_save):
        """Test planner saves goal to memory"""
        goal = "Update documentation"
        
        planner(goal)
        
        mock_save.assert_called_once_with("goal", goal)


class TestExecute:
    """Test execute function"""
    
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    @patch('subprocess.run')
    def test_execute_success(self, mock_subprocess, mock_get_repo, mock_create_branch, 
                            mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks,
                            mock_rate_limit):
        """Test execute function with successful workflow"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ Content\n\nTest content"
        mock_open_pr.return_value = ("https://github.com/test/pr/1", 1)
        mock_pr_checks.return_value = ("success", {"check1": "passed"})
        mock_rate_limit.return_value = (True, 1)  # Not rate limited
        
        goal = "Create FAQ"
        repo_full = "owner/repo"
        
        pr_url, state, trace_id = execute(goal, repo_full)
        
        assert pr_url == "https://github.com/test/pr/1"
        assert state == "success"
        assert trace_id is not None
        
        mock_get_repo.assert_called_once()
        mock_create_branch.assert_called_once()
        mock_generate_faq.assert_called_once()
        mock_commit.assert_called_once()
        mock_open_pr.assert_called_once()
        mock_pr_checks.assert_called_once()
    
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    def test_execute_with_trace_id(self, mock_get_repo, mock_create_branch, 
                                   mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks,
                                   mock_rate_limit):
        """Test execute with provided trace_id"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ Content"
        mock_open_pr.return_value = ("https://github.com/test/pr/2", 2)
        mock_pr_checks.return_value = ("pending", {})
        mock_rate_limit.return_value = (True, 1)  # Not rate limited
        
        custom_trace_id = "custom-trace-123"
        pr_url, state, trace_id = execute("Test", "owner/repo", trace_id=custom_trace_id)
        
        assert trace_id == custom_trace_id
    
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    def test_execute_generates_new_trace_id(self, mock_get_repo, mock_create_branch, 
                                           mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks,
                                           mock_rate_limit):
        """Test execute generates UUID when trace_id is None"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ"
        mock_open_pr.return_value = ("https://github.com/test/pr/3", 3)
        mock_pr_checks.return_value = ("success", {})
        mock_rate_limit.return_value = (True, 1)  # Not rate limited
        
        pr_url, state, trace_id = execute("Test", "owner/repo", trace_id=None)
        
        assert trace_id is not None
        assert len(trace_id) > 0
    
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    @patch('subprocess.run')
    def test_execute_auto_merge_enabled(self, mock_subprocess, mock_get_repo, mock_create_branch, 
                                       mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks,
                                       mock_rate_limit):
        """Test execute disables auto-merge for docs PRs (Issue #2100 human gate)"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ\n\nThis is a comprehensive guide.\n\nGenerated by MorningAI\ntrace-id: test-123"
        mock_open_pr.return_value = ("https://github.com/test/pr/4", 4)
        mock_pr_checks.return_value = ("success", {})
        mock_rate_limit.return_value = (True, 1)  # Not rate limited
        
        pr_url, state, trace_id = execute("Test", "owner/repo")
        
        # Issue #2100: Auto-merge is now disabled for docs PRs (human gate)
        # subprocess.run (gh pr merge --auto) should NOT be called
        mock_subprocess.assert_not_called()
        # But PR should still be created successfully
        assert pr_url == "https://github.com/test/pr/4"
    
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    @patch('subprocess.run')
    def test_execute_handles_auto_merge_failure(self, mock_subprocess, mock_get_repo, mock_create_branch, 
                                                mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks,
                                                mock_rate_limit):
        """Test execute creates PR successfully (auto-merge disabled for docs PRs per Issue #2100)"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ\n\nThis is a comprehensive guide.\n\nGenerated by MorningAI\ntrace-id: test-123"
        mock_open_pr.return_value = ("https://github.com/test/pr/5", 5)
        mock_pr_checks.return_value = ("success", {})
        mock_rate_limit.return_value = (True, 1)  # Not rate limited
        # Note: subprocess.run side_effect no longer matters since auto-merge is disabled
        
        pr_url, state, trace_id = execute("Test", "owner/repo")
        
        assert pr_url == "https://github.com/test/pr/5"
    
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    def test_execute_handles_faq_generation_failure(self, mock_get_repo, mock_create_branch, 
                                                    mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks,
                                                    mock_rate_limit):
        """Test execute handles FAQ generation failure with fallback"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_rate_limit.return_value = (True, 1)  # Not rate limited
        
        mock_generate_faq.side_effect = [
            Exception("Generation failed"),
            "# Fallback FAQ Content\n\nThis is a comprehensive guide.\n\nGenerated by MorningAI\ntrace-id: test-123"
        ]
        mock_open_pr.return_value = ("https://github.com/test/pr/6", 6)
        mock_pr_checks.return_value = ("success", {})
        
        pr_url, state, trace_id = execute("Test", "owner/repo")
        
        assert pr_url == "https://github.com/test/pr/6"
        assert mock_generate_faq.call_count == 2


class TestExecuteDryRun:
    """Test execute function with ORCHESTRATOR_DRY_RUN flag"""
    
    @patch('graph.settings')
    @patch('graph.evaluate_execution_policy')
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_cost_tracker')
    @patch('graph.get_reputation_engine')
    def test_execute_dry_run_skips_github_operations(
        self, mock_reputation, mock_cost_tracker, mock_rate_limit, 
        mock_policy, mock_settings
    ):
        """Test execute returns synthetic results when dry_run is enabled"""
        # Setup mocks
        mock_settings.orchestrator_dry_run = True
        mock_settings.orchestrator_test_mode = False
        mock_settings.redis_url = "redis://localhost"
        
        mock_cost_tracker_instance = Mock()
        mock_cost_tracker.return_value = mock_cost_tracker_instance
        
        mock_reputation_instance = Mock()
        mock_reputation_instance.get_or_create_agent.return_value = "agent-123"
        mock_reputation.return_value = mock_reputation_instance
        
        mock_rate_limit.return_value = (True, 0)  # Allowed, 0 PRs created
        
        goal = "Test FAQ question"
        repo_full = "RC918/morningai"
        trace_id = "test-trace-dry-run-123"
        
        pr_url, state, returned_trace_id = execute(goal, repo_full, trace_id=trace_id)
        
        # Verify dry_run results
        assert pr_url == f"dry-run://trace/{trace_id}"
        assert state == "dry_run"
        assert returned_trace_id == trace_id
    
    @patch('graph.settings')
    @patch('graph.evaluate_execution_policy')
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_cost_tracker')
    @patch('graph.get_reputation_engine')
    def test_execute_dry_run_does_not_call_github_api(
        self, mock_reputation, mock_cost_tracker, mock_rate_limit,
        mock_policy, mock_settings
    ):
        """Test execute does not call GitHub API functions when dry_run is enabled"""
        # Setup mocks
        mock_settings.orchestrator_dry_run = True
        mock_settings.orchestrator_test_mode = False
        mock_settings.redis_url = "redis://localhost"
        
        mock_cost_tracker_instance = Mock()
        mock_cost_tracker.return_value = mock_cost_tracker_instance
        
        mock_reputation_instance = Mock()
        mock_reputation_instance.get_or_create_agent.return_value = "agent-123"
        mock_reputation.return_value = mock_reputation_instance
        
        mock_rate_limit.return_value = (True, 0)
        
        with patch('graph.get_repo') as mock_get_repo, \
             patch('graph.create_branch') as mock_create_branch, \
             patch('graph.commit_file') as mock_commit, \
             patch('graph.open_pr') as mock_open_pr:
            
            execute("Test", "owner/repo", trace_id="dry-run-test")
            
            # Verify GitHub functions were NOT called
            mock_get_repo.assert_not_called()
            mock_create_branch.assert_not_called()
            mock_commit.assert_not_called()
            mock_open_pr.assert_not_called()
    
    @patch('graph.settings')
    @patch('graph.evaluate_execution_policy')
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_cost_tracker')
    @patch('graph.get_reputation_engine')
    def test_execute_dry_run_generates_trace_id_if_not_provided(
        self, mock_reputation, mock_cost_tracker, mock_rate_limit,
        mock_policy, mock_settings
    ):
        """Test execute generates trace_id when not provided in dry_run mode"""
        mock_settings.orchestrator_dry_run = True
        mock_settings.orchestrator_test_mode = False
        mock_settings.redis_url = "redis://localhost"
        
        mock_cost_tracker_instance = Mock()
        mock_cost_tracker.return_value = mock_cost_tracker_instance
        
        mock_reputation_instance = Mock()
        mock_reputation_instance.get_or_create_agent.return_value = "agent-123"
        mock_reputation.return_value = mock_reputation_instance
        
        mock_rate_limit.return_value = (True, 0)
        
        pr_url, state, trace_id = execute("Test", "owner/repo", trace_id=None)
        
        assert trace_id is not None
        assert len(trace_id) > 0
        assert pr_url == f"dry-run://trace/{trace_id}"
        assert state == "dry_run"


class TestMain:
    """Test main function"""
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_success(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main function with successful execution"""
        mock_planner.return_value = ["step1", "step2"]
        mock_enqueue.return_value = ["job-1", "job-2"]
        mock_execute.return_value = ("https://github.com/pr/1", "success", "trace-123")
        mock_recall.return_value = [{"text": "memory1"}]
        
        main("Test goal", "owner/repo")
        
        mock_planner.assert_called_once_with("Test goal")
        mock_enqueue.assert_called_once()
        mock_execute.assert_called_once()
        mock_recall.assert_called_once_with("recent")
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_redis_unavailable(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main handles Redis unavailability"""
        mock_planner.return_value = ["step1", "step2", "step3"]
        mock_enqueue.side_effect = Exception("Redis connection failed")
        mock_execute.return_value = ("https://github.com/pr/2", "success", "trace-456")
        mock_recall.return_value = []
        
        main("Test goal", "owner/repo")
        
        mock_execute.assert_called_once()
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_github_unavailable(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main handles GitHub API unavailability"""
        mock_planner.return_value = ["step1"]
        mock_enqueue.return_value = ["job-1"]
        mock_execute.side_effect = Exception("GitHub API error")
        mock_recall.return_value = []
        
        main("Test goal", "owner/repo")
        
        mock_execute.assert_called_once()
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_supabase_unavailable(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main handles Supabase unavailability"""
        mock_planner.return_value = ["step1"]
        mock_enqueue.return_value = ["job-1"]
        mock_execute.return_value = ("https://github.com/pr/3", "success", "trace-789")
        mock_recall.side_effect = Exception("Supabase connection failed")
        
        main("Test goal", "owner/repo")
        
        mock_recall.assert_called_once()
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_generates_trace_id(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main generates unique trace ID"""
        mock_planner.return_value = ["step1"]
        mock_enqueue.return_value = ["job-1"]
        
        trace_ids = []
        def capture_trace_id(goal, repo, trace_id):
            trace_ids.append(trace_id)
            return ("https://github.com/pr/1", "success", trace_id)
        
        mock_execute.side_effect = capture_trace_id
        mock_recall.return_value = []
        
        main("Test goal", "owner/repo")
        
        assert len(trace_ids) == 1
        assert trace_ids[0] is not None
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_uses_idempotency_key(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main uses idempotency key for queue"""
        mock_planner.return_value = ["step1", "step2"]
        mock_enqueue.return_value = ["job-1", "job-2"]
        mock_execute.return_value = ("https://github.com/pr/1", "success", "trace-123")
        mock_recall.return_value = []
        
        goal = "Test goal with idempotency"
        main(goal, "owner/repo")
        
        call_args = mock_enqueue.call_args
        assert call_args[1]['idempotency_key'] is not None


# =============================================================================
# Issue #2100: Documentation Safety Tests
# =============================================================================

class TestMakeTopicSlug:
    """Test make_topic_slug function for Issue #2100"""
    
    def test_basic_slug_generation(self):
        """Test basic slug generation from goal"""
        slug = make_topic_slug("How to setup authentication")
        assert "how-to-setup-authentication" in slug
        # Should have hash suffix
        assert len(slug.split('-')[-1]) == 8
    
    def test_slug_removes_special_characters(self):
        """Test slug removes special characters"""
        slug = make_topic_slug("What's the best way to configure OAuth2?")
        assert "'" not in slug
        assert "?" not in slug
        assert "whats-the-best-way-to-configure-oauth2" in slug
    
    def test_slug_collapses_whitespace(self):
        """Test slug collapses multiple whitespace to single hyphen"""
        slug = make_topic_slug("How   to    setup   auth")
        assert "---" not in slug
        assert "how-to-setup-auth" in slug
    
    def test_slug_handles_empty_string(self):
        """Test slug handles empty string gracefully"""
        slug = make_topic_slug("")
        # Should return just the hash
        assert len(slug) == 8
    
    def test_slug_handles_special_chars_only(self):
        """Test slug handles string with only special characters"""
        slug = make_topic_slug("???!!!")
        # Should return just the hash
        assert len(slug) == 8
    
    def test_slug_truncates_long_goals(self):
        """Test slug truncates very long goals"""
        long_goal = "This is a very long goal that should be truncated " * 10
        slug = make_topic_slug(long_goal)
        # Should be within MAX_SLUG_LENGTH
        assert len(slug) <= MAX_SLUG_LENGTH
    
    def test_slug_is_deterministic(self):
        """Test same goal produces same slug"""
        goal = "How to configure dark mode"
        slug1 = make_topic_slug(goal)
        slug2 = make_topic_slug(goal)
        assert slug1 == slug2
    
    def test_slug_different_for_different_goals(self):
        """Test different goals produce different slugs"""
        slug1 = make_topic_slug("How to setup auth")
        slug2 = make_topic_slug("How to configure database")
        assert slug1 != slug2
    
    def test_slug_lowercase(self):
        """Test slug is lowercase"""
        slug = make_topic_slug("HOW TO SETUP AUTH")
        assert slug == slug.lower()


class TestValidateFaqContent:
    """Test validate_faq_content function for Issue #2100"""
    
    def test_valid_content_no_issues(self):
        """Test valid content returns no issues"""
        content = """# FAQ: How to setup authentication
        
This is a comprehensive guide to setting up authentication.

## Steps
1. Configure your environment
2. Set up the database with tenant_id filters
3. Test the authentication flow

---
Generated by MorningAI Orchestrator
trace-id: test-123
"""
        issues = validate_faq_content("How to setup auth", content)
        # Should have no errors (may have warnings)
        errors = [i for i in issues if i.level == DocIssueLevel.ERROR]
        assert len(errors) == 0
    
    def test_detects_missing_tenant_filter_in_sql(self):
        """Test detects SQL without tenant filter"""
        content = """# FAQ
        
Here's how to query users:

```sql
SELECT * FROM users WHERE email = 'test@example.com'
```

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("Query users", content)
        codes = [i.code for i in issues]
        assert "MISSING_TENANT_FILTER" in codes
    
    def test_sql_with_tenant_filter_passes(self):
        """Test SQL with tenant filter passes"""
        content = """# FAQ
        
Here's how to query users:

```sql
SELECT * FROM users WHERE tenant_id = 'abc' AND email = 'test@example.com'
```

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("Query users", content)
        codes = [i.code for i in issues]
        assert "MISSING_TENANT_FILTER" not in codes
    
    def test_detects_missing_auth_in_api_example(self):
        """Test detects API example without auth context"""
        content = """# FAQ
        
Here's how to call the API:

```bash
curl https://api.example.com/users
```

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("API call", content)
        codes = [i.code for i in issues]
        assert "MISSING_AUTH_CONTEXT" in codes
    
    def test_api_with_auth_passes(self):
        """Test API example with auth passes"""
        content = """# FAQ
        
Here's how to call the API:

```bash
curl -H "Authorization: Bearer token" https://api.example.com/users
```

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("API call", content)
        codes = [i.code for i in issues]
        assert "MISSING_AUTH_CONTEXT" not in codes
    
    def test_detects_hardcoded_password(self):
        """Test detects hardcoded password"""
        content = """# FAQ
        
Configure your settings:

```python
password = "supersecret123"
```

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("Config", content)
        codes = [i.code for i in issues]
        assert "HARDCODED_PASSWORD" in codes
        # Should be an error, not warning
        error_issues = [i for i in issues if i.level == DocIssueLevel.ERROR]
        assert any(i.code == "HARDCODED_PASSWORD" for i in error_issues)
    
    def test_detects_hardcoded_api_key(self):
        """Test detects hardcoded API key"""
        content = """# FAQ
        
Set your API key:

```python
api_key = "sk-1234567890abcdef"
```

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("API setup", content)
        codes = [i.code for i in issues]
        assert "HARDCODED_API_KEY" in codes
    
    def test_detects_missing_metadata(self):
        """Test detects missing metadata footer"""
        content = """# FAQ
        
This is some content without metadata.
"""
        issues = validate_faq_content("Test", content)
        codes = [i.code for i in issues]
        assert "MISSING_METADATA" in codes
    
    def test_detects_content_too_short(self):
        """Test detects content that is too short"""
        content = "# FAQ\n\nShort."
        issues = validate_faq_content("Test", content)
        codes = [i.code for i in issues]
        assert "CONTENT_TOO_SHORT" in codes
        # Should be an error
        error_issues = [i for i in issues if i.level == DocIssueLevel.ERROR]
        assert any(i.code == "CONTENT_TOO_SHORT" for i in error_issues)
    
    def test_dark_mode_without_theme_context(self):
        """Test detects dark mode docs without ThemeContext"""
        content = """# FAQ: Dark Mode Setup
        
Here's how to enable dark mode in your application.

1. Add the dark mode toggle
2. Update your CSS

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("Dark mode", content)
        codes = [i.code for i in issues]
        assert "MISSING_THEME_CONTEXT" in codes
    
    def test_dark_mode_with_theme_context_passes(self):
        """Test dark mode docs with ThemeContext passes"""
        content = """# FAQ: Dark Mode Setup
        
Here's how to enable dark mode using ThemeContext.

1. Import ThemeContext from your theme provider
2. Use the useTheme hook

Generated by MorningAI
trace-id: test-123
"""
        issues = validate_faq_content("Dark mode", content)
        codes = [i.code for i in issues]
        assert "MISSING_THEME_CONTEXT" not in codes


class TestIsProtectedPath:
    """Test is_protected_path function for Issue #2100"""
    
    def test_faq_md_is_protected(self):
        """Test docs/FAQ.md is protected"""
        assert is_protected_path("docs/FAQ.md") is True
    
    def test_readme_is_protected(self):
        """Test README.md is protected"""
        assert is_protected_path("README.md") is True
        assert is_protected_path("docs/README.md") is True
    
    def test_generated_docs_not_protected(self):
        """Test generated docs path is not protected"""
        assert is_protected_path("docs/generated/my-topic-abc123.md") is False
    
    def test_case_insensitive(self):
        """Test protection is case insensitive"""
        assert is_protected_path("docs/faq.md") is True
        assert is_protected_path("DOCS/FAQ.MD") is True
    
    def test_windows_path_separator(self):
        """Test handles Windows path separators"""
        assert is_protected_path("docs\\FAQ.md") is True
    
    def test_arbitrary_docs_not_protected(self):
        """Test arbitrary docs are not protected"""
        assert is_protected_path("docs/my-custom-doc.md") is False
        assert is_protected_path("docs/guides/setup.md") is False


class TestDocsSafetyConstants:
    """Test documentation safety constants for Issue #2100"""
    
    def test_core_docs_protected_list(self):
        """Test CORE_DOCS_PROTECTED contains expected files"""
        assert "docs/FAQ.md" in CORE_DOCS_PROTECTED
        assert "README.md" in CORE_DOCS_PROTECTED
    
    def test_generated_docs_path(self):
        """Test GENERATED_DOCS_PATH is correct"""
        assert GENERATED_DOCS_PATH == "docs/generated"
    
    def test_max_slug_length(self):
        """Test MAX_SLUG_LENGTH is reasonable"""
        assert MAX_SLUG_LENGTH == 60
    
    def test_label_constants(self):
        """Test label constants are defined"""
        assert LABEL_ORCHESTRATOR_DOCS == "orchestrator-docs"
        assert LABEL_ORCHESTRATOR_DOCS_TEST == "orchestrator-docs-test"
        assert LABEL_ORCHESTRATOR_APPROVED == "orchestrator-approved"


class TestExecuteDocsSafety:
    """Test execute function with docs safety features for Issue #2100"""
    
    @patch('graph.settings')
    @patch('graph.evaluate_execution_policy')
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_cost_tracker')
    @patch('graph.get_reputation_engine')
    def test_execute_uses_docs_rate_limit(
        self, mock_reputation, mock_cost_tracker, mock_rate_limit,
        mock_policy, mock_settings
    ):
        """Test execute uses configurable docs PR rate limit"""
        mock_settings.orchestrator_dry_run = True
        mock_settings.orchestrator_test_mode = True
        mock_settings.orchestrator_docs_max_prs_per_hour = 3
        mock_settings.redis_url = "redis://localhost"
        
        mock_cost_tracker_instance = Mock()
        mock_cost_tracker.return_value = mock_cost_tracker_instance
        
        mock_reputation_instance = Mock()
        mock_reputation_instance.get_or_create_agent.return_value = "agent-123"
        mock_reputation.return_value = mock_reputation_instance
        
        mock_rate_limit.return_value = (True, 1)
        
        execute("Test FAQ", "owner/repo", trace_id="test-123")
        
        # Verify rate limit was called with docs max (3)
        mock_rate_limit.assert_called_once()
        call_args = mock_rate_limit.call_args
        assert call_args[1]['max_per_hour'] == 3
    
    @patch('graph.settings')
    @patch('graph.evaluate_execution_policy')
    @patch('graph.check_pr_rate_limit')
    @patch('graph.get_cost_tracker')
    @patch('graph.get_reputation_engine')
    def test_execute_rate_limited_returns_early(
        self, mock_reputation, mock_cost_tracker, mock_rate_limit,
        mock_policy, mock_settings
    ):
        """Test execute returns early when rate limited"""
        mock_settings.orchestrator_dry_run = False
        mock_settings.orchestrator_test_mode = True
        mock_settings.orchestrator_docs_max_prs_per_hour = 3
        mock_settings.redis_url = "redis://localhost"
        
        mock_cost_tracker_instance = Mock()
        mock_cost_tracker.return_value = mock_cost_tracker_instance
        
        mock_reputation_instance = Mock()
        mock_reputation_instance.get_or_create_agent.return_value = "agent-123"
        mock_reputation.return_value = mock_reputation_instance
        
        # Rate limited - already created 4 PRs
        mock_rate_limit.return_value = (False, 4)
        
        pr_url, state, trace_id = execute("Test FAQ", "owner/repo", trace_id="test-123")
        
        assert pr_url is None
        assert state == "rate_limited"
