# TMS PRD Alignment Validation Test Suite

This comprehensive test suite ensures strict compatibility and data integrity across all Transportation Management System (TMS) components by validating data models, APIs, databases, and event schemas against Product Requirements Documents (PRDs).

## Overview

The test suite implements rigorous Pydantic-based validation to prevent breaking deviations and maintain seamless integration across:

- **Domain Models**: Core business entities (loads, vehicles, drivers, routes)
- **API Schemas**: Request/response models for all API endpoints
- **Event Schemas**: Kafka event payloads and messaging contracts
- **Database Schemas**: PostgreSQL, TimescaleDB, PostGIS, and Neo4j constraints
- **Cross-Layer Compatibility**: Data consistency between all system layers

## Test Structure

```
server/app/tests/
├── __init__.py                  # Package initialization
├── conftest.py                  # Pytest fixtures and shared configuration
├── pytest.ini                  # Pytest configuration
├── test_requirements.txt        # Test-specific dependencies
├── run_tests.py                # Comprehensive test runner script
├── README.md                   # This documentation
│
├── test_prd_alignment.py       # Core PRD alignment validation tests
├── test_schema_validation.py   # Database schema validation tests
├── test_api_compatibility.py   # API compatibility validation tests
│
└── test_results.json          # Generated test results (after running)
```

## Test Categories

### 1. PRD Alignment Tests (`test_prd_alignment.py`)

Validates that all Pydantic models strictly align with PRD specifications:

- **Domain Model Validation**: Field presence, types, enums, constraints
- **Event Model Validation**: Event types, payload structures, metadata
- **API Model Validation**: Request/response schemas, field requirements
- **Enum Completeness**: All PRD enumerations are fully implemented
- **Business Logic Rules**: Pickup/delivery times, capacity limits, HOS constraints
- **Schema Evolution**: Version compatibility and backward compatibility

### 2. Schema Validation Tests (`test_schema_validation.py`)

Ensures database schema alignment with Pydantic models:

- **PostgreSQL Validation**: Table structures, constraints, data types
- **TimescaleDB Validation**: Hypertables, time-series constraints
- **PostGIS Validation**: Spatial data types, coordinate validation
- **Neo4j Validation**: Graph relationships, node properties
- **Enum Synchronization**: Database enums match Pydantic enums
- **Constraint Validation**: Business rules enforced at database level

### 3. API Compatibility Tests (`test_api_compatibility.py`)

Validates API request/response models and endpoint compatibility:

- **Request Model Validation**: All API inputs validate correctly
- **Response Model Validation**: All API outputs match schemas
- **Event API Compatibility**: Event publishing/consuming schemas
- **Cross-Layer Consistency**: API, domain, and event model alignment
- **Serialization Testing**: JSON serialization/deserialization
- **Error Response Validation**: Error schemas and status codes

## Quick Start

### Installation

1. **Install test dependencies:**
   ```bash
   cd server/app/tests
   pip install -r test_requirements.txt
   ```

2. **Or use the automated installer:**
   ```bash
   python run_tests.py --install-deps
   ```

### Running Tests

#### Basic Usage

```bash
# Run all validation tests
python run_tests.py

# Run specific test suite
python run_tests.py --suite prd
python run_tests.py --suite schema
python run_tests.py --suite api

# Run with coverage reporting
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose
```

#### Advanced Usage

```bash
# Run all tests including integration tests
python run_tests.py --integration

# Run smoke tests only (quick validation)
python run_tests.py --suite smoke

# Run with custom output file
python run_tests.py --output custom_results.json

# Install dependencies and run all tests with coverage
python run_tests.py --install-deps --coverage --verbose
```

#### Direct Pytest Usage

```bash
# Run specific test markers
pytest -m prd_alignment
pytest -m database_schema
pytest -m api_compatibility

# Run specific test files
pytest test_prd_alignment.py -v
pytest test_schema_validation.py --tb=short

# Run with coverage
pytest --cov=server/app/models --cov-report=html
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

The test suite includes comprehensive pytest configuration:

- **Test Discovery**: Automatic test file and function detection
- **Markers**: Organized test categorization and filtering
- **Output Settings**: Verbose reporting with useful error information
- **Coverage Integration**: Built-in coverage reporting support
- **Warning Filters**: Clean test output without noise

### Fixtures (`conftest.py`)

Shared fixtures provide consistent test data:

- **Sample Entities**: Pre-configured domain objects for testing
- **PRD Reference Data**: Complete enum values and constraints from PRDs
- **Test Cases**: Coordinate validation, business logic scenarios
- **Mock Services**: External API responses and database connections
- **Environment Setup**: Test database URLs and service configurations

## Key Features

### Strict Validation

- **No Fallback Data**: Tests fail if any deviation from PRD is detected
- **Type Enforcement**: Strict Pydantic validation with proper error handling
- **Comprehensive Coverage**: All fields, enums, and constraints validated
- **Schema Evolution**: Backward compatibility and versioning support

### Real-World Testing

- **Realistic Data**: Tests use authentic transportation industry data
- **Geographic Validation**: Proper latitude/longitude coordinate testing
- **Time Zone Awareness**: Datetime validation with timezone handling
- **Business Logic**: DOT regulations, HOS rules, capacity constraints

### CI/CD Integration

- **Automated Execution**: Ready for continuous integration pipelines
- **Structured Output**: JSON results for automated processing
- **Exit Codes**: Proper success/failure reporting for CI systems
- **Performance Tracking**: Test execution time monitoring

## Integration with External Services

### Database Testing

For full database integration testing:

```bash
# Set test database URL
export TEST_DATABASE_URL="postgresql://test:test@localhost/tms_test"

# Run schema validation tests
python run_tests.py --suite schema --integration
```

### Event Streaming Testing

For Kafka event testing:

```bash
# Set test Kafka configuration
export TEST_KAFKA_SERVERS="localhost:9092"

# Run event validation tests
pytest -m event_validation --integration
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: TMS PRD Alignment Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd server/app/tests
          pip install -r test_requirements.txt
      
      - name: Run PRD alignment tests
        run: |
          cd server/app/tests
          python run_tests.py --coverage --output ci_results.json
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tms-prd-alignment
        name: TMS PRD Alignment Tests
        entry: python server/app/tests/run_tests.py --suite smoke
        language: system
        pass_filenames: false
```

## Test Results and Reporting

### JSON Output Format

```json
{
  "timestamp": "2025-01-08T10:30:00Z",
  "results": [
    {
      "suite": "prd_alignment",
      "passed": true,
      "returncode": 0,
      "stdout": "...test output...",
      "stderr": ""
    }
  ],
  "summary": {
    "total_suites": 4,
    "passed_suites": 4,
    "failed_suites": 0
  }
}
```

### HTML Coverage Reports

When running with `--coverage`, detailed HTML reports are generated:

- **Line Coverage**: Shows which code lines are tested
- **Branch Coverage**: Identifies untested code paths
- **Function Coverage**: Reports on function-level testing
- **Missing Lines**: Highlights code that needs test coverage

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the correct directory
   cd server/app/tests
   
   # Check Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../.."
   ```

2. **Missing Dependencies**
   ```bash
   # Install all test requirements
   pip install -r test_requirements.txt
   
   # Or use the automated installer
   python run_tests.py --install-deps
   ```

3. **Database Connection Issues**
   ```bash
   # Skip integration tests if databases aren't available
   python run_tests.py --suite all
   
   # Or run only unit tests
   pytest -m "not integration"
   ```

### Debugging Test Failures

```bash
# Run with maximum verbosity
python run_tests.py --verbose

# Run specific failing test
pytest test_prd_alignment.py::test_load_model_validation -vvv

# Run with detailed traceback
pytest --tb=long

# Run with pdb debugger
pytest --pdb
```

## Contributing

### Adding New Tests

1. **Domain Model Tests**: Add to `test_prd_alignment.py`
2. **Database Schema Tests**: Add to `test_schema_validation.py`  
3. **API Tests**: Add to `test_api_compatibility.py`
4. **New Fixtures**: Add to `conftest.py`

### Test Naming Conventions

- `test_<component>_<functionality>_<condition>`
- Example: `test_load_model_validation_required_fields`
- Use descriptive names that explain what is being tested

### Marking New Tests

```python
import pytest

@pytest.mark.prd_alignment
def test_new_domain_model():
    """Test new domain model against PRD"""
    pass

@pytest.mark.database_schema
def test_new_database_constraint():
    """Test new database constraint"""
    pass
```

## Support

For questions or issues with the test suite:

1. Check this README for common solutions
2. Review test output and error messages
3. Run tests with `--verbose` for detailed information
4. Check that all dependencies are installed correctly
5. Verify that PRD documents are up to date

## License

This test suite is part of the TMS project and follows the same licensing terms.
