# Project Structure

```
AI-Vida/
├── README.md                           # Project overview and quick start
├── .gitignore                         # Git ignore patterns
├── Aivida_Discharge_Copilot_PRD_v2.pdf  # Product Requirements Document
│
├── docs/                              # 📚 Documentation
│   ├── README.md                      # Documentation index
│   │
│   ├── architecture/                  # 🏗️ Architecture Documentation
│   │   └── ARCHITECTURE_DESIGN.md    # Complete system architecture
│   │
│   ├── compliance/                    # 🔒 Compliance Documentation
│   │   └── HIPAA_SECURITY_GUIDE.md   # HIPAA implementation guide
│   │
│   ├── infrastructure/                # 🖥️ Infrastructure Documentation
│   │   └── INFRASTRUCTURE_TEMPLATES.md # Cloud-agnostic templates
│   │
│   └── api/                          # 🔌 API Documentation
│       └── API_SECURITY_PATTERNS.md  # API security patterns
│
├── diagrams/                         # 📊 Visual Diagrams
│   └── aivida_discharge_copilot_backend_diagrams_cloud_agnostic.jsx
│
├── src/                              # 💻 Source Code (Future)
│   ├── backend/                      # Backend services
│   │   ├── api-gateway/              # API Gateway service
│   │   ├── auth-service/             # Authentication service
│   │   ├── ingestion-service/        # Document ingestion
│   │   ├── normalization-service/    # Data normalization
│   │   ├── generation-service/       # Content generation
│   │   ├── chat-service/             # Interactive Q&A
│   │   └── audit-service/            # Audit logging
│   │
│   ├── frontend/                     # Frontend applications
│   │   ├── patient-portal/           # Patient web interface
│   │   ├── clinician-portal/         # Clinician web interface
│   │   ├── admin-portal/             # Admin web interface
│   │   └── mobile-app/               # React Native mobile app
│   │
│   └── shared/                       # Shared libraries
│       ├── models/                   # Data models
│       ├── utils/                    # Utility functions
│       └── types/                    # TypeScript definitions
│
├── infrastructure/                   # 🏗️ Infrastructure as Code
│   ├── terraform/                    # Terraform configurations
│   │   ├── modules/                  # Reusable modules
│   │   │   ├── vpc/                  # Network infrastructure
│   │   │   ├── kubernetes/           # K8s cluster setup
│   │   │   ├── database/             # Database configuration
│   │   │   ├── storage/              # Object storage setup
│   │   │   └── monitoring/           # Observability stack
│   │   │
│   │   ├── environments/             # Environment-specific configs
│   │   │   ├── development/          # Dev environment
│   │   │   ├── staging/              # Staging environment
│   │   │   └── production/           # Production environment
│   │   │
│   │   └── providers/                # Cloud provider configs
│   │       ├── aws/                  # AWS-specific resources
│   │       ├── azure/                # Azure-specific resources
│   │       └── gcp/                  # GCP-specific resources
│   │
│   ├── kubernetes/                   # Kubernetes manifests
│   │   ├── base/                     # Base configurations
│   │   ├── overlays/                 # Environment overlays
│   │   └── charts/                   # Helm charts
│   │
│   └── cloudformation/               # CloudFormation templates (AWS)
│       ├── vpc.yaml                  # VPC setup
│       ├── eks.yaml                  # EKS cluster
│       └── rds.yaml                  # Database setup
│
├── scripts/                          # 🔧 Automation Scripts
│   ├── setup/                        # Environment setup scripts
│   ├── deployment/                   # Deployment automation
│   ├── security/                     # Security scanning tools
│   └── maintenance/                  # Maintenance scripts
│
├── tests/                            # 🧪 Test Suites
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   ├── security/                     # Security tests
│   ├── performance/                  # Load and performance tests
│   └── compliance/                   # HIPAA compliance tests
│
├── configs/                          # ⚙️ Configuration Files
│   ├── development/                  # Development configurations
│   ├── staging/                      # Staging configurations
│   ├── production/                   # Production configurations
│   └── templates/                    # Configuration templates
│
└── tools/                            # 🛠️ Development Tools
    ├── docker/                       # Docker configurations
    ├── ci-cd/                        # CI/CD pipeline definitions
    ├── monitoring/                   # Monitoring configurations
    └── security/                     # Security tool configurations
```

## Directory Purposes

### 📚 `/docs` - Documentation
Complete technical documentation including architecture, compliance, infrastructure, and API guides.

### 📊 `/diagrams` - Visual Documentation  
Interactive diagrams and visual representations of the system architecture.

### 💻 `/src` - Source Code (Future)
Application source code organized by service and component type.

### 🏗️ `/infrastructure` - Infrastructure as Code
Cloud-agnostic infrastructure definitions using Terraform, Kubernetes, and CloudFormation.

### 🔧 `/scripts` - Automation
Scripts for environment setup, deployment, security scanning, and maintenance.

### 🧪 `/tests` - Test Suites
Comprehensive testing including unit, integration, security, and compliance tests.

### ⚙️ `/configs` - Configuration
Environment-specific configuration files and templates.

### 🛠️ `/tools` - Development Tools
Development, CI/CD, monitoring, and security tool configurations.

## File Naming Conventions

### Documentation Files
- Use uppercase with underscores: `ARCHITECTURE_DESIGN.md`
- Include descriptive names: `HIPAA_SECURITY_GUIDE.md`
- Version when needed: `API_SPEC_v1.md`

### Code Files
- Use kebab-case for directories: `api-gateway/`
- Use camelCase for TypeScript/JavaScript: `userService.ts`
- Use snake_case for Python: `user_service.py`
- Use PascalCase for React components: `PatientPortal.tsx`

### Infrastructure Files
- Use descriptive names: `vpc-setup.tf`
- Include environment: `production-cluster.yaml`
- Use provider prefixes when needed: `aws-rds.tf`

### Configuration Files
- Use environment prefixes: `dev.env`, `prod.env`
- Use service suffixes: `database.config.yaml`
- Include purpose: `monitoring.prometheus.yaml`

## Security Considerations

### Sensitive Files
- Never commit secrets, keys, or credentials
- Use `.env` files for local development only
- Store production secrets in secure key management systems
- Use encrypted configuration for sensitive settings

### Access Control
- Implement least privilege access
- Use role-based access control (RBAC)
- Audit file access and modifications
- Encrypt sensitive documentation

### Compliance
- Maintain audit trails for all changes
- Document security controls and procedures
- Regular security assessments and reviews
- HIPAA compliance validation
