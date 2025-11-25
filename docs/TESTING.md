# Testing Guide for Jarvis Personal Secretary

This document explains how to verify that all functions are working correctly after code changes.

## Quick Start

After making any code changes, run the test suite to verify everything still works:

```bash
python scripts/run_tests.py
```

Or use pytest directly:

```bash
python -m pytest tests/
```

## Test Suite Overview

The test suite includes comprehensive tests for all core components:

### Test Files

- **`tests/test_config.py`** - Tests configuration loading and constants
- **`tests/test_storage.py`** - Tests conversation storage and persistence
- **`tests/test_openai_client.py`** - Tests OpenAI API client (mocked)
- **`tests/test_conversation_manager.py`** - Tests conversation management logic
- **`tests/test_flask_routes.py`** - Tests Flask web routes
- **`tests/test_calendar_provider.py`** - Tests Google Calendar integration (mocked)

### Test Coverage

The suite includes **42 tests** covering:
- ✅ Configuration management
- ✅ Storage operations (create, read, update)
- ✅ Message validation
- ✅ API client error handling
- ✅ Conversation flow
- ✅ Flask route handlers
- ✅ Calendar provider authentication and API calls

## Running Tests

### Basic Test Run

```bash
python scripts/run_tests.py
```

### Verbose Output

To see detailed test information:

```bash
python scripts/run_tests.py --verbose
```

### With Coverage Report

To see code coverage:

```bash
python scripts/run_tests.py --coverage
```

### Run Specific Test

To run a specific test file:

```bash
python scripts/run_tests.py --test tests/test_storage.py
```

To run a specific test function:

```bash
python scripts/run_tests.py --test tests/test_storage.py::TestConversationStorage::test_add_message_to_existing_session
```

### Using pytest Directly

You can also use pytest directly with various options:

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_storage.py

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run and stop at first failure
python -m pytest tests/ -x

# Run only failed tests from last run
python -m pytest tests/ --lf
```

## Test Structure

Tests use the `pytest` framework with mocking to avoid:
- Making real API calls to OpenAI
- Requiring actual Google Calendar credentials
- Modifying production data files

All external dependencies are mocked using `unittest.mock` and `pytest-mock`.

## Continuous Testing

### Recommended Workflow

1. **Before committing changes**: Run the full test suite
   ```bash
   python scripts/run_tests.py
   ```

2. **After making changes to a specific module**: Run tests for that module
   ```bash
   python scripts/run_tests.py --test tests/test_storage.py
   ```

3. **Before deploying**: Run with coverage to ensure all code is tested
   ```bash
   python scripts/run_tests.py --coverage
   ```

## Troubleshooting

### Tests Fail After Code Changes

1. Read the error message carefully - it will show which test failed and why
2. Check if your changes broke existing functionality
3. Review the test to understand what it's verifying
4. Fix the code or update the test if the behavior change was intentional

### Import Errors

If you see import errors:
```bash
# Make sure you're in the project root directory
cd "C:\Users\omert\Desktop\Jarvis - personal secretery"

# Install test dependencies
python -m pip install -r requirements.txt
```

### Module Not Found

If tests can't find modules:
- Ensure you're running from the project root
- Check that `src/` directory exists and has `__init__.py` files
- Verify Python path includes the project directory

## Adding New Tests

When adding new features, add corresponding tests:

1. Create or update test file in `tests/` directory
2. Follow naming convention: `test_<module_name>.py`
3. Use descriptive test names: `test_<functionality>_<expected_behavior>`
4. Mock external dependencies (APIs, file system, etc.)
5. Run tests to ensure they pass

Example test structure:

```python
class TestNewFeature:
    """Test new feature functionality"""
    
    def test_feature_basic_functionality(self):
        """Test basic feature works"""
        # Arrange
        # Act
        # Assert
        pass
```

## Test Maintenance

- Keep tests up to date with code changes
- Remove or update obsolete tests
- Add tests for bug fixes to prevent regressions
- Aim for high code coverage (80%+ is good)

## CI/CD Integration

For automated testing in CI/CD pipelines:

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v --tb=short

# Or use the test runner
python scripts/run_tests.py
```

