# Testing Architecture Guide

## Overview

This document defines the testing strategy for the Morning AI project, implementing RFC #619 decision to separate unit tests and integration tests.

## Test Directory Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated, use mocks)
│   ├── routes/             # Route handler unit tests
│   ├── services/           # Business logic unit tests
│   └── middleware/         # Middleware unit tests
├── integration/            # Integration tests (slower, real dependencies)
│   ├── routes/            # Route integration tests
│   └── e2e/               # End-to-end workflow tests
├── fixtures/              # Shared test fixtures
│   ├── auth.py           # Authentication fixtures
│   └── database.py       # Database fixtures
├── conftest.py           # Pytest configuration
└── README.md             # Test documentation
```

## Test Types

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual functions/classes in isolation

**Characteristics**:
- Use mocks for all external dependencies
- Fast execution (< 1 second per test)
- High isolation (no side effects)
- Focus on logic correctness

**Example**:
```python
# tests/unit/routes/test_vectors_unit.py
import pytest
from unittest.mock import Mock, patch

def test_vector_search_logic(mock_jwt_required):
    """Test vector search logic without real dependencies"""
    with patch('src.routes.vectors.search_vectors') as mock_search:
        mock_search.return_value = [{'id': 1, 'text': 'test'}]
        result = perform_vector_search('query')
        assert len(result) == 1
        mock_search.assert_called_once()
```

**When to use**:
- Testing business logic
- Testing error handling
- Testing edge cases
- Fast feedback during development

### Integration Tests (`tests/integration/`)

**Purpose**: Test multiple components working together

**Characteristics**:
- Use real Flask app and JWT tokens
- Medium execution speed (1-5 seconds per test)
- Test component interactions
- Verify API contracts

**Example**:
```python
# tests/integration/routes/test_vectors_integration.py
import pytest
from src.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_vector_search_endpoint(client, auth_headers):
    """Test vector search endpoint with real dependencies"""
    response = client.post(
        '/api/vectors/search',
        json={'query': 'test'},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert 'results' in response.json
```

**When to use**:
- Testing API endpoints
- Testing authentication flows
- Testing database interactions
- Verifying system behavior

### E2E Tests (`tests/integration/e2e/`)

**Purpose**: Test complete user workflows

**Characteristics**:
- Test full user journeys
- Slowest execution (5-30 seconds per test)
- Use real services (database, Redis, etc.)
- Verify business requirements

**Example**:
```python
# tests/integration/e2e/test_user_workflow.py
def test_complete_user_journey(client, auth_headers):
    """Test complete user workflow from login to data retrieval"""
    # 1. Login
    login_response = client.post('/api/auth/login', json={...})
    assert login_response.status_code == 200
    
    # 2. Create resource
    create_response = client.post('/api/resource', json={...})
    assert create_response.status_code == 201
    
    # 3. Retrieve resource
    get_response = client.get('/api/resource/1')
    assert get_response.status_code == 200
```

**When to use**:
- Testing critical user paths
- Pre-deployment verification
- Regression testing
- Business requirement validation

## Test Fixtures

### Authentication Fixtures (`tests/fixtures/auth.py`)

**Mock JWT (Unit Tests)**:
```python
def test_protected_endpoint(client, mock_jwt_required):
    """Test endpoint logic without real JWT"""
    response = client.get('/api/protected')
    assert response.status_code == 200
```

**Real JWT (Integration Tests)**:
```python
def test_protected_endpoint_integration(client, auth_headers):
    """Test endpoint with real JWT authentication"""
    response = client.get('/api/protected', headers=auth_headers)
    assert response.status_code == 200
```

### Database Fixtures (`tests/fixtures/database.py`)

**Mock Database (Unit Tests)**:
```python
def test_user_query(mock_db_session):
    """Test database query logic with mock"""
    mock_db_session.query.return_value.filter.return_value.first.return_value = User(id=1)
    user = get_user_by_id(mock_db_session, 1)
    assert user.id == 1
```

**Real Database (Integration Tests)**:
```python
def test_user_creation(db_transaction):
    """Test user creation with real database"""
    user = create_user(name='Test User')
    assert user.id is not None
    # Changes automatically rolled back after test
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_logic():
    """Fast unit test"""
    pass

@pytest.mark.integration
def test_integration_flow():
    """Integration test with real dependencies"""
    pass

@pytest.mark.e2e
def test_complete_workflow():
    """End-to-end test"""
    pass

@pytest.mark.slow
def test_expensive_operation():
    """Test that takes > 1 second"""
    pass
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run only unit tests (fast feedback)
```bash
pytest tests/unit/ -m unit
```

### Run only integration tests
```bash
pytest tests/integration/ -m integration
```

### Run specific test file
```bash
pytest tests/unit/routes/test_vectors_unit.py
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

### Run in parallel (faster)
```bash
pytest -n auto
```

## Coverage Targets

| Test Type | Coverage Target | Execution Frequency |
|-----------|----------------|---------------------|
| Unit Tests | 80%+ | Every commit |
| Integration Tests | 60%+ | Every PR |
| E2E Tests | Critical paths 100% | Pre-deployment |

## CI Configuration

### Fast Feedback (< 30 seconds)
```yaml
- name: Run unit tests
  run: pytest tests/unit/ --maxfail=1 -m unit
```

### Complete Validation (< 5 minutes)
```yaml
- name: Run all tests
  run: pytest tests/unit/ tests/integration/ --cov=src
```

## Best Practices

### DO ✅

1. **Write unit tests first** - Fast feedback during development
2. **Use descriptive test names** - `test_user_creation_with_invalid_email`
3. **One assertion per test** - Clear failure messages
4. **Use fixtures** - Reusable test setup
5. **Mock external services** - Reliable, fast tests
6. **Test edge cases** - Empty inputs, null values, errors
7. **Keep tests independent** - No shared state between tests

### DON'T ❌

1. **Don't mix unit and integration tests** - Keep them separate
2. **Don't test implementation details** - Test behavior, not internals
3. **Don't use real secrets in tests** - Use test-specific secrets
4. **Don't skip test cleanup** - Always clean up resources
5. **Don't write flaky tests** - Tests should be deterministic
6. **Don't test third-party libraries** - Trust they work
7. **Don't commit commented-out tests** - Delete or fix them

## JWT Token Security

### Test Environment Secret

**IMPORTANT**: Tests must use a dedicated JWT secret:

```python
@pytest.fixture(autouse=True)
def test_jwt_secret():
    """Ensure test environment uses dedicated JWT secret"""
    os.environ['JWT_SECRET'] = 'test-secret-do-not-use-in-production'
    yield
```

### Token Usage

- **Unit Tests**: Use `mock_jwt_required` fixture
- **Integration Tests**: Use `auth_headers` fixture with real tokens
- **Never**: Hardcode JWT secrets in test files

## Migration Guide

### Moving Existing Tests

1. **Identify test type**:
   - Uses mocks? → `tests/unit/`
   - Uses real Flask app? → `tests/integration/`
   - Tests full workflow? → `tests/integration/e2e/`

2. **Move test file**:
   ```bash
   mv tests/test_vectors.py tests/integration/routes/test_vectors_integration.py
   ```

3. **Update imports**:
   ```python
   # Add fixtures import
   from tests.fixtures.auth import auth_headers
   ```

4. **Add test marker**:
   ```python
   @pytest.mark.integration
   def test_vector_search(client, auth_headers):
       ...
   ```

## Troubleshooting

### Tests fail with "JWT secret not set"
- Ensure `test_jwt_secret` fixture is imported
- Check `tests/fixtures/auth.py` is in PYTHONPATH

### Tests are slow
- Check if unit tests are using real dependencies
- Use `pytest -n auto` for parallel execution
- Profile with `pytest --durations=10`

### Tests are flaky
- Check for shared state between tests
- Ensure proper cleanup in fixtures
- Use `pytest --lf` to run last failed tests

## References

- **RFC #619**: Testing Architecture Strategy
- **pytest Documentation**: https://docs.pytest.org/
- **Flask Testing**: https://flask.palletsprojects.com/en/latest/testing/
- **Coverage.py**: https://coverage.readthedocs.io/

---

**Last Updated**: 2025-10-31  
**Status**: ✅ Active  
**Owner**: CTO (Devin)
