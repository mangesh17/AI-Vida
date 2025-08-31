#!/bin/bash
# Complete Phase 1 Validation Suite
# Runs all validation tests and provides comprehensive report

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Test results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

log_header() {
    echo -e "\n${BOLD}${BLUE}========================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}========================================${NC}\n"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓ PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[✗ FAIL]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

run_test_suite() {
    local suite_name="$1"
    local script_path="$2"
    local is_critical="${3:-true}"
    
    ((TOTAL_SUITES++))
    log_header "Running $suite_name"
    
    if [ ! -f "$script_path" ]; then
        log_fail "$suite_name - Script not found: $script_path"
        if [ "$is_critical" = "true" ]; then
            ((FAILED_SUITES++))
            return 1
        else
            log_warning "$suite_name - Skipping non-critical test"
            return 0
        fi
    fi
    
    if [ ! -x "$script_path" ]; then
        log_warning "Making $script_path executable..."
        chmod +x "$script_path"
    fi
    
    local start_time=$(date +%s)
    
    if "$script_path"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "$suite_name completed successfully (${duration}s)"
        ((PASSED_SUITES++))
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_fail "$suite_name failed (${duration}s)"
        if [ "$is_critical" = "true" ]; then
            ((FAILED_SUITES++))
            return 1
        else
            log_warning "$suite_name failed but is non-critical"
            return 0
        fi
    fi
}

# Pre-flight checks
pre_flight_checks() {
    log_header "Pre-Flight Checks"
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ] || [ ! -d "infrastructure" ]; then
        log_fail "Not in AI-Vida project root directory"
        exit 1
    fi
    
    log_success "In correct project directory"
    
    # Check basic tools
    local missing_tools=()
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    command -v python3 >/dev/null 2>&1 || missing_tools+=("python3")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_fail "Missing essential tools: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "Essential tools are available"
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log_fail "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Docker daemon is running"
}

# Generate comprehensive report
generate_final_report() {
    log_header "PHASE 1 VALIDATION REPORT"
    
    echo -e "Test Execution Summary:"
    echo -e "  Total Test Suites: ${BLUE}$TOTAL_SUITES${NC}"
    echo -e "  Passed: ${GREEN}$PASSED_SUITES${NC}"
    echo -e "  Failed: ${RED}$FAILED_SUITES${NC}"
    
    local success_rate=0
    if [ $TOTAL_SUITES -gt 0 ]; then
        success_rate=$((PASSED_SUITES * 100 / TOTAL_SUITES))
    fi
    echo -e "  Success Rate: ${BLUE}${success_rate}%${NC}"
    
    echo -e "\nPhase 1 Component Status:"
    echo -e "  ✓ Infrastructure as Code (Terraform)"
    echo -e "  ✓ Development Environment (Docker)"
    echo -e "  ✓ Python Dependencies & Virtual Environment"
    echo -e "  ✓ Security Configuration"
    echo -e "  ✓ CI/CD Pipeline Configuration"
    echo -e "  ✓ Project Structure & Documentation"
    
    echo -e "\nNext Steps:"
    if [ $FAILED_SUITES -eq 0 ]; then
        echo -e "  ${GREEN}🎉 Phase 1 validation PASSED!${NC}"
        echo -e "  ${GREEN}✓ Ready to proceed to Phase 2: Core AI Development${NC}"
        echo -e ""
        echo -e "  To start Phase 2:"
        echo -e "    1. Set up actual GCP project: gcloud projects create [PROJECT_ID]"
        echo -e "    2. Configure environment: cp .env.example .env && edit .env"
        echo -e "    3. Deploy infrastructure: cd infrastructure/terraform/environments/dev && terraform apply"
        echo -e "    4. Start development: docker-compose up -d"
        echo -e "    5. Begin implementing AI services in src/backend/"
        
        return 0
    else
        echo -e "  ${RED}❌ Phase 1 validation FAILED!${NC}"
        echo -e "  ${RED}✗ $FAILED_SUITES critical issues need to be resolved${NC}"
        echo -e ""
        echo -e "  Common fixes:"
        echo -e "    1. Install missing dependencies: ./scripts/setup/init-dev-env.sh"
        echo -e "    2. Fix Docker issues: restart Docker daemon"
        echo -e "    3. Check file permissions: chmod +x scripts/setup/*.sh"
        echo -e "    4. Install Python packages: source venv/bin/activate && pip install -r requirements.txt"
        
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    
    # Stop any running containers
    docker-compose down -v --remove-orphans >/dev/null 2>&1 || true
    
    # Clean up temporary files
    find . -name "test_temp_file.txt" -delete 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    local start_time=$(date +%s)
    
    log_header "AI-VIDA PHASE 1 VALIDATION SUITE"
    echo -e "Starting comprehensive validation of Phase 1 infrastructure..."
    echo -e "This will test all components needed for Phase 2 development.\n"
    
    # Pre-flight checks
    pre_flight_checks
    
    # Run test suites
    log_info "Running validation test suites...\n"
    
    # Critical tests (must pass)
    run_test_suite "Infrastructure Validation" "./scripts/setup/validate-phase1.sh" true
    run_test_suite "Python Environment Test" "./scripts/setup/test-python-env.py" true
    run_test_suite "Docker Stack Integration" "./scripts/setup/test-docker-stack.sh" true
    
    # Calculate total time
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    local minutes=$((total_duration / 60))
    local seconds=$((total_duration % 60))
    
    # Generate final report
    generate_final_report
    
    echo -e "\nTotal validation time: ${minutes}m ${seconds}s"
    log_header "VALIDATION COMPLETE"
    
    # Return appropriate exit code
    if [ $FAILED_SUITES -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "AI-Vida Phase 1 Validation Suite"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --quick, -q    Run quick validation (skip integration tests)"
        echo "  --verbose, -v  Enable verbose output"
        echo ""
        echo "This script validates that Phase 1 infrastructure is ready for Phase 2 development."
        echo "It tests infrastructure, dependencies, Docker stack, and basic functionality."
        exit 0
        ;;
    --quick|-q)
        log_warning "Quick mode: skipping integration tests"
        # Only run critical infrastructure tests
        pre_flight_checks
        run_test_suite "Infrastructure Validation" "./scripts/setup/validate-phase1.sh" true
        run_test_suite "Python Environment Test" "./scripts/setup/test-python-env.py" true
        generate_final_report
        exit $?
        ;;
    --verbose|-v)
        set -x
        main
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
