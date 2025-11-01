#!/bin/bash

# OMNI Intelligence Platform Smoke Test Runner
# Quick smoke test for the new OMNI platform implementation

set -e

echo ""
echo "🚀 OMNI Intelligence Platform - Quick Smoke Test"
echo "================================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Check if backend is running
echo "📡 Checking if backend is running on port 8080..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ Backend is running"
else
    echo "⚠️  Backend not detected on localhost:8080"
    echo "   Start backend with: cd backend && python3 -m uvicorn main:app --port 8080"
    echo ""
fi

# Check if frontend is running
echo "🌐 Checking if frontend is running on port 8000..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Frontend is running"
else
    echo "⚠️  Frontend not detected on localhost:8000"
    echo "   Start frontend with: cd frontend && python3 -m http.server 8000"
    echo ""
fi

# Install test dependencies
echo ""
echo "📦 Installing test dependencies..."
pip3 install -q requests 2>/dev/null || true

# Run the smoke tests
echo ""
echo "🧪 Running smoke tests..."
echo ""

python3 test_omni_platform.py "$@"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Smoke tests completed successfully!"
else
    echo "❌ Some smoke tests failed. Check the output above."
fi

exit $exit_code
