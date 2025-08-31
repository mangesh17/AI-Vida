#!/bin/bash
# Development Environment Setup Script for AI-Vida

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS or Linux
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    log_info "Detected OS: $OS"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    command -v git >/dev/null 2>&1 || missing_tools+=("git")
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    command -v python3 >/dev/null 2>&1 || missing_tools+=("python3")
    command -v node >/dev/null 2>&1 || missing_tools+=("node")
    command -v npm >/dev/null 2>&1 || missing_tools+=("npm")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and run this script again."
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Install Google Cloud SDK
install_gcloud_sdk() {
    log_info "Installing Google Cloud SDK..."
    
    if command -v gcloud >/dev/null 2>&1; then
        log_success "Google Cloud SDK is already installed"
        return
    fi
    
    if [[ "$OS" == "macos" ]]; then
        if command -v brew >/dev/null 2>&1; then
            brew install --cask google-cloud-sdk
        else
            log_warning "Homebrew not found. Please install Google Cloud SDK manually."
            log_info "Visit: https://cloud.google.com/sdk/docs/install"
        fi
    elif [[ "$OS" == "linux" ]]; then
        curl https://sdk.cloud.google.com | bash
        exec -l $SHELL
    fi
    
    log_success "Google Cloud SDK installed"
}

# Install Terraform
install_terraform() {
    log_info "Installing Terraform..."
    
    if command -v terraform >/dev/null 2>&1; then
        log_success "Terraform is already installed"
        return
    fi
    
    if [[ "$OS" == "macos" ]]; then
        if command -v brew >/dev/null 2>&1; then
            brew tap hashicorp/tap
            brew install hashicorp/tap/terraform
        else
            log_warning "Homebrew not found. Please install Terraform manually."
        fi
    elif [[ "$OS" == "linux" ]]; then
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
    fi
    
    log_success "Terraform installed"
}

# Install kubectl
install_kubectl() {
    log_info "Installing kubectl..."
    
    if command -v kubectl >/dev/null 2>&1; then
        log_success "kubectl is already installed"
        return
    fi
    
    if [[ "$OS" == "macos" ]]; then
        if command -v brew >/dev/null 2>&1; then
            brew install kubectl
        else
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
            chmod +x kubectl
            sudo mv kubectl /usr/local/bin/
        fi
    elif [[ "$OS" == "linux" ]]; then
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        sudo mv kubectl /usr/local/bin/
    fi
    
    log_success "kubectl installed"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2)
    required_version="3.11"
    
    if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
        log_error "Python $required_version or higher is required. Found: $python_version"
        exit 1
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    
    if [ -f "requirements-dev.txt" ]; then
        log_info "Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi
    
    log_success "Python environment setup complete"
}

# Setup Node.js environment
setup_node_env() {
    log_info "Setting up Node.js environment..."
    
    # Check Node.js version
    node_version=$(node --version | cut -d'v' -f2)
    required_version="18.0.0"
    
    if [[ "$(printf '%s\n' "$required_version" "$node_version" | sort -V | head -n1)" != "$required_version" ]]; then
        log_error "Node.js $required_version or higher is required. Found: $node_version"
        exit 1
    fi
    
    # Install frontend dependencies
    for app in patient-portal clinician-portal admin-portal; do
        if [ -d "src/frontend/$app" ]; then
            log_info "Installing dependencies for $app..."
            cd "src/frontend/$app"
            npm install
            cd ../../..
        fi
    done
    
    log_success "Node.js environment setup complete"
}

# Setup environment variables
setup_env_vars() {
    log_info "Setting up environment variables..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Created .env file from .env.example"
            log_warning "Please update .env file with your actual configuration values"
        else
            log_warning ".env.example file not found. Please create .env file manually"
        fi
    else
        log_success ".env file already exists"
    fi
}

# Setup Git hooks
setup_git_hooks() {
    log_info "Setting up Git hooks..."
    
    # Pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for AI-Vida

# Run linting
echo "Running Python linting..."
source venv/bin/activate
flake8 src/ --max-line-length=88 --exclude=migrations
if [ $? -ne 0 ]; then
    echo "Python linting failed. Please fix the issues before committing."
    exit 1
fi

# Run security checks
echo "Running security checks..."
bandit -r src/ -x tests/
if [ $? -ne 0 ]; then
    echo "Security check failed. Please fix the issues before committing."
    exit 1
fi

# Run tests
echo "Running tests..."
pytest tests/ --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Please fix the issues before committing."
    exit 1
fi

echo "All checks passed!"
EOF
    
    chmod +x .git/hooks/pre-commit
    log_success "Git hooks setup complete"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p uploads
    mkdir -p logs
    mkdir -p backups
    mkdir -p temp
    mkdir -p data/postgres
    mkdir -p data/redis
    
    log_success "Directories created"
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    # Start database container
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    if [ -f "alembic.ini" ]; then
        source venv/bin/activate
        alembic upgrade head
        log_success "Database migrations applied"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check if all services can start
    docker-compose up -d
    sleep 30
    
    # Check service health
    services=("postgres" "redis" "api-gateway")
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service failed to start"
        fi
    done
    
    # Stop services
    docker-compose down
}

# Main execution
main() {
    log_info "Starting AI-Vida development environment setup..."
    
    detect_os
    check_prerequisites
    install_gcloud_sdk
    install_terraform
    install_kubectl
    setup_python_env
    setup_node_env
    setup_env_vars
    setup_git_hooks
    create_directories
    setup_database
    verify_installation
    
    log_success "Development environment setup complete!"
    log_info "Next steps:"
    log_info "1. Update .env file with your configuration"
    log_info "2. Configure GCP credentials: gcloud auth login"
    log_info "3. Run: docker-compose up -d to start all services"
    log_info "4. Access the application at http://localhost:3000"
}

# Run main function
main "$@"
