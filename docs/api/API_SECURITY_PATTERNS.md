# API Security and Integration Patterns

## Overview
This document outlines the API security patterns, integration strategies, and implementation guidelines for the Aivida Discharge Copilot platform, ensuring HIPAA compliance and robust security controls.

## Table of Contents
1. [API Security Architecture](#api-security-architecture)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection Patterns](#data-protection-patterns)
4. [Integration Patterns](#integration-patterns)
5. [Rate Limiting & DDoS Protection](#rate-limiting--ddos-protection)
6. [Audit & Monitoring](#audit--monitoring)
7. [Error Handling & Security](#error-handling--security)

## API Security Architecture

### Zero Trust API Gateway
```yaml
API Gateway Security Layers:
  Layer 1 - Perimeter Security:
    - WAF (Web Application Firewall)
    - DDoS protection
    - Geo-blocking for unauthorized regions
    - IP allowlisting for administrative access
  
  Layer 2 - Authentication:
    - OAuth 2.0 / OpenID Connect
    - JWT token validation
    - Multi-factor authentication for PHI access
    - Certificate-based authentication for B2B
  
  Layer 3 - Authorization:
    - Role-based access control (RBAC)
    - Attribute-based access control (ABAC)
    - Resource-level permissions
    - Minimum necessary access principle
  
  Layer 4 - Data Protection:
    - Request/response encryption
    - PHI field-level encryption
    - Data masking and filtering
    - Content validation and sanitization
  
  Layer 5 - Monitoring:
    - Real-time threat detection
    - Audit logging
    - Performance monitoring
    - Compliance reporting
```

### API Security Implementation
```python
# api_gateway/security/middleware.py
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet
import jwt

class HIPAASecurityMiddleware:
    """
    Comprehensive security middleware for HIPAA-compliant APIs
    """
    
    def __init__(self, 
                 jwt_secret: str,
                 encryption_key: bytes,
                 audit_logger: 'AuditLogger',
                 rate_limiter: 'RateLimiter'):
        self.jwt_secret = jwt_secret
        self.cipher = Fernet(encryption_key)
        self.audit_logger = audit_logger
        self.rate_limiter = rate_limiter
        self.security_scheme = HTTPBearer()
    
    async def __call__(self, request: Request, call_next):
        """
        Process security middleware for each request
        """
        start_time = time.time()
        
        try:
            # 1. Rate limiting check
            await self._check_rate_limit(request)
            
            # 2. Authentication
            user_context = await self._authenticate_request(request)
            
            # 3. Authorization
            await self._authorize_request(request, user_context)
            
            # 4. Request validation and sanitization
            await self._validate_request(request)
            
            # 5. Process request
            response = await call_next(request)
            
            # 6. Response filtering and encryption
            response = await self._process_response(response, user_context)
            
            # 7. Audit logging
            await self._log_request(request, response, user_context, start_time)
            
            return response
            
        except Exception as e:
            # Log security exception
            await self._log_security_exception(request, e, start_time)
            raise
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        Authenticate request using JWT tokens
        """
        # Extract authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            
            # Additional token validation
            await self._validate_token_claims(payload, request)
            
            return {
                'user_id': payload.get('sub'),
                'roles': payload.get('roles', []),
                'permissions': payload.get('permissions', []),
                'session_id': payload.get('session_id'),
                'mfa_verified': payload.get('mfa_verified', False)
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def _authorize_request(self, request: Request, user_context: Dict[str, Any]):
        """
        Authorize request based on RBAC and ABAC
        """
        endpoint = request.url.path
        method = request.method
        
        # Check role-based permissions
        required_role = self._get_required_role(endpoint, method)
        if required_role and required_role not in user_context['roles']:
            raise HTTPException(status_code=403, detail="Insufficient role permissions")
        
        # Check PHI access requirements
        if self._is_phi_endpoint(endpoint):
            if not user_context.get('mfa_verified'):
                raise HTTPException(status_code=403, detail="MFA required for PHI access")
            
            # Apply minimum necessary access principle
            await self._check_minimum_necessary_access(request, user_context)
    
    async def _validate_request(self, request: Request):
        """
        Validate and sanitize request content
        """
        # Content type validation
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise HTTPException(status_code=400, detail="Invalid content type")
        
        # Request size validation
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="Request too large")
        
        # SQL injection and XSS protection
        if hasattr(request, 'json'):
            request_body = await request.json()
            await self._sanitize_input(request_body)
    
    async def _process_response(self, response: Response, user_context: Dict[str, Any]) -> Response:
        """
        Process response with PHI filtering and encryption
        """
        # Check if response contains PHI
        if hasattr(response, 'body') and self._contains_phi(response.body):
            # Apply field-level filtering based on user permissions
            filtered_body = await self._filter_phi_fields(response.body, user_context)
            
            # Encrypt sensitive fields
            encrypted_body = await self._encrypt_sensitive_fields(filtered_body)
            
            # Update response
            response.body = encrypted_body
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    async def _check_rate_limit(self, request: Request):
        """
        Implement rate limiting with different tiers
        """
        client_ip = self._get_client_ip(request)
        user_id = self._extract_user_id_from_token(request)
        
        # Different limits based on endpoint and user type
        if self._is_phi_endpoint(request.url.path):
            limit = await self.rate_limiter.check_phi_limit(user_id, client_ip)
        elif self._is_admin_endpoint(request.url.path):
            limit = await self.rate_limiter.check_admin_limit(user_id, client_ip)
        else:
            limit = await self.rate_limiter.check_general_limit(user_id, client_ip)
        
        if not limit.allowed:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Try again in {limit.retry_after} seconds"
            )
```

## Authentication & Authorization

### OAuth 2.0 + OpenID Connect Implementation
```python
# auth/oauth_provider.py
from authlib.integrations.fastapi_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import CodeChallenge
import secrets
import hashlib

class HIPAAOAuthServer(AuthorizationServer):
    """
    HIPAA-compliant OAuth 2.0 authorization server
    """
    
    def __init__(self, app, audit_logger: 'AuditLogger'):
        super().__init__(app)
        self.audit_logger = audit_logger
        
        # Register grant types
        self.register_grant(AuthorizationCodeGrant, [CodeChallenge(required=True)])
        self.register_grant(RefreshTokenGrant)
        self.register_grant(ClientCredentialsGrant)
        
        # Register endpoints
        self.register_endpoint(RevocationEndpoint)
        self.register_endpoint(IntrospectionEndpoint)

class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    """
    Enhanced authorization code grant with HIPAA requirements
    """
    
    def save_authorization_credential(self, credential):
        """
        Save authorization code with audit trail
        """
        # Generate secure authorization code
        auth_code = secrets.token_urlsafe(32)
        
        # Store with expiration (short-lived for security)
        credential.code = auth_code
        credential.expires_at = time.time() + 600  # 10 minutes
        
        # Audit log
        self.audit_logger.log_event({
            'event_type': 'authorization_code_issued',
            'client_id': credential.client_id,
            'user_id': credential.user_id,
            'scope': credential.scope,
            'code_challenge_method': credential.code_challenge_method,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return credential.save()
    
    def authenticate_user(self, authorization_request):
        """
        Authenticate user with MFA for PHI access
        """
        # Standard username/password authentication
        user = self._authenticate_primary_credentials(authorization_request)
        if not user:
            return None
        
        # Check if requested scope requires PHI access
        scopes = authorization_request.scope.split(' ')
        requires_phi_access = any(scope.startswith('phi:') for scope in scopes)
        
        if requires_phi_access:
            # Require MFA for PHI access
            mfa_verified = self._verify_mfa(user, authorization_request)
            if not mfa_verified:
                raise HTTPException(status_code=401, detail="MFA required for PHI access")
            
            user.mfa_verified = True
        
        return user

class TokenGenerator:
    """
    HIPAA-compliant JWT token generator
    """
    
    def __init__(self, secret_key: str, audit_logger: 'AuditLogger'):
        self.secret_key = secret_key
        self.audit_logger = audit_logger
    
    def generate_access_token(self, user: 'User', client: 'Client', scope: str) -> str:
        """
        Generate access token with HIPAA-specific claims
        """
        now = datetime.utcnow()
        
        # Shorter expiration for PHI access
        phi_access = any(s.startswith('phi:') for s in scope.split(' '))
        expires_in = 900 if phi_access else 3600  # 15 min vs 1 hour
        
        payload = {
            'iss': 'aivida.com',
            'sub': str(user.id),
            'aud': client.client_id,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=expires_in)).timestamp()),
            'scope': scope,
            'roles': user.roles,
            'permissions': self._calculate_permissions(user, scope),
            'session_id': str(uuid.uuid4()),
            'mfa_verified': getattr(user, 'mfa_verified', False),
            'phi_access': phi_access
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Audit log token issuance
        self.audit_logger.log_event({
            'event_type': 'access_token_issued',
            'user_id': user.id,
            'client_id': client.client_id,
            'scope': scope,
            'expires_in': expires_in,
            'phi_access': phi_access,
            'timestamp': now.isoformat()
        })
        
        return token
    
    def _calculate_permissions(self, user: 'User', scope: str) -> List[str]:
        """
        Calculate fine-grained permissions based on role and scope
        """
        permissions = []
        scopes = scope.split(' ')
        
        for user_role in user.roles:
            role_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            for scope_item in scopes:
                # Map scopes to specific permissions
                scope_permissions = SCOPE_PERMISSIONS.get(scope_item, [])
                
                # Apply intersection of role and scope permissions
                applicable_permissions = set(role_permissions) & set(scope_permissions)
                permissions.extend(applicable_permissions)
        
        return list(set(permissions))

# Permission mappings
ROLE_PERMISSIONS = {
    'patient': [
        'read:own_records',
        'read:own_instructions',
        'read:own_appointments',
        'create:own_messages'
    ],
    'clinician': [
        'read:patient_records',
        'write:patient_records',
        'read:patient_instructions',
        'write:patient_instructions',
        'read:appointments',
        'write:appointments',
        'approve:discharge_packets'
    ],
    'admin': [
        'read:system_config',
        'write:system_config',
        'read:audit_logs',
        'manage:users',
        'read:analytics'
    ]
}

SCOPE_PERMISSIONS = {
    'phi:read': ['read:patient_records', 'read:patient_instructions'],
    'phi:write': ['write:patient_records', 'write:patient_instructions'],
    'appointments:read': ['read:appointments'],
    'appointments:write': ['write:appointments'],
    'profile:read': ['read:own_profile'],
    'profile:write': ['write:own_profile']
}
```

## Data Protection Patterns

### Field-Level Encryption
```python
# security/field_encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from typing import Dict, Any, List

class FieldLevelEncryption:
    """
    Implements field-level encryption for PHI data
    """
    
    def __init__(self, master_key: bytes):
        self.master_key = master_key
        self.field_keys = {}
        
        # Define PHI fields that require encryption
        self.phi_fields = {
            'patient_name', 'ssn', 'date_of_birth', 'address',
            'phone_number', 'email', 'medical_record_number',
            'insurance_id', 'emergency_contact'
        }
    
    def _get_field_key(self, field_name: str) -> bytes:
        """
        Derive field-specific encryption key
        """
        if field_name not in self.field_keys:
            # Derive field-specific key from master key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=field_name.encode(),
                iterations=100000,
            )
            field_key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
            self.field_keys[field_name] = field_key
        
        return self.field_keys[field_name]
    
    def encrypt_phi_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt PHI fields in data structure
        """
        encrypted_data = data.copy()
        
        for field_name, value in data.items():
            if field_name in self.phi_fields and value is not None:
                field_key = self._get_field_key(field_name)
                cipher = Fernet(field_key)
                
                # Convert value to string for encryption
                value_str = json.dumps(value) if not isinstance(value, str) else value
                encrypted_value = cipher.encrypt(value_str.encode())
                
                # Store as base64 string with field identifier
                encrypted_data[field_name] = {
                    'encrypted': True,
                    'value': base64.b64encode(encrypted_value).decode(),
                    'field': field_name
                }
        
        return encrypted_data
    
    def decrypt_phi_fields(self, data: Dict[str, Any], 
                          user_permissions: List[str]) -> Dict[str, Any]:
        """
        Decrypt PHI fields based on user permissions
        """
        decrypted_data = data.copy()
        
        for field_name, value in data.items():
            if (isinstance(value, dict) and 
                value.get('encrypted') and 
                self._user_can_access_field(field_name, user_permissions)):
                
                field_key = self._get_field_key(field_name)
                cipher = Fernet(field_key)
                
                try:
                    encrypted_bytes = base64.b64decode(value['value'].encode())
                    decrypted_value = cipher.decrypt(encrypted_bytes).decode()
                    
                    # Try to parse as JSON, fallback to string
                    try:
                        decrypted_data[field_name] = json.loads(decrypted_value)
                    except json.JSONDecodeError:
                        decrypted_data[field_name] = decrypted_value
                        
                except Exception:
                    # If decryption fails, remove field
                    decrypted_data[field_name] = None
            
            elif isinstance(value, dict) and value.get('encrypted'):
                # User doesn't have permission, mask the field
                decrypted_data[field_name] = "[REDACTED]"
        
        return decrypted_data
    
    def _user_can_access_field(self, field_name: str, permissions: List[str]) -> bool:
        """
        Check if user has permission to access specific PHI field
        """
        # Map fields to required permissions
        field_permissions = {
            'patient_name': 'phi:demographics',
            'ssn': 'phi:identifiers',
            'date_of_birth': 'phi:demographics',
            'address': 'phi:contact',
            'phone_number': 'phi:contact',
            'email': 'phi:contact',
            'medical_record_number': 'phi:identifiers',
            'insurance_id': 'phi:financial',
            'emergency_contact': 'phi:contact'
        }
        
        required_permission = field_permissions.get(field_name, 'phi:read')
        return required_permission in permissions

class PHIMaskingService:
    """
    Service for masking PHI data based on user context
    """
    
    def __init__(self):
        self.masking_rules = {
            'patient_name': self._mask_name,
            'ssn': self._mask_ssn,
            'phone_number': self._mask_phone,
            'email': self._mask_email,
            'address': self._mask_address,
            'date_of_birth': self._mask_date_of_birth
        }
    
    def mask_phi_data(self, data: Dict[str, Any], 
                     user_permissions: List[str]) -> Dict[str, Any]:
        """
        Apply PHI masking based on user permissions
        """
        masked_data = data.copy()
        
        for field_name, value in data.items():
            if field_name in self.masking_rules:
                if not self._has_field_permission(field_name, user_permissions):
                    masking_func = self.masking_rules[field_name]
                    masked_data[field_name] = masking_func(value)
        
        return masked_data
    
    def _mask_name(self, name: str) -> str:
        """Mask patient name partially"""
        if not name:
            return name
        
        parts = name.split(' ')
        if len(parts) == 1:
            return f"{parts[0][0]}***"
        else:
            return f"{parts[0][0]}*** {parts[-1][0]}***"
    
    def _mask_ssn(self, ssn: str) -> str:
        """Mask SSN showing only last 4 digits"""
        if not ssn:
            return ssn
        
        # Remove any formatting
        clean_ssn = ''.join(filter(str.isdigit, ssn))
        if len(clean_ssn) >= 4:
            return f"***-**-{clean_ssn[-4:]}"
        return "***-**-****"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number showing only area code"""
        if not phone:
            return phone
        
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) >= 10:
            return f"({clean_phone[:3]}) ***-****"
        return "(***) ***-****"
    
    def _mask_email(self, email: str) -> str:
        """Mask email preserving domain"""
        if not email or '@' not in email:
            return "***@***.***"
        
        local, domain = email.split('@', 1)
        masked_local = f"{local[0]}***" if local else "***"
        return f"{masked_local}@{domain}"
    
    def _mask_address(self, address: str) -> str:
        """Mask address showing only city/state"""
        if not address:
            return address
        
        # Simple masking - in production, use more sophisticated parsing
        return "*** [STREET ADDRESS REDACTED] ***"
    
    def _mask_date_of_birth(self, dob: str) -> str:
        """Mask DOB showing only year"""
        if not dob:
            return dob
        
        # Assuming ISO format date
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(dob.replace('Z', '+00:00'))
            return f"**/*/{date_obj.year}"
        except:
            return "**/**/****"
```

## Integration Patterns

### EHR Integration with FHIR
```python
# integrations/fhir_client.py
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

class FHIRClient:
    """
    HIPAA-compliant FHIR client for EHR integration
    """
    
    def __init__(self, 
                 base_url: str,
                 client_id: str,
                 client_secret: str,
                 audit_logger: 'AuditLogger'):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.audit_logger = audit_logger
        self.session = None
        self.access_token = None
        self.token_expires_at = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=True, limit=10)
        )
        await self._authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _authenticate(self):
        """
        Authenticate with EHR system using client credentials
        """
        auth_url = f"{self.base_url}/oauth2/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'patient/*.read encounter/*.read'
        }
        
        try:
            async with self.session.post(auth_url, data=auth_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    # Audit log authentication
                    self.audit_logger.log_event({
                        'event_type': 'fhir_authentication',
                        'ehr_system': self.base_url,
                        'client_id': self.client_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                else:
                    raise Exception(f"Authentication failed: {response.status}")
                    
        except Exception as e:
            self.audit_logger.log_event({
                'event_type': 'fhir_authentication_failed',
                'ehr_system': self.base_url,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            raise
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if (not self.access_token or 
            not self.token_expires_at or 
            datetime.utcnow() >= self.token_expires_at - timedelta(minutes=5)):
            await self._authenticate()
    
    async def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve patient demographics from FHIR server
        """
        await self._ensure_authenticated()
        
        url = f"{self.base_url}/Patient/{patient_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    patient_data = await response.json()
                    
                    # Audit log PHI access
                    self.audit_logger.log_event({
                        'event_type': 'fhir_patient_access',
                        'patient_id': patient_id,
                        'ehr_system': self.base_url,
                        'data_type': 'Patient',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    return patient_data
                elif response.status == 404:
                    return None
                else:
                    raise Exception(f"Failed to retrieve patient: {response.status}")
                    
        except Exception as e:
            self.audit_logger.log_event({
                'event_type': 'fhir_access_error',
                'patient_id': patient_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            raise
    
    async def get_patient_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve patient medications from FHIR server
        """
        await self._ensure_authenticated()
        
        url = f"{self.base_url}/MedicationStatement"
        params = {
            'patient': patient_id,
            '_sort': '-effective',
            '_count': 100
        }
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/fhir+json'
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    bundle = await response.json()
                    medications = bundle.get('entry', [])
                    
                    # Audit log
                    self.audit_logger.log_event({
                        'event_type': 'fhir_medication_access',
                        'patient_id': patient_id,
                        'medication_count': len(medications),
                        'ehr_system': self.base_url,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    return [entry['resource'] for entry in medications]
                else:
                    raise Exception(f"Failed to retrieve medications: {response.status}")
                    
        except Exception as e:
            self.audit_logger.log_event({
                'event_type': 'fhir_medication_error',
                'patient_id': patient_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            raise

class FHIRDataNormalizer:
    """
    Normalizes FHIR data to internal format
    """
    
    def normalize_patient(self, fhir_patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert FHIR Patient resource to internal patient format
        """
        normalized = {
            'external_id': fhir_patient.get('id'),
            'name': self._extract_name(fhir_patient),
            'gender': fhir_patient.get('gender'),
            'birth_date': fhir_patient.get('birthDate'),
            'address': self._extract_address(fhir_patient),
            'phone': self._extract_phone(fhir_patient),
            'email': self._extract_email(fhir_patient),
            'identifiers': self._extract_identifiers(fhir_patient)
        }
        
        return normalized
    
    def normalize_medication(self, fhir_medication: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert FHIR MedicationStatement to internal format
        """
        normalized = {
            'external_id': fhir_medication.get('id'),
            'medication_code': self._extract_medication_code(fhir_medication),
            'medication_name': self._extract_medication_name(fhir_medication),
            'dosage': self._extract_dosage(fhir_medication),
            'frequency': self._extract_frequency(fhir_medication),
            'start_date': self._extract_effective_date(fhir_medication),
            'status': fhir_medication.get('status', 'unknown')
        }
        
        return normalized
    
    def _extract_name(self, patient: Dict[str, Any]) -> str:
        """Extract patient name from FHIR Patient resource"""
        names = patient.get('name', [])
        if names:
            name = names[0]  # Use first name
            given = ' '.join(name.get('given', []))
            family = ' '.join(name.get('family', []) if isinstance(name.get('family'), list) else [name.get('family', '')])
            return f"{given} {family}".strip()
        return ""
    
    def _extract_address(self, patient: Dict[str, Any]) -> str:
        """Extract primary address from FHIR Patient resource"""
        addresses = patient.get('address', [])
        for addr in addresses:
            if addr.get('use') == 'home' or not addresses:
                lines = addr.get('line', [])
                city = addr.get('city', '')
                state = addr.get('state', '')
                postal = addr.get('postalCode', '')
                
                address_parts = []
                if lines:
                    address_parts.extend(lines)
                if city:
                    address_parts.append(city)
                if state:
                    address_parts.append(state)
                if postal:
                    address_parts.append(postal)
                
                return ', '.join(address_parts)
        return ""
```

## Rate Limiting & DDoS Protection

### Intelligent Rate Limiting
```python
# security/rate_limiting.py
import asyncio
import time
from typing import Dict, Optional, NamedTuple
from enum import Enum
import redis.asyncio as redis

class RateLimitTier(Enum):
    GENERAL = "general"
    PHI_ACCESS = "phi_access"
    ADMIN = "admin"
    BULK_OPERATION = "bulk_operation"

class RateLimitResult(NamedTuple):
    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None

class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with different tiers and threat detection
    """
    
    def __init__(self, redis_client: redis.Redis, audit_logger: 'AuditLogger'):
        self.redis = redis_client
        self.audit_logger = audit_logger
        
        # Rate limit configurations per tier
        self.limits = {
            RateLimitTier.GENERAL: {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'burst_allowance': 10
            },
            RateLimitTier.PHI_ACCESS: {
                'requests_per_minute': 30,
                'requests_per_hour': 300,
                'burst_allowance': 5
            },
            RateLimitTier.ADMIN: {
                'requests_per_minute': 100,
                'requests_per_hour': 2000,
                'burst_allowance': 20
            },
            RateLimitTier.BULK_OPERATION: {
                'requests_per_minute': 5,
                'requests_per_hour': 50,
                'burst_allowance': 2
            }
        }
    
    async def check_rate_limit(self, 
                              identifier: str,
                              tier: RateLimitTier,
                              endpoint: str = None) -> RateLimitResult:
        """
        Check rate limit for given identifier and tier
        """
        now = int(time.time())
        minute_window = now // 60
        hour_window = now // 3600
        
        limits = self.limits[tier]
        
        # Redis keys for different time windows
        minute_key = f"rate_limit:{tier.value}:{identifier}:minute:{minute_window}"
        hour_key = f"rate_limit:{tier.value}:{identifier}:hour:{hour_window}"
        burst_key = f"rate_limit:{tier.value}:{identifier}:burst"
        
        pipe = self.redis.pipeline()
        
        # Check current counts
        pipe.get(minute_key)
        pipe.get(hour_key)
        pipe.get(burst_key)
        
        results = await pipe.execute()
        
        minute_count = int(results[0] or 0)
        hour_count = int(results[1] or 0)
        burst_count = int(results[2] or 0)
        
        # Check if limits exceeded
        if minute_count >= limits['requests_per_minute']:
            await self._log_rate_limit_exceeded(identifier, tier, 'minute', endpoint)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=(minute_window + 1) * 60,
                retry_after=60 - (now % 60)
            )
        
        if hour_count >= limits['requests_per_hour']:
            await self._log_rate_limit_exceeded(identifier, tier, 'hour', endpoint)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=(hour_window + 1) * 3600,
                retry_after=3600 - (now % 3600)
            )
        
        # Check burst limit (sliding window)
        if burst_count >= limits['burst_allowance']:
            burst_window_start = now - 10  # 10 second burst window
            burst_requests = await self._count_requests_in_window(
                identifier, tier, burst_window_start, now
            )
            
            if burst_requests >= limits['burst_allowance']:
                await self._log_rate_limit_exceeded(identifier, tier, 'burst', endpoint)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=now + 10,
                    retry_after=10
                )
        
        # Increment counters
        pipe = self.redis.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        pipe.incr(burst_key)
        pipe.expire(burst_key, 10)
        
        await pipe.execute()
        
        # Check for suspicious patterns
        await self._analyze_request_patterns(identifier, tier, endpoint)
        
        return RateLimitResult(
            allowed=True,
            remaining=limits['requests_per_minute'] - minute_count - 1,
            reset_time=(minute_window + 1) * 60
        )
    
    async def _analyze_request_patterns(self, 
                                      identifier: str,
                                      tier: RateLimitTier,
                                      endpoint: str):
        """
        Analyze request patterns for suspicious activity
        """
        # Get request history for the last 5 minutes
        now = int(time.time())
        history_key = f"request_history:{identifier}"
        
        # Store request timestamp and endpoint
        await self.redis.lpush(history_key, f"{now}:{tier.value}:{endpoint}")
        await self.redis.expire(history_key, 300)  # 5 minutes
        
        # Get recent requests
        recent_requests = await self.redis.lrange(history_key, 0, 100)
        
        # Analyze patterns
        if len(recent_requests) > 50:  # High volume
            endpoints = [req.decode().split(':')[2] for req in recent_requests[:20]]
            unique_endpoints = set(endpoints)
            
            # Check for endpoint scanning (many different endpoints)
            if len(unique_endpoints) > 15:
                await self._flag_suspicious_activity(
                    identifier, 'endpoint_scanning', {
                        'unique_endpoints': len(unique_endpoints),
                        'total_requests': len(recent_requests)
                    }
                )
            
            # Check for repeated failed attempts to same endpoint
            endpoint_counts = {}
            for endpoint in endpoints:
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
            max_endpoint_count = max(endpoint_counts.values()) if endpoint_counts else 0
            if max_endpoint_count > 10:
                await self._flag_suspicious_activity(
                    identifier, 'repeated_endpoint_access', {
                        'endpoint': max(endpoint_counts, key=endpoint_counts.get),
                        'count': max_endpoint_count
                    }
                )
    
    async def _flag_suspicious_activity(self, 
                                      identifier: str,
                                      activity_type: str,
                                      details: Dict):
        """
        Flag suspicious activity for security review
        """
        self.audit_logger.log_event({
            'event_type': 'suspicious_activity_detected',
            'identifier': identifier,
            'activity_type': activity_type,
            'details': details,
            'timestamp': time.time(),
            'severity': 'high'
        })
        
        # Temporarily increase rate limiting for this identifier
        temp_limit_key = f"temp_limit:{identifier}"
        await self.redis.setex(temp_limit_key, 3600, "restricted")  # 1 hour

class DDoSProtection:
    """
    DDoS protection with automatic mitigation
    """
    
    def __init__(self, redis_client: redis.Redis, audit_logger: 'AuditLogger'):
        self.redis = redis_client
        self.audit_logger = audit_logger
        self.protection_levels = {
            'low': {'threshold': 1000, 'action': 'monitor'},
            'medium': {'threshold': 5000, 'action': 'rate_limit'},
            'high': {'threshold': 10000, 'action': 'block_suspicious'},
            'critical': {'threshold': 50000, 'action': 'emergency_block'}
        }
    
    async def check_ddos_protection(self, request_info: Dict) -> Dict[str, Any]:
        """
        Check for DDoS attack patterns and apply mitigation
        """
        now = int(time.time())
        minute_window = now // 60
        
        # Count requests in current minute window
        total_requests_key = f"ddos:total:{minute_window}"
        ip_requests_key = f"ddos:ip:{request_info['source_ip']}:{minute_window}"
        
        pipe = self.redis.pipeline()
        pipe.incr(total_requests_key)
        pipe.expire(total_requests_key, 60)
        pipe.incr(ip_requests_key)
        pipe.expire(ip_requests_key, 60)
        
        results = await pipe.execute()
        total_requests = results[0]
        ip_requests = results[1]
        
        # Determine protection level
        protection_level = self._determine_protection_level(total_requests)
        
        # Check for single IP flooding
        if ip_requests > 100:  # Single IP making > 100 requests/minute
            await self._apply_ip_mitigation(request_info['source_ip'], ip_requests)
            return {
                'action': 'block',
                'reason': 'ip_flooding',
                'ip_requests': ip_requests
            }
        
        # Apply protection based on level
        if protection_level['action'] == 'emergency_block':
            # Block all non-whitelisted IPs
            if not await self._is_whitelisted_ip(request_info['source_ip']):
                return {
                    'action': 'block',
                    'reason': 'emergency_ddos_protection',
                    'total_requests': total_requests
                }
        
        elif protection_level['action'] == 'block_suspicious':
            # Use ML-based suspicious request detection
            is_suspicious = await self._detect_suspicious_request(request_info)
            if is_suspicious:
                return {
                    'action': 'block',
                    'reason': 'suspicious_pattern',
                    'total_requests': total_requests
                }
        
        return {
            'action': 'allow',
            'protection_level': protection_level,
            'total_requests': total_requests
        }
```

This comprehensive API security framework provides robust protection for the Aivida Discharge Copilot platform while maintaining HIPAA compliance. The implementation includes multi-layered security controls, intelligent rate limiting, comprehensive audit logging, and adaptive threat protection.
