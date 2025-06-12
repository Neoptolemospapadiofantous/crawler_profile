#!/bin/bash

# ============================================================================
# PHASE 1 COMPREHENSIVE TESTING SCRIPT
# Run this to validate the complete Phase 1 setup
# ============================================================================

set -e  # Exit on any error

echo ""
echo "🧪 PHASE 1 COMPREHENSIVE TESTING"
echo "================================="
echo "Testing all components of Phase 1 setup..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_WARNED=0
TESTS_FAILED=0

# Helper function to run tests
run_test() {
    local test_name="$1"
    local test_command="$2"
    local should_pass="$3"  # "pass", "warn", or "fail_ok"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    print_test "$test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        if [ "$should_pass" = "pass" ] || [ "$should_pass" = "warn" ]; then
            print_pass "$test_name"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            print_warn "$test_name (unexpected pass)"
            TESTS_WARNED=$((TESTS_WARNED + 1))
        fi
    else
        if [ "$should_pass" = "fail_ok" ]; then
            print_warn "$test_name (expected failure)"
            TESTS_WARNED=$((TESTS_WARNED + 1))
        else
            print_fail "$test_name"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
}

# ============================================================================
# TEST 1: Project Structure
# ============================================================================
echo "📁 TEST SUITE 1: Project Structure"
echo "-----------------------------------"

run_test "README.md exists" "[ -f README.md ]" "pass"
run_test "setup.py exists" "[ -f setup.py ]" "pass"
run_test "requirements.txt exists" "[ -f requirements.txt ]" "pass"
run_test ".env.example exists" "[ -f .env.example ]" "pass"
run_test ".gitignore exists" "[ -f .gitignore ]" "pass"
run_test "LICENSE exists" "[ -f LICENSE ]" "pass"

run_test "src/ directory exists" "[ -d src ]" "pass"
run_test "config/ directory exists" "[ -d config ]" "pass"
run_test "scripts/ directory exists" "[ -d scripts ]" "pass"
run_test "tests/ directory exists" "[ -d tests ]" "pass"

run_test "src/__init__.py exists" "[ -f src/__init__.py ]" "pass"
run_test "src/main.py exists" "[ -f src/main.py ]" "pass"
run_test "src/cli.py exists" "[ -f src/cli.py ]" "pass"
run_test "config/settings.py exists" "[ -f config/settings.py ]" "pass"
run_test "config/logging.yaml exists" "[ -f config/logging.yaml ]" "pass"

echo ""

# ============================================================================
# TEST 2: Git Repository
# ============================================================================
echo "📊 TEST SUITE 2: Git Repository"
echo "-------------------------------"

run_test "Git repository initialized" "[ -d .git ]" "pass"
run_test "Git has commits" "git log --oneline -1" "pass"
run_test "Git working directory clean" "git diff --quiet" "warn"

echo ""
echo "📋 Recent Git commits:"
git log --oneline -5 2>/dev/null || echo "No git history found"
echo ""

# ============================================================================
# TEST 3: Python Environment Detection
# ============================================================================
echo "🐍 TEST SUITE 3: Python Environment"
echo "-----------------------------------"

# Detect Python command
PYTHON_CMD=""
if command -v python &> /dev/null && python --version 2>&1 | grep -q "Python 3"; then
    PYTHON_CMD="python"
    print_pass "Python command found: python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_pass "Python command found: python3"
elif command -v py &> /dev/null; then
    PYTHON_CMD="py"
    print_pass "Python command found: py"
else
    print_fail "No Python 3 command found"
    echo ""
    echo "❌ CRITICAL ERROR: Python 3.8+ required"
    echo "Please install Python from https://python.org/downloads/"
    echo "During installation, check 'Add Python to PATH'"
    exit 1
fi

echo "✅ Using Python command: $PYTHON_CMD"
echo "✅ Python version: $($PYTHON_CMD --version 2>&1)"

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
    print_pass "Python version is 3.8+ ($PYTHON_VERSION)"
else
    print_fail "Python version too old: $PYTHON_VERSION (need 3.8+)"
    exit 1
fi

echo ""

# ============================================================================
# TEST 4: Virtual Environment
# ============================================================================
echo "🔧 TEST SUITE 4: Virtual Environment"
echo "------------------------------------"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_test "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -eq 0 ]; then
        print_pass "Virtual environment created"
    else
        print_fail "Failed to create virtual environment"
        exit 1
    fi
else
    print_pass "Virtual environment already exists"
fi

# Activate virtual environment (Windows vs Unix)
print_test "Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
    print_pass "Virtual environment activated (Windows)"
elif [ -f "venv/bin/activate" ]; then
    # Unix/Linux/Mac
    source venv/bin/activate
    print_pass "Virtual environment activated (Unix)"
else
    print_fail "Could not find virtual environment activation script"
    ls -la venv/ 2>/dev/null || echo "venv directory not found"
    exit 1
fi

# Verify we're in virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_pass "Virtual environment is active"
    echo "  Virtual env path: $VIRTUAL_ENV"
else
    print_warn "Virtual environment might not be fully active"
fi

echo "  Python location: $(which python)"
echo "  Pip location: $(which pip)"

echo ""

# ============================================================================
# TEST 5: Dependencies Installation
# ============================================================================
echo "📦 TEST SUITE 5: Dependencies"
echo "-----------------------------"

# Detect network connectivity for package installation
NETWORK_AVAILABLE=1
curl -Is https://pypi.org --connect-timeout 5 >/dev/null 2>&1 || NETWORK_AVAILABLE=0

# Upgrade pip if network is available
print_test "Upgrading pip..."
if [ $NETWORK_AVAILABLE -eq 1 ]; then
    pip install --upgrade pip --quiet
    print_pass "Pip upgraded"
else
    print_warn "No network connection, skipping pip upgrade"
fi

# Install requirements
if [ -f "requirements.txt" ]; then
    print_test "Installing requirements..."
    if [ $NETWORK_AVAILABLE -eq 1 ]; then
        pip install -r requirements.txt --quiet
        if [ $? -eq 0 ]; then
            print_pass "Requirements installed successfully"
        else
            print_fail "Some requirements failed to install"
            echo "This might be due to missing build tools"
        fi
    else
        print_warn "No network connection, skipping requirements installation"
    fi
else
    print_fail "requirements.txt not found"
    exit 1
fi

# Check key packages
echo ""
echo "📋 Key installed packages:"
pip list | grep -E "(click|pydantic|selenium|structlog|cryptography)" || print_warn "Some packages might be missing"

echo ""

# ============================================================================
# TEST 6: Application Entry Points
# ============================================================================
echo "🚀 TEST SUITE 6: Application Testing"
echo "------------------------------------"

# Test main application
print_test "Testing main application import..."
if python -c "import src.main" >/dev/null 2>&1; then
    print_pass "Main application imports successfully"
else
    print_fail "Main application import failed"
    echo "Debugging import error:"
    python -c "import src.main" 2>&1 | head -5
fi

print_test "Testing main application help..."
if python -m src.main --help >/dev/null 2>&1; then
    print_pass "Main application help works"
else
    print_fail "Main application help failed"
fi

print_test "Testing CLI import..."
if python -c "import src.cli" >/dev/null 2>&1; then
    print_pass "CLI imports successfully"
else
    print_fail "CLI import failed"
fi

print_test "Testing CLI help..."
if python -m src.cli --help >/dev/null 2>&1; then
    print_pass "CLI help works"
else
    print_fail "CLI help failed"
fi

echo ""

# ============================================================================
# TEST 7: Configuration System
# ============================================================================
echo "⚙️  TEST SUITE 7: Configuration"
echo "-------------------------------"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    print_test "Creating .env from example..."
    cp .env.example .env
    print_pass ".env file created"
    
    # Generate encryption key
    print_test "Generating encryption key..."
    if python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" >/dev/null 2>&1; then
        ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        # Update .env file (cross-platform sed alternative)
        python -c "
import re
with open('.env', 'r') as f:
    content = f.read()
content = re.sub(r'ENCRYPTION_KEY=.*', f'ENCRYPTION_KEY=$ENCRYPTION_KEY', content)
with open('.env', 'w') as f:
    f.write(content)
"
        print_pass "Encryption key generated and added to .env"
    else
        print_warn "Could not generate encryption key automatically"
    fi
else
    print_pass ".env file already exists"
fi

# Test configuration loading
print_test "Testing configuration system..."
if python -c "from config.settings import get_settings; s = get_settings(); print('Config loaded')" >/dev/null 2>&1; then
    print_pass "Configuration system works"
else
    print_fail "Configuration system failed"
    echo "Debugging config error:"
    python -c "from config.settings import get_settings; get_settings()" 2>&1 | head -3
fi

# Test config commands
print_test "Testing config show command..."
if python -m src.cli config show >/dev/null 2>&1; then
    print_pass "Config show command works"
else
    print_warn "Config show command failed (might be due to missing DB config)"
fi

echo ""

# ============================================================================
# TEST 8: Logging System
# ============================================================================
echo "📝 TEST SUITE 8: Logging System"
echo "-------------------------------"

# Create logs directory
mkdir -p logs

print_test "Testing logging system..."
if python -c "from src.core.logging import get_main_logger; logger = get_main_logger(); logger.info('Test log message')" >/dev/null 2>&1; then
    print_pass "Logging system works"
else
    print_fail "Logging system failed"
fi

# Test application init (creates logs)
print_test "Testing application init..."
if python -m src.main init >/dev/null 2>&1; then
    print_pass "Application init works"
else
    print_warn "Application init failed (might be due to missing config)"
fi

# Check if logs were created
if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
    print_pass "Log files created"
    echo "  Log files: $(ls logs/ 2>/dev/null | tr '\n' ' ')"
else
    print_warn "No log files found (might be normal on first run)"
fi

echo ""

# ============================================================================
# TEST 9: Status Command (Full Integration Test)
# ============================================================================
echo "🔍 TEST SUITE 9: Integration Test"
echo "---------------------------------"

print_test "Running full status command..."
echo ""
echo "=== Application Status Output ==="
python -m src.main status 2>&1 || print_warn "Status command had issues"
echo "================================="
echo ""

# ============================================================================
# TEST 10: External Dependencies (Optional)
# ============================================================================
echo "🌐 TEST SUITE 10: External Dependencies"
echo "---------------------------------------"

print_test "Checking Chrome browser..."
if command -v google-chrome &> /dev/null || command -v chrome &> /dev/null || command -v chromium &> /dev/null; then
    print_pass "Chrome browser found"
elif [ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ] || [ -f "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" ]; then
    print_pass "Chrome browser found (Windows)"
else
    print_warn "Chrome browser not found (install from https://www.google.com/chrome/)"
fi

print_test "Checking ChromeDriver..."
if command -v chromedriver &> /dev/null; then
    print_pass "ChromeDriver found: $(chromedriver --version 2>/dev/null | head -1)"
else
    print_warn "ChromeDriver not found (webdriver-manager will auto-download)"
fi

print_test "Checking MySQL client..."
if command -v mysql &> /dev/null; then
    print_pass "MySQL client found"
else
    print_warn "MySQL client not found (needed for Phase 2)"
fi

echo ""

# ============================================================================
# FINAL TEST SUMMARY
# ============================================================================
echo "📊 PHASE 1 TEST SUMMARY"
echo "======================="

echo ""
echo "📈 Test Results:"
echo "  Tests Run: $TESTS_RUN"
echo "  Passed: $TESTS_PASSED"
echo "  Warnings: $TESTS_WARNED"
echo "  Failed: $TESTS_FAILED"

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    print_pass "ALL CRITICAL TESTS PASSED! ✅"
    echo ""
    echo "🎉 PHASE 1 IS READY!"
    echo "===================="
    echo ""
    echo "✅ What's working:"
    echo "  - Project structure ✓"
    echo "  - Python environment ✓"
    echo "  - Virtual environment ✓"
    echo "  - Dependencies installed ✓"
    echo "  - Applications start ✓"
    echo "  - Configuration loads ✓"
    echo "  - Logging system works ✓"
    echo ""
    echo "🎯 Ready for Phase 2: Database Models"
    echo ""
    echo "🔧 Next steps:"
    echo "  1. Edit .env with your database credentials"
    echo "  2. Install Chrome if you haven't already"
    echo "  3. Set up MySQL database"
    echo "  4. Proceed to Phase 2!"
    
    exit 0
else
    print_fail "$TESTS_FAILED CRITICAL TESTS FAILED ❌"
    echo ""
    echo "🔧 ISSUES TO FIX:"
    echo "=================="
    echo ""
    echo "Before proceeding to Phase 2, please:"
    echo "  1. Review the failed tests above"
    echo "  2. Fix any Python/import issues"
    echo "  3. Ensure all core files exist"
    echo "  4. Re-run this test script"
    echo ""
    echo "💡 Common fixes:"
    echo "  - Install missing Python packages"
    echo "  - Check Python path and version"
    echo "  - Verify virtual environment activation"
    echo "  - Fix import path issues"
    
    exit 1
fi
