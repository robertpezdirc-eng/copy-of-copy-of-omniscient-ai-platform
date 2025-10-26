#!/bin/bash

# Bash script for parallel building of all Omni modules
# Compatible with Linux, macOS, and WSL

set -e  # Exit on any error

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

print_header() {
    echo -e "\033[1;36m$1\033[0m"
}

echo "🔧 OMNI Platform - Parallel Build"
echo "================================="

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

print_header "Starting parallel build of all Omni modules..."
echo "=================================================="

# Function to build a single module
build_module() {
    local module_json="$1"
    local MODULE_NAME=$(echo "$module_json" | jq -r '.name')
    local MODULE_STATUS=$(echo "$module_json" | jq -r '.status')

    if [ "$MODULE_STATUS" != "built" ]; then
        print_status "Building module: $MODULE_NAME"

        if python build_module.py --module "$MODULE_NAME"; then
            print_success "Module $MODULE_NAME built successfully"

            # Update module status in state file
            jq --arg name "$MODULE_NAME" \
               --arg timestamp "$(date -Iseconds)" \
               '(.modules[] | select(.name==$name) | .status)="built" | (.modules[] | select(.name==$name) | .last_build)=$timestamp' \
               "$STATE_FILE" > temp_state.json && mv temp_state.json "$STATE_FILE"

        else
            print_error "Build failed for module: $MODULE_NAME"

            # Update module status to failed
            jq --arg name "$MODULE_NAME" \
               --arg timestamp "$(date -Iseconds)" \
               '(.modules[] | select(.name==$name) | .status)="failed" | (.modules[] | select(.name==$name) | .last_build)=$timestamp' \
               "$STATE_FILE" > temp_state.json && mv temp_state.json "$STATE_FILE"
        fi
    else
        print_status "Module $MODULE_NAME already built, skipping..."
    fi
}

# Export the function so it can be used with parallel
export -f build_module
export -f print_status
export -f print_success
export -f print_error
export -f print_warning

# Build modules in parallel using background processes
PID_ARRAY=()
MODULE_ARRAY=()

while read -r module; do
    # Build module in background
    build_module "$module" &
    PID_ARRAY+=($!)
    MODULE_ARRAY+=("$module")
done <<< "$MODULES"

# Wait for all background processes to complete
print_status "Waiting for all parallel builds to complete..."
for i in "${!PID_ARRAY[@]}"; do
    pid=${PID_ARRAY[$i]}
    module=${MODULE_ARRAY[$i]}

    MODULE_NAME=$(echo "$module" | jq -r '.name')
    wait $pid
    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        print_error "Background process for $MODULE_NAME failed with exit code $EXIT_CODE"
    fi
done

# Update state file timestamp
jq --arg timestamp "$(date -Iseconds)" '.last_updated=$timestamp' "$STATE_FILE" > temp_state.json && mv temp_state.json "$STATE_FILE"

# Final status check
TOTAL_MODULES=$(jq '.modules | length' "$STATE_FILE")
BUILT_MODULES=$(jq '[.modules[] | select(.status=="built")] | length' "$STATE_FILE")
FAILED_MODULES=$(jq '[.modules[] | select(.status=="failed")] | length' "$STATE_FILE")

print_header "PARALLEL BUILD COMPLETION SUMMARY:"
echo "=================================================="
print_status "Total modules: $TOTAL_MODULES"
print_success "Successfully built: $BUILT_MODULES"
print_error "Failed: $FAILED_MODULES"

COMPLETION_RATE=$((BUILT_MODULES * 100 / TOTAL_MODULES))
print_status "Build completion rate: $COMPLETION_RATE%"

if [ $FAILED_MODULES -eq 0 ]; then
    print_success "All modules built successfully in parallel! ✅"
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

    echo ""
    print_error "Failed modules:"
    jq -r '.modules[] | select(.status=="failed") | .name' "$STATE_FILE" | while read module; do
        echo "  - $module"
    done
fi

echo ""
print_status "Build state saved to: $STATE_FILE"
print_status "Build completed at: $(date)"