# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Issues Fixed

1. Package import issues:
   - Installed package in development mode: `pip install -e .`
   - Created `setup.py` for package structure
   - Added `conftest.py` to handle module imports

2. Environment configuration:
   - Created `.env.test` for test environment
   - Added auto-loading of test environment in conftest.py
   - Set test API keys for OpenAI and Perplexity
   
3. Dependencies:
   - Installed missing dependencies like email-validator
   - Added test directories to prevent file IO errors

4. Test API endpoints:
   - Added test endpoints to main.py for testing routes
   - Created missing router files (status.py, users.py)
   - Skipped tests that require real OpenAI API key

5. Test mocking:
   - Added proper mocks for image generation tests
   - Fixed pytest asyncio configuration to silence warnings

## Commands

- Run application: `python main.py`
- Run all tests: `pytest`
- Run a specific test: `pytest tests/test_specific_file.py::TestClass::test_function -v`
- Run test with higher verbosity: `pytest -vv`
- Run a single conversion test: `python test_markdown_conversion.py`
- Check test coverage: `pytest --cov=src --cov-report=term-missing`

## Environment Setup

- Create virtual environment: `python -m venv venv`
- Activate environment:
  - Linux/macOS: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`
- Install package in editable mode: `pip install -e .`
- Create environment file:
  - Development: `cp .env.example .env.local` (then edit with your API keys)
  - Testing: `cp .env.example .env.test` (uses test API keys)

## Code Style Guidelines

- **Imports**: Group standard library, then third-party, then local imports with a blank line between groups
- **Typing**: Use type hints with all function parameters and return values
- **Naming**: Use snake_case for variables/functions and PascalCase for classes
- **Docstrings**: Use Google-style docstrings with Args/Returns sections
- **Error handling**: Use try/except blocks with specific exceptions and error logging
- **Async**: Use asyncio for asynchronous operations with proper await syntax
- **Logging**: Use the built-in logging module at appropriate levels (INFO, DEBUG, ERROR)
- **Environment**: Load environment variables from .env.local file using dotenv
- **Models**: Default to "gpt-4o-mini" with temperature 0.3 for general agent tasks
- **Concurrency**: Limit concurrent operations using asyncio semaphores when appropriate