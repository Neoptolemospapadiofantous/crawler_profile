#!/bin/bash

# Profile Automation System Setup Script
# This script helps set up the development environment

set -e

echo "🚀 Setting up Profile Automation System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate || {
        print_error "Failed to activate virtual environment"
        exit 1
    }
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p data/profiles
    mkdir -p logs
    mkdir -p config
    mkdir -p docs/{api,user-guide,development}
    mkdir -p tests/{unit,integration,fixtures}
    
    print_success "Directories created"
}

# Copy configuration template
setup_config() {
    print_status "Setting up configuration..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your configuration"
    else
        print_warning ".env file already exists"
    fi
}

# Check for external dependencies
check_external_deps() {
    print_status "Checking external dependencies..."
    
    # Check for Chrome
    if command -v google-chrome &> /dev/null || command -v chrome &> /dev/null || command -v chromium &> /dev/null; then
        print_success "Chrome browser found"
    else
        print_warning "Chrome browser not found. Please install Google Chrome for web automation"
    fi
    
    # Check for ChromeDriver
    if command -v chromedriver &> /dev/null; then
        print_success "ChromeDriver found"
    else
        print_warning "ChromeDriver not found. Please install ChromeDriver or update .env with path"
    fi
    
    # Check for MySQL
    if command -v mysql &> /dev/null; then
        print_success "MySQL client found"
    else
        print_warning "MySQL client not found. Please install MySQL"
    fi
}

# Generate encryption key
generate_encryption_key() {
    print_status "Generating encryption key..."
    
    if command -v python3 &> /dev/null; then
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        echo "Generated encryption key: $ENCRYPTION_KEY"
        print_warning "Please add this key to your .env file as ENCRYPTION_KEY"
    else
        print_warning "Could not generate encryption key. Please generate manually"
    fi
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."
    
    source venv/bin/activate
    python -m src.main status
    
    print_success "Initial tests completed"
}

# Main setup flow
main() {
    echo "======================================"
    echo "Profile Automation System Setup"
    echo "======================================"
    
    check_python
    create_venv
    install_dependencies
    create_directories
    setup_config
    check_external_deps
    generate_encryption_key
    
    echo ""
    echo "======================================"
    print_success "Setup completed!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Install Chrome and ChromeDriver if not already installed"
echo "   - Download Chrome: https://www.google.com/chrome/"
echo "   - Download ChromeDriver: https://chromedriver.chromium.org/"
echo "   - Or use: pip install webdriver-manager (auto-manages ChromeDriver)"
    echo "3. Set up MySQL database"
    echo "4. Run: source venv/bin/activate"
    echo "5. Run: python -m src.main init"
    echo "6. Run: python -m src.main status"
    echo ""
    echo "For more information, see README.md"
}

# Run main function
main "$@"