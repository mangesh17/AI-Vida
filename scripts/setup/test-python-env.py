#!/usr/bin/env python3
"""
Phase 1 Python Dependencies and Environment Test
Tests Python virtual environment, dependencies, and basic functionality
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path
from typing import List, Tuple, Dict
import json

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_pass(self):
        self.total += 1
        self.passed += 1

    def add_fail(self):
        self.total += 1
        self.failed += 1

    def add_warning(self):
        self.warnings += 1

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[✓ PASS]{Colors.NC} {message}")

def log_fail(message: str):
    print(f"{Colors.RED}[✗ FAIL]{Colors.NC} {message}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def test_python_version() -> bool:
    """Test Python version requirements"""
    log_info("Testing Python version...")
    
    version = sys.version_info
    required_major, required_minor = 3, 11
    
    if version.major >= required_major and version.minor >= required_minor:
        log_success(f"Python version {version.major}.{version.minor}.{version.micro} meets requirements")
        return True
    else:
        log_fail(f"Python {required_major}.{required_minor}+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def test_virtual_environment() -> bool:
    """Test if running in virtual environment"""
    log_info("Testing virtual environment...")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        log_success("Running in virtual environment")
        return True
    else:
        log_fail("Not running in virtual environment")
        return False

def test_pip_installation() -> bool:
    """Test pip and package installation"""
    log_info("Testing pip installation...")
    
    try:
        import pip
        log_success("Pip is available")
        
        # Check pip version
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            log_success(f"Pip version: {result.stdout.strip()}")
            return True
        else:
            log_fail("Pip version check failed")
            return False
    except ImportError:
        log_fail("Pip is not available")
        return False

def test_core_dependencies() -> Tuple[int, int]:
    """Test core Python dependencies"""
    log_info("Testing core Python dependencies...")
    
    # Core dependencies that should be available
    core_deps = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'sqlalchemy': 'Database ORM',
        'psycopg2': 'PostgreSQL adapter',
        'redis': 'Redis client',
        'pydantic': 'Data validation',
        'cryptography': 'Cryptographic functions',
        'httpx': 'HTTP client',
        'jose': 'JWT handling',
        'passlib': 'Password hashing'
    }
    
    passed = 0
    failed = 0
    
    for module, description in core_deps.items():
        try:
            importlib.import_module(module)
            log_success(f"{description} ({module})")
            passed += 1
        except ImportError:
            log_fail(f"{description} ({module}) - not installed")
            failed += 1
    
    return passed, failed

def test_development_dependencies() -> Tuple[int, int]:
    """Test development dependencies"""
    log_info("Testing development dependencies...")
    
    dev_deps = {
        'pytest': 'Testing framework',
        'black': 'Code formatter',
        'isort': 'Import sorter',
        'flake8': 'Linting',
        'mypy': 'Type checking',
        'bandit': 'Security linting'
    }
    
    passed = 0
    failed = 0
    
    for module, description in dev_deps.items():
        try:
            importlib.import_module(module)
            log_success(f"{description} ({module})")
            passed += 1
        except ImportError:
            log_warning(f"{description} ({module}) - not installed (development dependency)")
            failed += 1
    
    return passed, failed

def test_environment_variables() -> bool:
    """Test environment variable configuration"""
    log_info("Testing environment variables...")
    
    # Check for .env.example
    env_example_path = Path('.env.example')
    if not env_example_path.exists():
        log_fail(".env.example file not found")
        return False
    
    log_success(".env.example file exists")
    
    # Read and validate .env.example
    try:
        with open(env_example_path, 'r') as f:
            env_content = f.read()
        
        required_vars = [
            'PROJECT_ID',
            'DATABASE_URL',
            'JWT_SECRET_KEY',
            'ENVIRONMENT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            log_fail(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        else:
            log_success("All required environment variables defined in .env.example")
            return True
    
    except Exception as e:
        log_fail(f"Error reading .env.example: {e}")
        return False

def test_database_connection_string() -> bool:
    """Test database connection string format"""
    log_info("Testing database connection configuration...")
    
    # Test if we can construct a database URL
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.engine.url import make_url
        
        # Test connection string parsing
        test_url = "postgresql://aivida_app:password@localhost:5432/aivida_main"
        parsed_url = make_url(test_url)
        
        if parsed_url.drivername == 'postgresql':
            log_success("Database URL parsing works correctly")
            return True
        else:
            log_fail("Database URL parsing failed")
            return False
    
    except Exception as e:
        log_fail(f"Database connection test failed: {e}")
        return False

def test_ai_dependencies() -> Tuple[int, int]:
    """Test AI/ML dependencies"""
    log_info("Testing AI/ML dependencies...")
    
    ai_deps = {
        'openai': 'OpenAI API client',
        'tiktoken': 'OpenAI tokenizer',
        'langchain': 'LangChain framework'
    }
    
    passed = 0
    failed = 0
    
    for module, description in ai_deps.items():
        try:
            importlib.import_module(module)
            log_success(f"{description} ({module})")
            passed += 1
        except ImportError:
            log_warning(f"{description} ({module}) - not installed (will be needed for AI features)")
            failed += 1
    
    return passed, failed

def test_healthcare_dependencies() -> Tuple[int, int]:
    """Test healthcare-specific dependencies"""
    log_info("Testing healthcare dependencies...")
    
    healthcare_deps = {
        'fhir': 'FHIR resources',
        'hl7apy': 'HL7 message processing'
    }
    
    passed = 0
    failed = 0
    
    for module, description in healthcare_deps.items():
        try:
            importlib.import_module(module)
            log_success(f"{description} ({module})")
            passed += 1
        except ImportError:
            log_warning(f"{description} ({module}) - not installed (will be needed for healthcare integration)")
            failed += 1
    
    return passed, failed

def test_file_processing_dependencies() -> Tuple[int, int]:
    """Test file processing dependencies"""
    log_info("Testing file processing dependencies...")
    
    file_deps = {
        'PyPDF2': 'PDF processing',
        'PIL': 'Image processing (Pillow)',
        'docx': 'Word document processing'
    }
    
    passed = 0
    failed = 0
    
    for module, description in file_deps.items():
        try:
            importlib.import_module(module)
            log_success(f"{description} ({module})")
            passed += 1
        except ImportError:
            log_warning(f"{description} ({module}) - not installed (will be needed for file processing)")
            failed += 1
    
    return passed, failed

def test_basic_functionality() -> bool:
    """Test basic Python functionality that will be needed"""
    log_info("Testing basic functionality...")
    
    try:
        # Test JSON handling
        test_data = {"test": "data", "number": 42}
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        assert parsed_data == test_data
        log_success("JSON processing works")
        
        # Test file operations
        test_file = Path("test_temp_file.txt")
        test_file.write_text("test content")
        content = test_file.read_text()
        test_file.unlink()
        assert content == "test content"
        log_success("File operations work")
        
        # Test datetime
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        assert now.year >= 2024
        log_success("Datetime operations work")
        
        return True
    
    except Exception as e:
        log_fail(f"Basic functionality test failed: {e}")
        return False

def test_security_capabilities() -> bool:
    """Test security-related capabilities"""
    log_info("Testing security capabilities...")
    
    try:
        # Test password hashing
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        password = "test_password"
        hashed = pwd_context.hash(password)
        verified = pwd_context.verify(password, hashed)
        assert verified
        log_success("Password hashing works")
        
        # Test JWT capabilities
        from jose import jwt
        secret = "test_secret_key_32_characters_long"
        payload = {"test": "data"}
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded == payload
        log_success("JWT operations work")
        
        # Test cryptography
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(b"test data")
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == b"test data"
        log_success("Encryption/decryption works")
        
        return True
    
    except Exception as e:
        log_fail(f"Security capabilities test failed: {e}")
        return False

def generate_report(results: TestResults, details: Dict):
    """Generate test report"""
    log_info("=" * 50)
    log_info("PYTHON ENVIRONMENT TEST REPORT")
    log_info("=" * 50)
    
    print(f"Total Tests: {Colors.BLUE}{results.total}{Colors.NC}")
    print(f"Passed: {Colors.GREEN}{results.passed}{Colors.NC}")
    print(f"Failed: {Colors.RED}{results.failed}{Colors.NC}")
    print(f"Warnings: {Colors.YELLOW}{results.warnings}{Colors.NC}")
    
    success_rate = (results.passed / results.total * 100) if results.total > 0 else 0
    print(f"Success Rate: {Colors.BLUE}{success_rate:.1f}%{Colors.NC}")
    
    log_info("\nDETAILS:")
    for category, (passed, failed) in details.items():
        total = passed + failed
        if total > 0:
            rate = passed / total * 100
            status = "✓" if failed == 0 else "⚠" if passed > failed else "✗"
            print(f"  {status} {category}: {passed}/{total} ({rate:.1f}%)")
    
    log_info("=" * 50)
    
    if results.failed == 0:
        log_success("Python environment is ready for Phase 2!")
        return True
    else:
        log_fail("Python environment has issues that need to be resolved.")
        return False

def main():
    """Main test execution"""
    log_info("Starting Python Environment Test...")
    
    results = TestResults()
    details = {}
    
    # Core tests
    if test_python_version():
        results.add_pass()
    else:
        results.add_fail()
    
    if test_virtual_environment():
        results.add_pass()
    else:
        results.add_fail()
    
    if test_pip_installation():
        results.add_pass()
    else:
        results.add_fail()
    
    # Dependency tests
    core_passed, core_failed = test_core_dependencies()
    details["Core Dependencies"] = (core_passed, core_failed)
    results.total += core_passed + core_failed
    results.passed += core_passed
    results.failed += core_failed
    
    dev_passed, dev_failed = test_development_dependencies()
    details["Development Dependencies"] = (dev_passed, dev_failed)
    results.warnings += dev_failed
    
    ai_passed, ai_failed = test_ai_dependencies()
    details["AI/ML Dependencies"] = (ai_passed, ai_failed)
    results.warnings += ai_failed
    
    healthcare_passed, healthcare_failed = test_healthcare_dependencies()
    details["Healthcare Dependencies"] = (healthcare_passed, healthcare_failed)
    results.warnings += healthcare_failed
    
    file_passed, file_failed = test_file_processing_dependencies()
    details["File Processing Dependencies"] = (file_passed, file_failed)
    results.warnings += file_failed
    
    # Functionality tests
    if test_environment_variables():
        results.add_pass()
    else:
        results.add_fail()
    
    if test_database_connection_string():
        results.add_pass()
    else:
        results.add_fail()
    
    if test_basic_functionality():
        results.add_pass()
    else:
        results.add_fail()
    
    if test_security_capabilities():
        results.add_pass()
    else:
        results.add_fail()
    
    # Generate report
    success = generate_report(results, details)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
