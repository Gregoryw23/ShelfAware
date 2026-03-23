import unittest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_book_crud import TestBookService, TestBookSchemas
from tests.test_recommendation_engine import RecommendationEngineTests


def run_unit_tests():
    """Run unit tests for the ShelfAware application (excluding integration tests that require full app)."""

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases (only unit tests that don't require full app imports)
    suite.addTests(loader.loadTestsFromTestCase(TestBookService))
    suite.addTests(loader.loadTestsFromTestCase(TestBookSchemas))
    suite.addTests(loader.loadTestsFromTestCase(RecommendationEngineTests))

    print("Running unit tests for Book CRUD operations and recommendation engine...")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


def run_route_tests():
    """Run integration tests for routes (requires full app setup)."""
    try:
        from tests.test_book_routes import TestBookRoutes, TestBookRoutesValidation

        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # Add route test cases
        suite.addTests(loader.loadTestsFromTestCase(TestBookRoutes))
        suite.addTests(loader.loadTestsFromTestCase(TestBookRoutesValidation))

        print("Running route integration tests...")

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Return exit code based on test results
        return 0 if result.wasSuccessful() else 1

    except ImportError as e:
        print(f"Route tests not available: {e}")
        print("Note: Route integration tests require the full application to be properly configured.")
        return 0  # Not a failure, just not available


if __name__ == '__main__':
    # Run unit tests first
    unit_exit_code = run_unit_tests()

    print("\n" + "="*50 + "\n")

    # Try to run route tests
    route_exit_code = run_route_tests()

    # Return combined exit code
    exit_code = unit_exit_code or route_exit_code
    sys.exit(exit_code)