#!/bin/bash
# Code Quality Setup Script
# Installs all development dependencies and configures the environment

set -e  # Exit on error

echo "=========================================="
echo "Code Quality Setup for Open Projects Hub"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    print_success "Python $PYTHON_VERSION detected (requirement: ≥3.11)"
else
    print_error "Python 3.11+ required (found: $PYTHON_VERSION)"
    exit 1
fi

# Check if pip is available
echo ""
echo "🔍 Checking pip..."
if command -v pip3 &> /dev/null; then
    print_success "pip is available"
else
    print_error "pip not found. Please install pip first."
    exit 1
fi

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip3 install --upgrade pip --quiet
print_success "pip upgraded"

# Install production dependencies
echo ""
echo "📦 Installing production dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    print_success "Production dependencies installed"
else
    print_warning "requirements.txt not found, skipping"
fi

# Install development dependencies
echo ""
echo "📦 Installing development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    pip3 install -r requirements-dev.txt --quiet
    print_success "Development dependencies installed"
else
    print_error "requirements-dev.txt not found"
    exit 1
fi

# Verify installations
echo ""
echo "🔍 Verifying tool installations..."

tools=(
    "ruff:Ruff (linter/formatter)"
    "mypy:MyPy (type checker)"
    "bandit:Bandit (security scanner)"
    "pre-commit:Pre-commit (git hooks)"
    "pytest:Pytest (testing framework)"
)

all_installed=true
for tool_info in "${tools[@]}"; do
    tool=$(echo $tool_info | cut -d: -f1)
    name=$(echo $tool_info | cut -d: -f2)
    
    if command -v $tool &> /dev/null; then
        version=$($tool --version 2>&1 | head -n1)
        print_success "$name: $version"
    else
        print_error "$name not found"
        all_installed=false
    fi
done

if [ "$all_installed" = false ]; then
    print_error "Some tools are not installed correctly"
    exit 1
fi

# Install pre-commit hooks
echo ""
echo "🪝 Installing pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install --install-hooks > /dev/null 2>&1
    pre-commit install --hook-type commit-msg > /dev/null 2>&1
    print_success "Pre-commit hooks installed"
else
    print_warning ".pre-commit-config.yaml not found, skipping hooks"
fi

# Create virtual environment recommendation
echo ""
if [ -d ".venv" ] || [ -d "venv" ]; then
    print_info "Virtual environment detected"
else
    print_warning "No virtual environment detected. Consider creating one:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
fi

# Success summary
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Read the documentation:"
echo "   • Quick start: docs/QUICK_START_CODE_QUALITY.md"
echo "   • Full guide: docs/CODE_QUALITY.md"
echo ""
echo "2. Run initial checks:"
echo "   make lint-fix"
echo "   make format"
echo "   make test"
echo ""
echo "3. Start coding:"
echo "   Pre-commit hooks will run automatically on every commit!"
echo ""
echo "📖 Available commands:"
echo "   make help              # Show all available commands"
echo "   make lint              # Check code quality"
echo "   make format            # Format code"
echo "   make test              # Run tests"
echo "   make coverage          # Run tests with coverage"
echo ""
print_success "Happy coding! 🚀"
