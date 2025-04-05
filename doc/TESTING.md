# Testing Guide

## Overview

This document outlines the testing approach for the AI Document Generator project. It covers test organization, running tests, and writing new tests.

## Test Organization

Tests are organized into the following categories:

1. **Unit Tests**: Test individual components in isolation
   - Located in the `/tests/` directory
   - Named with pattern `test_*.py`
   - Focus on a single class or function

2. **Integration Tests**: Test interactions between components
   - Located in the root directory
   - Files like `test_markdown_conversion.py`, `test_report_generation.py`
   - Test multiple components working together

3. **End-to-End Tests**: Test complete workflows
   - Located in the root directory
   - Named with pattern `test_e2e_*.py`
   - Simulate actual user workflows

## Running Tests

### Prerequisites

- Python 3.10 or higher
- Virtual environment with dependencies installed
- API keys set in `.env.local`

### Running All Tests

```bash
pytest
```

### Running Specific Tests

Test a specific file:
```bash
pytest tests/test_image_generation.py
```

Test a specific test case:
```bash
pytest tests/test_image_generation.py::TestImageGeneration::test_generate_single_image
```

Test with higher verbosity:
```bash
pytest -vv
```

Test with print statement output:
```bash
pytest -s
```

### Using Markers

The project uses pytest markers to categorize tests. For example, to run only async tests:

```bash
pytest -m asyncio
```

Available markers are defined in `pytest.ini`.

## Writing New Tests

### Test Structure

Tests follow this general structure:

```python
import unittest

class TestComponentName(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup run once before all tests
        pass
        
    def setUp(self):
        # Setup run before each test
        pass
        
    def test_specific_functionality(self):
        # Test a specific aspect of the component
        pass
        
    def tearDown(self):
        # Cleanup after each test
        pass
        
    @classmethod
    def tearDownClass(cls):
        # Cleanup run once after all tests
        pass
```

### Asynchronous Tests

For testing async code, use the `asyncio` marker and `async`/`await`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

Alternatively, use `unittest` with the async event loop:

```python
import asyncio
import unittest

class TestAsyncComponent(unittest.TestCase):
    
    async def test_async_method(self):
        result = await async_method()
        self.assertEqual(result, expected_value)
        
    def test_async_wrapper(self):
        result = asyncio.run(self.test_async_method())
```

### Mocking External Services

Use `unittest.mock` to mock external API calls:

```python
from unittest.mock import patch, MagicMock

@patch('openai.OpenAI')
def test_with_mocked_openai(mock_openai):
    # Configure the mock
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.images.generate.return_value = mock_response
    
    # Test code that uses OpenAI
    result = component_using_openai()
    
    # Assertions
    assert mock_client.images.generate.called
    assert result == expected_value
```

### Test Data Fixtures

Create fixtures for reusable test data:

```python
import pytest

@pytest.fixture
def sample_report_structure():
    return ReportStructure(
        title="Test Report",
        sections=[
            ReportSection(
                title="Test Section",
                content="Test content"
            )
        ],
        metadata={"template_type": "standard"}
    )
```

## Test Coverage

To check test coverage, install pytest-cov and run:

```bash
pytest --cov=src --cov-report=term-missing
```

## Continuous Integration

Tests automatically run in CI via GitHub Actions. For faster local iteration, you can also run:

```bash
python test_markdown_conversion.py
```

This runs a specific test directly, which is faster but doesn't use the pytest framework.