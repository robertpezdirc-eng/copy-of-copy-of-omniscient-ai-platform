#!/bin/bash

# Bash script for automated sequential building of all Omni modules
# Compatible with Linux, macOS, and WSL

set -e  # Exit on any error

echo "🔧 OMNI Platform - Automated Sequential Build"
echo "============================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Check if we're in the right directory
if [ ! -f "omni_build_manager.py" ]; then
    print_error "omni_build_manager.py not found. Are you in the correct directory?"
    exit 1
fi

# Activate virtual environment
VENV_PATH="OMNIBOT13/.venv/bin/activate"

if [ -f "$VENV_PATH" ]; then
    print_status "Activating virtual environment..."
    source "$VENV_PATH"
    print_success "Virtual environment activated"
else
    print_warning "Virtual environment not found at $VENV_PATH"
    print_status "Continuing without virtual environment..."
fi

# Path to state file
STATE_FILE="omni_build_state.json"

# Initialize state if it doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    print_status "Initializing build state..."

    cat > "$STATE_FILE" << 'EOL'
{
  "modules": [
    {"name":"omni-platform-v1.0.0","status":"pending","age":0,"last_build":null},
    {"name":"omni-desktop-v1.0.0","status":"pending","age":0,"last_build":null},
    {"name":"omni-frontend-v1.0.0","status":"pending","age":0,"last_build":null}
  ],
  "last_updated": null
}
EOL

    print_success "Build state initialized"
fi

# Load current state
print_status "Loading build state..."
MODULES=$(jq -c '.modules[]' "$STATE_FILE")

if [ -z "$MODULES" ]; then
    print_error "No modules found in state file"
    exit 1
fi

print_status "Starting sequential build of all Omni modules..."
echo "=================================================="

# Build each module sequentially
BUILT_COUNT=0
TOTAL_COUNT=0

for module_json in $MODULES; do
    TOTAL_COUNT=$((TOTAL_COUNT + 1))

    # Extract module information
    MODULE_NAME=$(echo "$module_json" | jq -r '.name')
    MODULE_STATUS=$(echo "$module_json" | jq -r '.status')

    print_status "Processing module: $MODULE_NAME (Status: $MODULE_STATUS)"

    if [ "$MODULE_STATUS" != "built" ]; then
        print_status "Building module: $MODULE_NAME"
        echo "--------------------------------"

        # Run build command for specific module
        if ! python build_module.py --module "$MODULE_NAME"; then
            print_error "Build failed for module: $MODULE_NAME"
            echo "Continuing with next module..."
            continue
        fi

        # Update module status in state file
        jq --arg name "$MODULE_NAME" \
           --arg timestamp "$(date -Iseconds)" \
           '(.modules[] | select(.name==$name) | .status)="built" | (.modules[] | select(.name==$name) | .last_build)=$timestamp' \
           "$STATE_FILE" > temp_state.json && mv temp_state.json "$STATE_FILE"

        print_success "Module $MODULE_NAME built successfully"
        BUILT_COUNT=$((BUILT_COUNT + 1))

    else
        print_status "Module $MODULE_NAME already built, skipping..."
    fi

    echo ""
done

# Final status check
print_status "Build completion summary:"
echo "=================================================="
print_status "Total modules: $TOTAL_COUNT"
print_success "Successfully built: $BUILT_COUNT"
COMPLETION_RATE=$((BUILT_COUNT * 100 / TOTAL_COUNT))
print_status "Build completion rate: $COMPLETION_RATE%"

if [ $BUILT_COUNT -eq $TOTAL_COUNT ]; then
    print_success "All modules built successfully! ✅"
    echo ""
    print_status "Next steps:"
    echo "1. Test platform: python omni_build_runner.py"
    echo "2. Launch desktop app: ./deployment-packages/omni-desktop-v1.0.0/OMNI\\ AI\\ Dashboard"
    echo "3. Check status: python omni_build_monitor.py"
    echo "4. View build report: python omni_build_manager.py"
else
    print_warning "Some modules failed to build. Check errors above."
    print_status "You can retry failed modules individually:"
    echo "python build_module.py --module <module_name>"
fi

echo ""
print_status "Build state saved to: $STATE_FILE"
print_status "Build completed at: $(date)"

# Update state file timestamp
jq --arg timestamp "$(date -Iseconds)" '.last_updated=$timestamp' "$STATE_FILE" > temp_state.json && mv temp_state.json "$STATE_FILE"