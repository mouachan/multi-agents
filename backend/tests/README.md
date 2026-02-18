# Backend Tests

Comprehensive test suite for the backend services with focus on:
- **Persistence**: All database operations tested
- **Logging**: All critical steps logged and verified
- **Integration**: End-to-end workflows tested

## Structure

```
tests/
├── conftest.py                        # Fixtures and test configuration
├── test_services/                     # Unit tests for services
│   ├── test_context_builder.py       # Context building tests
│   ├── test_response_parser.py       # Response parsing tests
│   ├── test_orchestrator.py          # Agent orchestration tests (to be added)
│   ├── test_reviewer.py              # Review service tests (to be added)
│   └── test_claim_service.py         # Claim service tests with persistence
└── test_integration/                  # Integration tests
    └── test_claim_workflow_e2e.py     # End-to-end workflow tests
```

## Running Tests

### All tests
```bash
cd backend
pytest
```

### Unit tests only
```bash
pytest tests/test_services/
```

### Integration tests only
```bash
pytest tests/test_integration/
```

### With coverage report
```bash
pytest --cov=app/services --cov-report=html
# Open htmlcov/index.html to view coverage
```

### Specific test file
```bash
pytest tests/test_services/test_claim_service.py
```

### Specific test
```bash
pytest tests/test_services/test_claim_service.py::TestClaimService::test_save_decision_persistence
```

### Verbose output with logging
```bash
pytest -v -s --log-cli-level=DEBUG
```

## Test Features

### Database Persistence Testing
All tests verify:
- ✅ INSERT operations persist data
- ✅ UPDATE operations modify correctly
- ✅ SELECT operations retrieve accurate data
- ✅ Transaction rollback on errors
- ✅ Data integrity across tables

### Logging Verification
All tests check:
- ✅ Critical steps are logged
- ✅ Error conditions are logged
- ✅ Log levels are appropriate
- ✅ Log messages contain relevant information

### Coverage
Minimum coverage threshold: **80%**

Run coverage report:
```bash
pytest --cov=app/services --cov-report=term-missing
```

## Fixtures

### Database Fixtures
- `db_session`: Clean database session for each test
- `test_claim`: Sample claim in database
- `test_claim_with_document`: Claim with OCR document
- `test_claim_with_decision`: Claim with decision

### Mock Fixtures
- `mock_llamastack_response`: Mocked agent response
- `mock_agent_config`: Mocked agent configuration

### Logging Fixtures
- `capture_logs`: Capture and verify log output
- `assert_logged`: Helper to assert log messages

## Writing New Tests

### Unit Test Template
```python
import pytest
from app.services.your_service import YourService

class TestYourService:
    @pytest.fixture
    def service(self):
        return YourService()

    @pytest.mark.asyncio
    async def test_your_feature(self, service, db_session, capture_logs):
        # Test implementation
        result = await service.do_something(db_session)

        # Assert result
        assert result is not None

        # Verify persistence
        # ... query database to verify

        # Verify logging
        assert any("expected log" in r.message for r in capture_logs.records)
```

### Integration Test Template
```python
import pytest
from sqlalchemy import select
from app.models.claim import Claim

class TestIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, db_session, capture_logs):
        # Step 1: Setup
        # ...

        # Step 2: Execute workflow
        # ...

        # Step 3: Verify persistence
        result = await db_session.execute(select(Claim).where(...))
        claim = result.scalar_one()
        assert claim.status == expected_status

        # Step 4: Verify logging
        log_messages = [r.message for r in capture_logs.records]
        assert any("workflow completed" in msg for msg in log_messages)
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt -r requirements-test.txt
    pytest --cov=app/services --cov-report=xml
```

## Troubleshooting

### ImportError
Make sure you're in the backend directory:
```bash
cd backend
export PYTHONPATH=.
pytest
```

### Database errors
Tests use in-memory SQLite. If you see database errors, check:
- SQLAlchemy models are imported in conftest.py
- Async session fixtures are correctly configured

### Async errors
Make sure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Database Cleanup**: Use fixtures that rollback after each test
3. **Mock External Services**: Always mock LlamaStack API calls
4. **Verify Persistence**: Query database to confirm data is saved
5. **Verify Logging**: Check that important steps are logged
6. **Clear Assertions**: Use descriptive assertion messages
7. **Coverage**: Aim for >80% code coverage
