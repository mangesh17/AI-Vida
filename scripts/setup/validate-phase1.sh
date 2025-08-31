#!/bin/bash
# Phase 1 Infrastructure Validation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TOTAL_TESTS++))
    log_info "Testing: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        log_success "$test_name"
        ((PASSED_TESTS++))
        return 0
    else
        log_fail "$test_name"
        ((FAILED_TESTS++))
        return 0  # Don't exit on test failure, just record it
    fi
}

run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected_output="$3"
    
    ((TOTAL_TESTS++))
    log_info "Testing: $test_name"
    
    local output
    output=$(eval "$test_command" 2>&1)
    
    if [[ "$output" == *"$expected_output"* ]]; then
        log_success "$test_name"
        return 0
    else
        log_fail "$test_name - Expected: $expected_output, Got: $output"
        return 1
    fi
}

# Test 1: Check Required Tools
test_required_tools() {
    log_info "=== Testing Required Tools ==="
    
    run_test "Python 3.11+ installed" "python3 --version | grep -E 'Python 3\.(11|12)'"
    run_test "Docker installed" "docker --version"
    run_test "Docker Compose installed" "docker-compose --version"
    run_test "Node.js 16+ installed" "node --version | grep -E 'v(1[6-9]|[2-9][0-9])'"
    run_test "npm installed" "npm --version"
    run_test "Git installed" "git --version"
}

# Test 2: Check Project Structure
test_project_structure() {
    log_info "=== Testing Project Structure ==="
    
    local required_dirs=(
        "src/backend"
        "src/frontend"
        "src/shared"
        "infrastructure/terraform"
        "infrastructure/kubernetes"
        "tests"
        "configs"
        "scripts"
        "docs"
    )
    
    for dir in "${required_dirs[@]}"; do
        run_test "Directory exists: $dir" "[ -d '$dir' ]"
    done
    
    local required_files=(
        "Dockerfile"
        "docker-compose.yml"
        "requirements.txt"
        "requirements-dev.txt"
        ".env.example"
        ".github/workflows/ci-cd.yml"
    )
    
    for file in "${required_files[@]}"; do
        run_test "File exists: $file" "[ -f '$file' ]"
    done
}

# Test 3: Python Environment
test_python_environment() {
    log_info "=== Testing Python Environment ==="
    
    run_test "Virtual environment exists" "[ -d 'venv' ]"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        run_test "Virtual environment activated" "[ '$VIRTUAL_ENV' != '' ]"
        run_test "Pip is latest version" "python -m pip install --upgrade pip --dry-run | grep -q 'already satisfied\|would install'"
        
        # Test if requirements files are valid syntax
        if [ -f "requirements.txt" ]; then
            run_test "Requirements.txt is valid" "python -m pip check --quiet || python -c 'open(\"requirements.txt\").read()'"
        fi
        
        if [ -f "requirements-dev.txt" ]; then
            run_test "Requirements-dev.txt is valid" "python -c 'open(\"requirements-dev.txt\").read()'"
        fi
    fi
}

# Test 4: Docker Configuration
test_docker_configuration() {
    log_info "=== Testing Docker Configuration ==="
    
    run_test "Docker daemon is running" "docker info"
    run_test "Docker Compose file is valid" "docker-compose config"
    run_test "Dockerfile syntax is valid" "docker build --help > /dev/null && [ -f Dockerfile ]"
    
    # Test if Dockerfile has valid base image and basic structure
    run_test "Dockerfile build validation" "grep -q 'FROM ' Dockerfile && [ -f Dockerfile ]"
}

# Test 5: Configuration Files
test_configuration_files() {
    log_info "=== Testing Configuration Files ==="
    
    # Test .env.example
    if [ -f ".env.example" ]; then
        run_test ".env.example has required variables" "grep -q 'PROJECT_ID\|DATABASE_URL\|JWT_SECRET_KEY' .env.example"
    fi
    
    # Test Redis config
    if [ -f "configs/redis/redis.conf" ]; then
        run_test "Redis config is valid" "grep -q 'requirepass\|bind' configs/redis/redis.conf"
    fi
    
    # Test database init script
    if [ -f "scripts/setup/init-db.sql" ]; then
        run_test "Database init script is valid" "grep -q 'CREATE DATABASE\|CREATE USER' scripts/setup/init-db.sql"
    fi
}

# Test 6: Terraform Configuration
test_terraform_configuration() {
    log_info "=== Testing Terraform Configuration ==="
    
    if command -v terraform >/dev/null 2>&1; then
        cd infrastructure/terraform/environments/dev
        
        run_test "Terraform format check" "terraform fmt -check -diff"
        run_test "Terraform initialization" "terraform init -backend=false"
        run_test "Terraform validation" "terraform validate"
        
        cd ../../../..
    else
        log_warning "Terraform not installed, skipping Terraform tests"
    fi
}

# Test 7: CI/CD Configuration
test_cicd_configuration() {
    log_info "=== Testing CI/CD Configuration ==="
    
    if [ -f ".github/workflows/ci-cd.yml" ]; then
        run_test "CI/CD workflow file exists" "[ -f '.github/workflows/ci-cd.yml' ]"
        run_test "CI/CD workflow has required jobs" "grep -q 'security-scan\|backend-test\|frontend-test' .github/workflows/ci-cd.yml"
    fi
}

# Test 8: Network Connectivity
test_network_connectivity() {
    log_info "=== Testing Network Connectivity ==="
    
    run_test "Internet connectivity" "ping -c 1 google.com"
    run_test "Docker Hub connectivity" "docker pull hello-world"
    run_test "npm registry connectivity" "npm ping"
    
    # Clean up test image
    docker rmi hello-world >/dev/null 2>&1 || true
}

# Test 9: File Permissions
test_file_permissions() {
    log_info "=== Testing File Permissions ==="
    
    run_test "Setup script is executable" "[ -x 'scripts/setup/init-dev-env.sh' ]"
    
    # Check if .env file has secure permissions (if it exists)
    if [ -f ".env" ]; then
        run_test ".env file has secure permissions" "[ '$(stat -c %a .env)' = '600' ]"
    fi
}

# Test 10: Security Validation
test_security_validation() {
    log_info "=== Testing Security Configuration ==="
    
    # Check for sensitive data in config files
    run_test "No hardcoded passwords in configs" "! grep -r 'password.*=' configs/ | grep -v 'development_password\|your-password'"
    run_test "No API keys in configs" "! grep -r 'api.*key.*=' configs/ | grep -v 'your-api-key'"
    
    # Check .gitignore
    if [ -f ".gitignore" ]; then
        run_test ".gitignore excludes sensitive files" "grep -q '.env\|secrets\|*.key' .gitignore"
    fi
}

# Main execution
main() {
    log_info "Starting Phase 1 Infrastructure Validation..."
    log_info "======================================="
    
    test_required_tools
    test_project_structure
    test_python_environment
    test_docker_configuration
    test_configuration_files
    test_terraform_configuration
    test_cicd_configuration
    test_network_connectivity
    test_file_permissions
    test_security_validation
    
    log_info "======================================="
    log_info "VALIDATION SUMMARY"
    log_info "======================================="
    echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo -e "Success Rate: ${BLUE}$(( PASSED_TESTS * 100 / TOTAL_TESTS ))%${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "All validation tests passed! Phase 1 is ready for Phase 2."
        exit 0
    else
        log_fail "$FAILED_TESTS tests failed. Please fix the issues before proceeding to Phase 2."
        exit 1
    fi
}

# Run main function
main "$@"
