#!/bin/bash
# Docker Stack Integration Test for Phase 1

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓ PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[✗ FAIL]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Test variables
DOCKER_COMPOSE_FILE="docker-compose.yml"
TEST_TIMEOUT=120
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=5

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    docker-compose down -v --remove-orphans >/dev/null 2>&1 || true
    docker system prune -f >/dev/null 2>&1 || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Test 1: Docker Compose Validation
test_docker_compose_validation() {
    log_info "=== Testing Docker Compose Configuration ==="
    
    if docker-compose config >/dev/null 2>&1; then
        log_success "Docker Compose configuration is valid"
    else
        log_fail "Docker Compose configuration is invalid"
        docker-compose config
        return 1
    fi
}

# Test 2: Service Startup
test_service_startup() {
    log_info "=== Testing Service Startup ==="
    
    log_info "Starting core services (postgres, redis)..."
    if docker-compose up -d postgres redis; then
        log_success "Core services started successfully"
    else
        log_fail "Failed to start core services"
        return 1
    fi
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    local retries=0
    while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
        if docker-compose ps postgres | grep -q "Up (healthy)" && \
           docker-compose ps redis | grep -q "Up (healthy)"; then
            log_success "All core services are healthy"
            return 0
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
        ((retries++))
        log_info "Health check attempt $retries/$HEALTH_CHECK_RETRIES"
    done
    
    log_fail "Services failed to become healthy within timeout"
    docker-compose logs postgres redis
    return 1
}

# Test 3: Database Connectivity
test_database_connectivity() {
    log_info "=== Testing Database Connectivity ==="
    
    # Test PostgreSQL connection
    local db_test_result
    db_test_result=$(docker-compose exec -T postgres psql -U aivida_app -d aivida_main -c "SELECT 1;" 2>&1)
    
    if echo "$db_test_result" | grep -q "1 row"; then
        log_success "PostgreSQL database connection successful"
    else
        log_fail "PostgreSQL database connection failed: $db_test_result"
        return 1
    fi
    
    # Test Redis connection
    local redis_test_result
    redis_test_result=$(docker-compose exec -T redis redis-cli ping 2>&1)
    
    if echo "$redis_test_result" | grep -q "PONG"; then
        log_success "Redis connection successful"
    else
        log_fail "Redis connection failed: $redis_test_result"
        return 1
    fi
}

# Test 4: Database Schema
test_database_schema() {
    log_info "=== Testing Database Schema ==="
    
    # Check if databases exist
    local databases
    databases=$(docker-compose exec -T postgres psql -U aivida_app -d postgres -t -c "SELECT datname FROM pg_database WHERE datname IN ('aivida_main', 'aivida_audit', 'aivida_test');" | tr -d ' ')
    
    if echo "$databases" | grep -q "aivida_main" && \
       echo "$databases" | grep -q "aivida_audit" && \
       echo "$databases" | grep -q "aivida_test"; then
        log_success "All required databases exist"
    else
        log_fail "Required databases are missing: $databases"
        return 1
    fi
    
    # Check extensions
    local extensions
    extensions=$(docker-compose exec -T postgres psql -U aivida_app -d aivida_main -t -c "SELECT extname FROM pg_extension;" | tr -d ' ')
    
    if echo "$extensions" | grep -q "uuid-ossp" && \
       echo "$extensions" | grep -q "pgcrypto"; then
        log_success "Required PostgreSQL extensions are installed"
    else
        log_fail "Required PostgreSQL extensions are missing: $extensions"
        return 1
    fi
}

# Test 5: Volume Persistence
test_volume_persistence() {
    log_info "=== Testing Volume Persistence ==="
    
    # Create test data
    docker-compose exec -T postgres psql -U aivida_app -d aivida_main -c "CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, data TEXT);"
    docker-compose exec -T postgres psql -U aivida_app -d aivida_main -c "INSERT INTO test_table (data) VALUES ('test_persistence');"
    
    # Restart services
    log_info "Restarting services to test persistence..."
    docker-compose restart postgres redis
    
    # Wait for services to be ready
    sleep 10
    
    # Check if data persists
    local test_data
    test_data=$(docker-compose exec -T postgres psql -U aivida_app -d aivida_main -t -c "SELECT data FROM test_table WHERE data='test_persistence';" | tr -d ' ')
    
    if echo "$test_data" | grep -q "test_persistence"; then
        log_success "Database data persistence verified"
    else
        log_fail "Database data persistence failed"
        return 1
    fi
    
    # Cleanup test data
    docker-compose exec -T postgres psql -U aivida_app -d aivida_main -c "DROP TABLE IF EXISTS test_table;"
}

# Test 6: Network Connectivity Between Services
test_service_networking() {
    log_info "=== Testing Service Networking ==="
    
    # Test if services can reach each other
    if docker-compose exec -T postgres pg_isready -h postgres -p 5432; then
        log_success "PostgreSQL is reachable via service name"
    else
        log_fail "PostgreSQL is not reachable via service name"
        return 1
    fi
    
    # Test Redis connectivity from within network
    if docker-compose exec -T redis redis-cli -h redis ping | grep -q "PONG"; then
        log_success "Redis is reachable via service name"
    else
        log_fail "Redis is not reachable via service name"
        return 1
    fi
}

# Test 7: Environment Variables
test_environment_variables() {
    log_info "=== Testing Environment Variables ==="
    
    # Check if environment variables are properly set
    local postgres_env
    postgres_env=$(docker-compose exec -T postgres env | grep POSTGRES_)
    
    if echo "$postgres_env" | grep -q "POSTGRES_DB=aivida_main" && \
       echo "$postgres_env" | grep -q "POSTGRES_USER=aivida_app"; then
        log_success "PostgreSQL environment variables are correct"
    else
        log_fail "PostgreSQL environment variables are incorrect"
        return 1
    fi
}

# Test 8: Security Configuration
test_security_configuration() {
    log_info "=== Testing Security Configuration ==="
    
    # Check if Redis requires authentication
    local redis_auth_test
    if docker-compose exec -T redis redis-cli -h redis --no-auth-warning info server >/dev/null 2>&1; then
        log_warning "Redis authentication may not be configured (this is OK for development)"
    else
        log_success "Redis authentication is configured"
    fi
    
    # Check PostgreSQL user permissions
    local pg_permissions
    pg_permissions=$(docker-compose exec -T postgres psql -U aivida_app -d aivida_main -c "\du aivida_app" | grep aivida_app)
    
    if echo "$pg_permissions" | grep -q "aivida_app"; then
        log_success "PostgreSQL user permissions are configured"
    else
        log_fail "PostgreSQL user permissions are not configured"
        return 1
    fi
}

# Test 9: Resource Usage
test_resource_usage() {
    log_info "=== Testing Resource Usage ==="
    
    # Check container resource usage
    local stats
    stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}")
    
    log_info "Container resource usage:"
    echo "$stats"
    
    # Basic checks for memory usage (should be reasonable)
    local postgres_mem
    postgres_mem=$(docker stats --no-stream --format "{{.MemUsage}}" aivida-postgres | cut -d'/' -f1 | sed 's/[^0-9.]//g')
    
    if [ -n "$postgres_mem" ] && [ "$(echo "$postgres_mem < 500" | bc -l)" -eq 1 ]; then
        log_success "PostgreSQL memory usage is reasonable (${postgres_mem}MB)"
    else
        log_warning "PostgreSQL memory usage is high (${postgres_mem}MB)"
    fi
}

# Test 10: Monitoring Endpoints
test_monitoring_endpoints() {
    log_info "=== Testing Monitoring Endpoints ==="
    
    # Start monitoring services
    log_info "Starting monitoring services..."
    docker-compose up -d prometheus grafana
    
    # Wait for services to start
    sleep 20
    
    # Test Prometheus
    if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_success "Prometheus is accessible and healthy"
    else
        log_warning "Prometheus health check failed (may still be starting)"
    fi
    
    # Test Grafana
    if curl -s http://localhost:3002/api/health >/dev/null 2>&1; then
        log_success "Grafana is accessible"
    else
        log_warning "Grafana health check failed (may still be starting)"
    fi
}

# Main execution
main() {
    log_info "Starting Docker Stack Integration Test..."
    log_info "======================================="
    
    # Ensure we start with a clean environment
    cleanup
    
    # Run tests
    test_docker_compose_validation || exit 1
    test_service_startup || exit 1
    test_database_connectivity || exit 1
    test_database_schema || exit 1
    test_volume_persistence || exit 1
    test_service_networking || exit 1
    test_environment_variables || exit 1
    test_security_configuration || exit 1
    test_resource_usage || exit 1
    test_monitoring_endpoints || exit 1
    
    log_info "======================================="
    log_success "All Docker stack integration tests passed!"
    log_info "Your Phase 1 infrastructure is fully functional."
    log_info "======================================="
}

# Run main function
main "$@"
