#!/bin/bash

# OMNI Platform Google Cloud Smoke Test Runner (Linux/Unix Shell)
# Comprehensive smoke test execution script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

echo ""
echo "🔥 OMNI Platform Google Cloud Smoke Test Suite"
echo "=============================================="
echo "Testing Google Cloud Run, Vertex AI, Gemini, and entire platform"
echo ""

# Set environment variables
export PYTHONPATH="$(pwd)"
export VERTEX_AI_API_KEY="AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ"
export GOOGLE_CLOUD_PROJECT="refined-graph-471712-n9"
export GOOGLE_CLOUD_REGION="europe-west1"
export PLATFORM_URL="http://34.140.18.254:8080"

log_info "Environment configured:"
echo "  Project: $GOOGLE_CLOUD_PROJECT"
echo "  Region: $GOOGLE_CLOUD_REGION"
echo "  Platform URL: $PLATFORM_URL"
echo ""

# Check Python installation
if ! command -v python &> /dev/null; then
    log_error "Python is not installed or not in PATH"
    log_info "Please install Python 3.8 or higher"
    exit 1
fi

log_info "Python version:"
python --version
echo ""

# Install required packages
log_info "Installing required packages..."
if pip install -r requirements-smoke-test.txt; then
    log_success "Packages installed successfully"
else
    log_warning "Failed to install some packages, continuing anyway..."
fi

echo ""
log_info "Starting smoke tests..."
echo ""

# Function to run test with error handling
run_test() {
    local test_name="$1"
    local test_script="$2"
    local test_number="$3"
    local total_tests="$4"

    log_info "[$test_number/$total_tests] Running $test_name..."
    echo "  Description: Testing $(echo "$test_name" | sed 's/ Tests//')"

    if python "$test_script"; then
        log_success "$test_name completed successfully"
        return 0
    else
        log_warning "$test_name failed, continuing with other tests..."
        return 1
    fi
}

# Run main smoke test
run_test "Main Smoke Test" "omni_smoke_test.py" "1" "4"

# Run Cloud Run tests
echo ""
run_test "Cloud Run Tests" "omni_cloudrun_test.py" "2" "4"

# Run Vertex AI tests
echo ""
run_test "Vertex AI Tests" "omni_vertex_gemini_test.py" "3" "4"

# Run unified test runner
echo ""
log_info "[4/4] Running unified test runner with report generation..."
if python omni_smoke_test_runner.py --verbose; then
    TEST_EXIT_CODE=0
    log_success "Unified test runner completed successfully"
else
    TEST_EXIT_CODE=1
    log_warning "Unified test runner failed"
fi

echo ""
echo "=============================================="
echo "SMOKE TEST EXECUTION COMPLETED"
echo "=============================================="
echo ""

# Check if any tests failed
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "All smoke tests passed! ✅"
    echo "🎉 Platform is ready for production deployment."
else
    log_warning "Some smoke tests failed! ⚠️"
    echo "🔍 Check the generated report files for details."
    echo "🔧 Review logs and fix issues before production deployment."
fi

echo ""
log_info "Generated files:"
if ls -t omni_smoke_test*.txt omni_smoke_test*.json omni_smoke_test*.html 2>/dev/null | head -5; then
    ls -t omni_smoke_test*.txt omni_smoke_test*.json omni_smoke_test*.html 2>/dev/null | head -5
else
    echo "  No report files found"
fi

echo ""

# Try to open latest HTML report if available (Linux)
LATEST_HTML=$(ls -t omni_smoke_test_report_*.html 2>/dev/null | head -1)
if [ -n "$LATEST_HTML" ] && [ -f "$LATEST_HTML" ]; then
    log_info "Opening latest HTML report in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "$LATEST_HTML" 2>/dev/null &
        log_success "HTML report opened in browser"
    elif command -v open &> /dev/null; then
        open "$LATEST_HTML" 2>/dev/null &
        log_success "HTML report opened in browser"
    else
        log_warning "Could not open browser automatically"
        echo "  Open manually: $LATEST_HTML"
    fi
else
    log_info "No HTML report found to open in browser."
fi

echo ""
log_info "Test logs and reports are available in the current directory."
log_info "Check individual test script outputs for detailed results."
echo ""

# Exit with appropriate code
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "Exiting with success code."
    exit 0
else
    log_warning "Exiting with failure code."
    exit 1
fi