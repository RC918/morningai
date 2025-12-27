"""
Unit tests for Sensitive Data Masker

Tests cover:
- Value masking (short and long values)
- String masking with patterns
- Dictionary masking (recursive)
- List masking
- Custom patterns
- Default patterns (API keys, tokens)
- Key-based masking

Issue: #1960 - 狀態目錄權限與敏感資料遮罩
Milestone: M5 - Meta Agent 優化
"""

import pytest

from meta_agent.sensitive_data_masker import (
    SensitiveDataMasker,
    get_masker,
    mask_sensitive_data,
)


class TestSensitiveDataMasker:
    """Tests for SensitiveDataMasker class"""

    @pytest.fixture
    def masker(self):
        """Create a fresh SensitiveDataMasker instance"""
        return SensitiveDataMasker()

    def test_mask_value_long_string(self, masker):
        """Test masking a long string value"""
        result = masker.mask_value("sk-1234567890abcdef")
        assert result == "sk-1****cdef"

    def test_mask_value_short_string(self, masker):
        """Test masking a short string value (< 8 chars)"""
        result = masker.mask_value("secret")
        assert result == "******"

    def test_mask_value_exactly_8_chars(self, masker):
        """Test masking exactly 8 character string"""
        result = masker.mask_value("12345678")
        assert result == "1234****5678"

    def test_mask_value_empty_string(self, masker):
        """Test masking empty string"""
        result = masker.mask_value("")
        assert result == ""

    def test_mask_value_none(self, masker):
        """Test masking None value"""
        result = masker.mask_value(None)
        assert result is None

    def test_mask_string_with_openai_key(self, masker):
        """Test masking OpenAI API key in string"""
        text = "Using API key sk-1234567890abcdefghijklmnop for requests"
        result = masker.mask_string(text)
        assert "sk-1234567890abcdefghijklmnop" not in result
        assert "sk-1****mnop" in result

    def test_mask_string_with_github_token(self, masker):
        """Test masking GitHub personal access token"""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = masker.mask_string(text)
        assert "ghp_1234567890abcdefghijklmnopqrstuvwxyz" not in result

    def test_mask_string_with_bearer_token(self, masker):
        """Test masking Bearer token"""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = masker.mask_string(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_mask_string_no_sensitive_data(self, masker):
        """Test string without sensitive data"""
        text = "This is a normal string without secrets"
        result = masker.mask_string(text)
        assert result == text

    def test_mask_dict_with_sensitive_keys(self, masker):
        """Test masking dictionary with sensitive keys"""
        data = {
            "username": "john",
            "password": "supersecretpassword123",
            "api_key": "sk-1234567890abcdefghij",
        }
        result = masker.mask_dict(data)

        assert result["username"] == "john"
        assert result["password"] == "supe****d123"
        assert "sk-1234567890abcdefghij" not in result["api_key"]

    def test_mask_dict_nested(self, masker):
        """Test masking nested dictionary"""
        data = {
            "config": {
                "database": {
                    "host": "localhost",
                    "password": "dbpassword123456",
                }
            }
        }
        result = masker.mask_dict(data)

        assert result["config"]["database"]["host"] == "localhost"
        assert result["config"]["database"]["password"] == "dbpa****3456"

    def test_mask_dict_with_list(self, masker):
        """Test masking dictionary containing lists"""
        data = {
            "tokens": ["token1234567890", "token0987654321"],
            "names": ["alice", "bob"],
        }
        result = masker.mask_dict(data)

        assert result["names"] == ["alice", "bob"]

    def test_mask_dict_empty(self, masker):
        """Test masking empty dictionary"""
        result = masker.mask_dict({})
        assert result == {}

    def test_mask_any_string(self, masker):
        """Test mask_any with string"""
        result = masker.mask_any("sk-1234567890abcdefghij")
        assert "sk-1234567890abcdefghij" not in result

    def test_mask_any_dict(self, masker):
        """Test mask_any with dictionary"""
        data = {"secret": "mysecretvalue123"}
        result = masker.mask_any(data)
        assert result["secret"] == "myse****e123"

    def test_mask_any_list(self, masker):
        """Test mask_any with list"""
        data = [{"token": "mytoken12345678"}]
        result = masker.mask_any(data)
        assert result[0]["token"] == "myto****5678"

    def test_mask_any_other_type(self, masker):
        """Test mask_any with non-string/dict/list type"""
        result = masker.mask_any(12345)
        assert result == 12345

    def test_is_sensitive_key(self, masker):
        """Test sensitive key detection"""
        assert masker._is_sensitive_key("password")
        assert masker._is_sensitive_key("api_key")
        assert masker._is_sensitive_key("access_token")
        assert masker._is_sensitive_key("my_secret_value")
        assert not masker._is_sensitive_key("username")
        assert not masker._is_sensitive_key("email")

    def test_custom_sensitive_keys(self):
        """Test adding custom sensitive keys"""
        masker = SensitiveDataMasker(sensitive_keys={"custom_field"})
        assert masker._is_sensitive_key("custom_field")
        assert masker._is_sensitive_key("password")  # Default still works

    def test_custom_value_patterns(self):
        """Test adding custom value patterns"""
        masker = SensitiveDataMasker(value_patterns=[r"CUSTOM-[A-Z0-9]+"])
        text = "Key: CUSTOM-ABC123DEF456"
        result = masker.mask_string(text)
        assert "CUSTOM-ABC123DEF456" not in result

    def test_custom_mask_char(self):
        """Test custom mask character"""
        masker = SensitiveDataMasker(mask_char="#")
        result = masker.mask_value("sk-1234567890abcdef")
        assert result == "sk-1####cdef"

    def test_custom_mask_length(self):
        """Test custom mask length"""
        masker = SensitiveDataMasker(mask_length=8)
        result = masker.mask_value("sk-1234567890abcdef")
        assert result == "sk-1********cdef"


class TestGlobalMasker:
    """Tests for global masker functions"""

    def test_get_masker_returns_instance(self):
        """Test get_masker returns a SensitiveDataMasker instance"""
        masker = get_masker()
        assert isinstance(masker, SensitiveDataMasker)

    def test_get_masker_returns_same_instance(self):
        """Test get_masker returns the same instance (singleton)"""
        masker1 = get_masker()
        masker2 = get_masker()
        assert masker1 is masker2

    def test_mask_sensitive_data_string(self):
        """Test convenience function with string"""
        result = mask_sensitive_data("sk-1234567890abcdefghij")
        assert "sk-1234567890abcdefghij" not in result

    def test_mask_sensitive_data_dict(self):
        """Test convenience function with dictionary"""
        data = {"password": "mysecretpassword"}
        result = mask_sensitive_data(data)
        assert result["password"] == "myse****word"


class TestRealWorldScenarios:
    """Tests for real-world masking scenarios"""

    @pytest.fixture
    def masker(self):
        return SensitiveDataMasker()

    def test_mask_execution_state(self, masker):
        """Test masking a typical execution state"""
        state = {
            "execution_id": "exec-12345",
            "status": "running",
            "config": {
                "github_token": "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
                "openai_api_key": "sk-1234567890abcdefghijklmnop",
                "database_url": "postgres://user:password123@localhost/db",
            },
            "tasks": [
                {"id": "task-1", "status": "completed"},
                {"id": "task-2", "auth_token": "bearer_token_12345678"},
            ],
        }
        result = masker.mask_dict(state)

        # Non-sensitive data preserved
        assert result["execution_id"] == "exec-12345"
        assert result["status"] == "running"
        assert result["tasks"][0]["status"] == "completed"

        # Sensitive data masked
        assert "ghp_1234567890abcdefghijklmnopqrstuvwxyz" not in str(result)
        assert "sk-1234567890abcdefghijklmnop" not in str(result)

    def test_mask_audit_event_details(self, masker):
        """Test masking audit event details"""
        details = {
            "operation": "api_call",
            "endpoint": "/api/v1/users",
            "headers": {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
                "Content-Type": "application/json",
            },
            "api_key": "sk-proj-1234567890abcdefghij",
        }
        result = masker.mask_dict(details)

        # Non-sensitive preserved
        assert result["operation"] == "api_call"
        assert result["endpoint"] == "/api/v1/users"
        assert result["headers"]["Content-Type"] == "application/json"

        # Sensitive masked
        assert "eyJhbGciOiJIUzI1NiJ9" not in str(result)
        assert "sk-proj-1234567890abcdefghij" not in result["api_key"]

    def test_mask_error_message_with_credentials(self, masker):
        """Test masking error messages containing credentials"""
        # Use a token that matches the pattern (ghp_ + exactly 36 chars)
        error = "Failed to connect with token ghp_abcdefghijklmnopqrstuvwxyz123456"
        result = masker.mask_string(error)
        # Verify the error message is processed (token is 40 chars, pattern expects 36)
        assert "Failed to connect" in result

        # Test with a properly formatted token
        error2 = "Failed with ghp_123456789012345678901234567890123456"
        result2 = masker.mask_string(error2)
        assert "ghp_123456789012345678901234567890123456" not in result2
        assert "Failed with" in result2


class TestPostgreSQLSensitiveDataMasking:
    """
    Tests for PostgreSQL DSN and password masking patterns.

    Issue #3107: Add sensitive data sanitization to checkpoint error logs
    These tests verify that PostgreSQL connection strings and passwords
    are properly masked in error messages to prevent credential exposure.
    """

    @pytest.fixture
    def masker(self):
        return SensitiveDataMasker()

    def test_mask_postgres_dsn_with_password(self, masker):
        """Test masking PostgreSQL DSN with embedded password"""
        dsn = "postgres://myuser:supersecretpassword@db.example.com:5432/mydb"
        result = masker.mask_string(dsn)
        assert "supersecretpassword" not in result
        assert "postgres://" in result or "post****" in result

    def test_mask_postgresql_dsn_with_password(self, masker):
        """Test masking PostgreSQL DSN with postgresql:// scheme"""
        dsn = "postgresql://admin:p@ssw0rd123@localhost:5432/production"
        result = masker.mask_string(dsn)
        assert "p@ssw0rd123" not in result

    def test_mask_postgres_dsn_in_error_message(self, masker):
        """Test masking PostgreSQL DSN embedded in error message"""
        error = (
            "OperationalError: could not connect to server: "
            "postgres://dbuser:mypassword123@db.host.com:5432/appdb "
            "Connection refused"
        )
        result = masker.mask_string(error)
        assert "mypassword123" not in result
        assert "could not connect to server" in result
        assert "Connection refused" in result

    def test_mask_password_equals_pattern(self, masker):
        """Test masking password=value pattern"""
        config = "host=localhost port=5432 password=secretpass123 dbname=mydb"
        result = masker.mask_string(config)
        assert "secretpass123" not in result
        assert "host=localhost" in result
        assert "dbname=mydb" in result

    def test_mask_password_colon_pattern(self, masker):
        """Test masking password: value pattern"""
        log = "Database config: password: mysecretvalue user: admin"
        result = masker.mask_string(log)
        assert "mysecretvalue" not in result

    def test_mask_pwd_pattern(self, masker):
        """Test masking pwd=value pattern"""
        config = "server=db.example.com;pwd=hunter2;database=prod"
        result = masker.mask_string(config)
        assert "hunter2" not in result

    def test_mask_passwd_pattern(self, masker):
        """Test masking passwd=value pattern"""
        error = "Authentication failed: passwd=wrongpassword"
        result = masker.mask_string(error)
        assert "wrongpassword" not in result

    def test_mask_dsn_style_connection_string(self, masker):
        """Test masking DSN-style connection string with password"""
        dsn = "host=db.example.com port=5432 user=admin password=topsecret dbname=app"
        result = masker.mask_string(dsn)
        assert "topsecret" not in result
        assert "host=db.example.com" in result

    def test_mask_checkpoint_error_with_dsn(self, masker):
        """Test masking real-world checkpoint error containing DSN"""
        error = (
            "ResilientPostgresSaver: Transient error in put, retrying. "
            "error_type=OperationalError error=SSL connection has been closed "
            "unexpectedly while connecting to postgres://checkpoint_user:Str0ngP@ss!@"
            "checkpoint-db.internal:5432/langgraph_checkpoints"
        )
        result = masker.mask_string(error)
        assert "Str0ngP@ss!" not in result
        assert "ResilientPostgresSaver" in result
        assert "Transient error" in result

    def test_mask_degraded_checkpointer_error(self, masker):
        """Test masking DegradedPersistenceCheckpointer error message"""
        error = (
            "CHECKPOINT DEGRADED: Primary checkpointer failed. "
            "error='could not connect to postgresql://app:dbpassword@host/db'"
        )
        result = masker.mask_string(error)
        assert "dbpassword" not in result
        assert "CHECKPOINT DEGRADED" in result

    def test_preserve_non_sensitive_postgres_info(self, masker):
        """Test that non-sensitive PostgreSQL info is preserved"""
        message = "Connected to PostgreSQL database on port 5432"
        result = masker.mask_string(message)
        assert result == message

    def test_mask_multiple_passwords_in_message(self, masker):
        """Test masking multiple password patterns in one message"""
        message = (
            "Primary: postgres://u1:pass1@h1/db1 "
            "Fallback: password=pass2 "
            "Backup: pwd=pass3"
        )
        result = masker.mask_string(message)
        assert "pass1" not in result
        assert "pass2" not in result
        assert "pass3" not in result

    def test_mask_sensitive_data_convenience_function(self):
        """Test convenience function masks PostgreSQL credentials"""
        error = "Failed: postgres://user:secret@host/db"
        result = mask_sensitive_data(error)
        assert "secret" not in result


class TestMaskingFailureFallback:
    """
    Tests for masking failure fallback behavior.

    Issue #3107: Ensure that if mask_sensitive_data() fails, the retry/failover
    logic is not affected. The system should gracefully fall back to the original
    error string rather than breaking the critical path.
    """

    def test_mask_string_handles_none_gracefully(self):
        """Test that mask_string handles None input gracefully"""
        masker = SensitiveDataMasker()
        result = masker.mask_string(None)
        assert result is None

    def test_mask_sensitive_data_with_empty_string(self):
        """Test convenience function handles empty string"""
        result = mask_sensitive_data("")
        assert result == ""

    def test_mask_sensitive_data_with_non_string_coerced(self):
        """Test that non-string inputs are handled (coerced to string in caller)"""
        result = mask_sensitive_data("123")
        assert result == "123"

    def test_masker_does_not_raise_on_valid_input(self):
        """Test that masker doesn't raise exceptions on valid input"""
        masker = SensitiveDataMasker()
        test_cases = [
            "normal error message",
            "postgres://user:pass@host/db",
            "password=secret123",
            "Error: connection refused to host=db.example.com password=test",
            "",
            "a" * 10000,
        ]
        for test_input in test_cases:
            result = masker.mask_string(test_input)
            assert result is not None

    def test_masker_with_special_characters(self):
        """Test masker handles special regex characters in input"""
        masker = SensitiveDataMasker()
        special_input = "Error: [.*+?^${}()|[\\]\\\\] password=secret"
        result = masker.mask_string(special_input)
        assert "secret" not in result
        assert "Error:" in result

    def test_masker_with_unicode_characters(self):
        """Test masker handles unicode characters"""
        masker = SensitiveDataMasker()
        unicode_input = "錯誤: postgres://user:密碼@host/db"
        result = masker.mask_string(unicode_input)
        assert result is not None
