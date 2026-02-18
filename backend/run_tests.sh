#!/bin/bash
# Run backend tests with coverage

set -e

echo "=================================================="
echo "Backend Test Runner"
echo "=================================================="
echo ""

# Check if in backend directory
if [ ! -f "pytest.ini" ]; then
    echo "❌ Error: Must be run from backend directory"
    echo "   cd backend && ./run_tests.sh"
    exit 1
fi

# Check if test dependencies are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install -r requirements-test.txt
    echo "✅ Test dependencies installed"
    echo ""
fi

# Parse arguments
TEST_PATH="${1:-tests/}"
COVERAGE_MIN="${2:-80}"

echo "🧪 Running tests from: $TEST_PATH"
echo "📊 Minimum coverage: $COVERAGE_MIN%"
echo ""

# Run tests
echo "=================================================="
echo "Executing Tests"
echo "=================================================="
python -m pytest "$TEST_PATH" \
    --verbose \
    --cov=app/services \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under="$COVERAGE_MIN" \
    --log-cli-level=INFO

TEST_EXIT_CODE=$?

echo ""
echo "=================================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Coverage report: htmlcov/index.html"
else
    echo "❌ Tests failed"
fi
echo "=================================================="

exit $TEST_EXIT_CODE
