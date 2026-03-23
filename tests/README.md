# ShelfAware Unit Tests

This directory contains unit tests for the ShelfAware application, focusing on the book CRUD operations and related functionality.

## Test Structure

### `test_book_crud.py`
Unit tests for book CRUD operations:
- **TestBookService**: Tests for the `BookService` class methods
  - `get_books()` - with and without limits
  - `get_book()` - found and not found cases
  - `add_book()` - successful creation
  - `update_book()` - full and partial updates, not found cases
  - `delete_book()` - successful deletion and not found cases

- **TestBookSchemas**: Tests for Pydantic schemas
  - `BookCreate` - valid and minimal data
  - `BookUpdate` - all fields and partial updates
  - `BookRead` - creation from SQLAlchemy models

### `test_book_routes.py`
Integration tests for book API routes (requires full FastAPI app):
- **TestBookRoutes**: Tests for all CRUD endpoints
  - GET `/books` - list all books
  - GET `/books/{book_id}` - get specific book
  - POST `/books` - create new book (admin only)
  - PUT `/books/{book_id}` - update book (admin only)
  - DELETE `/books/{book_id}` - delete book (admin only)

- **TestBookRoutesValidation**: Input validation tests
  - Invalid data handling
  - Required field validation

### `test_recommendation_engine.py`
Existing tests for the recommendation engine functionality.

## Running Tests

### Run All Unit Tests
```bash
python run_tests.py
```

This will run:
1. Unit tests for BookService and schemas
2. Recommendation engine tests
3. Route integration tests (if FastAPI app can be imported)

### Run Specific Test Files
```bash
# Run only book CRUD unit tests
python -m unittest tests.test_book_crud

# Run only book route tests
python -m unittest tests.test_book_routes

# Run all tests in verbose mode
python -m unittest discover -v
```

### Run Individual Test Classes
```bash
# Run only BookService tests
python -m unittest tests.test_book_crud.TestBookService

# Run only schema tests
python -m unittest tests.test_book_crud.TestBookSchemas
```

## Test Coverage

The tests cover:

### Book CRUD Operations
- ✅ Create books with all fields
- ✅ Create books with minimal required fields
- ✅ Read single books (found/not found)
- ✅ Read all books (with/without limits)
- ✅ Update books (full and partial updates)
- ✅ Delete books (success/failure cases)
- ✅ Input validation and error handling

### API Routes
- ✅ All HTTP methods (GET, POST, PUT, DELETE)
- ✅ Status codes (200, 201, 404, 422)
- ✅ Admin role requirements
- ✅ JSON request/response handling
- ✅ Error responses

### Data Validation
- ✅ Pydantic schema validation
- ✅ Required vs optional fields
- ✅ Data type validation
- ✅ SQLAlchemy model conversion

## Test Dependencies

The tests use:
- `unittest` - Python's built-in testing framework
- `unittest.mock` - For mocking dependencies
- `fastapi.testclient` - For API route testing (optional)

## Mocking Strategy

- **Database**: All database operations are mocked using `MagicMock`
- **Services**: Service dependencies are mocked to isolate unit tests
- **External APIs**: OpenAI, AWS Cognito calls are mocked
- **Authentication**: Admin role checks are mocked

## Adding New Tests

When adding new tests:

1. **Unit Tests**: Mock all external dependencies (database, services, APIs)
2. **Integration Tests**: Test actual API endpoints with mocked services
3. **Edge Cases**: Test error conditions, boundary values, and invalid inputs
4. **Naming**: Use descriptive test method names (e.g., `test_get_book_not_found`)

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements.txt
    python run_tests.py
```

## Test Data

Tests use realistic but fake data:
- Book IDs: UUID format strings
- Titles: Descriptive strings
- Dates: Valid date objects
- URLs: Valid HTTP URLs
- Page counts: Reasonable integers

All test data is self-contained and doesn't rely on external systems.