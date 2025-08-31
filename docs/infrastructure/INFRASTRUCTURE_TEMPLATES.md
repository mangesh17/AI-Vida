# Cloud-Agnostic Infrastructure Templates

## Overview
This directory contains Infrastructure as Code (IaC) templates for deploying the Aivida Discharge Copilot platform across different cloud providers while maintaining HIPAA compliance and security best practices.

## Provider Support
- **AWS**: CloudFormation and Terraform
- **Azure**: ARM Templates and Terraform  
- **Google Cloud**: Deployment Manager and Terraform
- **Multi-Cloud**: Terraform with provider abstraction

## Common Infrastructure Components

### 1. Virtual Private Cloud (VPC) / Virtual Network

#### AWS Implementation
```yaml
# cloudformation/vpc.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'HIPAA-compliant VPC for Aivida Discharge Copilot'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]
  
  VpcCidr:
    Type: String
    Default: 10.0.0.0/16
    Description: CIDR block for VPC

Resources:
  # VPC with DNS support
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub 'aivida-vpc-${Environment}'
        - Key: Environment
          Value: !Ref Environment
        - Key: Compliance
          Value: HIPAA

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub 'aivida-igw-${Environment}'

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Public Subnets for Load Balancers
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Sub '10.0.1.0/24'
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value: !Sub 'aivida-public-subnet-1-${Environment}'
        - Key: Type
          Value: Public

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Sub '10.0.2.0/24'
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value: !Sub 'aivida-public-subnet-2-${Environment}'
        - Key: Type
          Value: Public

  # Private Subnets for Applications
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Sub '10.0.11.0/24'
      Tags:
        - Key: Name
          Value: !Sub 'aivida-private-subnet-1-${Environment}'
        - Key: Type
          Value: Private
        - Key: Tier
          Value: Application

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Sub '10.0.12.0/24'
      Tags:
        - Key: Name
          Value: !Sub 'aivida-private-subnet-2-${Environment}'
        - Key: Type
          Value: Private
        - Key: Tier
          Value: Application

  # Database Subnets
  DatabaseSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Sub '10.0.21.0/24'
      Tags:
        - Key: Name
          Value: !Sub 'aivida-database-subnet-1-${Environment}'
        - Key: Type
          Value: Private
        - Key: Tier
          Value: Database

  DatabaseSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Sub '10.0.22.0/24'
      Tags:
        - Key: Name
          Value: !Sub 'aivida-database-subnet-2-${Environment}'
        - Key: Type
          Value: Private
        - Key: Tier
          Value: Database

  # NAT Gateways for private subnet internet access
  NatGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc

  NatGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1

  # Route Tables
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub 'aivida-public-routes-${Environment}'

  DefaultPublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet1

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet2

  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub 'aivida-private-routes-1-${Environment}'

  DefaultPrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway1

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      SubnetId: !Ref PrivateSubnet1

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      SubnetId: !Ref PrivateSubnet2

  # VPC Flow Logs for security monitoring
  VPCFlowLogsRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: vpc-flow-logs.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: flowlogsDeliveryRolePolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - logs:DescribeLogGroups
                  - logs:DescribeLogStreams
                Resource: '*'

  VPCFlowLogsLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/vpc/flowlogs/${Environment}'
      RetentionInDays: 365

  VPCFlowLogs:
    Type: AWS::EC2::FlowLog
    Properties:
      ResourceType: VPC
      ResourceId: !Ref VPC
      TrafficType: ALL
      LogDestinationType: cloud-watch-logs
      LogGroupName: !Ref VPCFlowLogsLogGroup
      DeliverLogsPermissionArn: !GetAtt VPCFlowLogsRole.Arn

Outputs:
  VPC:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub '${AWS::StackName}-VPC'

  PublicSubnets:
    Description: Public subnet IDs
    Value: !Join [',', [!Ref PublicSubnet1, !Ref PublicSubnet2]]
    Export:
      Name: !Sub '${AWS::StackName}-PublicSubnets'

  PrivateSubnets:
    Description: Private subnet IDs
    Value: !Join [',', [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]
    Export:
      Name: !Sub '${AWS::StackName}-PrivateSubnets'

  DatabaseSubnets:
    Description: Database subnet IDs
    Value: !Join [',', [!Ref DatabaseSubnet1, !Ref DatabaseSubnet2]]
    Export:
      Name: !Sub '${AWS::StackName}-DatabaseSubnets'
```

#### Terraform Multi-Cloud VPC Module
```hcl
# terraform/modules/vpc/main.tf
variable "cloud_provider" {
  description = "Cloud provider (aws, azure, gcp)"
  type        = string
  validation {
    condition     = contains(["aws", "azure", "gcp"], var.cloud_provider)
    error_message = "Supported providers: aws, azure, gcp."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}

# AWS VPC Implementation
resource "aws_vpc" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "aivida-vpc-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    ManagedBy   = "Terraform"
  }
}

resource "aws_internet_gateway" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name = "aivida-igw-${var.environment}"
  }
}

# Public subnets
resource "aws_subnet" "public" {
  count = var.cloud_provider == "aws" ? var.availability_zones : 0
  
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + 1)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = false

  tags = {
    Name = "aivida-public-subnet-${count.index + 1}-${var.environment}"
    Type = "Public"
    Tier = "DMZ"
  }
}

# Private subnets for applications
resource "aws_subnet" "private" {
  count = var.cloud_provider == "aws" ? var.availability_zones : 0
  
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + 11)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "aivida-private-subnet-${count.index + 1}-${var.environment}"
    Type = "Private"
    Tier = "Application"
  }
}

# Database subnets
resource "aws_subnet" "database" {
  count = var.cloud_provider == "aws" ? var.availability_zones : 0
  
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + 21)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "aivida-database-subnet-${count.index + 1}-${var.environment}"
    Type = "Private"
    Tier = "Database"
  }
}

# Azure Virtual Network Implementation
resource "azurerm_virtual_network" "main" {
  count = var.cloud_provider == "azure" ? 1 : 0
  
  name                = "aivida-vnet-${var.environment}"
  address_space       = [var.cidr_block]
  location            = var.azure_location
  resource_group_name = var.azure_resource_group

  tags = {
    Environment = var.environment
    Compliance  = "HIPAA"
    ManagedBy   = "Terraform"
  }
}

resource "azurerm_subnet" "public" {
  count = var.cloud_provider == "azure" ? var.availability_zones : 0
  
  name                 = "aivida-public-subnet-${count.index + 1}"
  resource_group_name  = var.azure_resource_group
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = [cidrsubnet(var.cidr_block, 8, count.index + 1)]
}

resource "azurerm_subnet" "private" {
  count = var.cloud_provider == "azure" ? var.availability_zones : 0
  
  name                 = "aivida-private-subnet-${count.index + 1}"
  resource_group_name  = var.azure_resource_group
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = [cidrsubnet(var.cidr_block, 8, count.index + 11)]
}

# Google Cloud VPC Implementation
resource "google_compute_network" "main" {
  count = var.cloud_provider == "gcp" ? 1 : 0
  
  name                    = "aivida-vpc-${var.environment}"
  auto_create_subnetworks = false
  mtu                     = 1460
}

resource "google_compute_subnetwork" "public" {
  count = var.cloud_provider == "gcp" ? var.availability_zones : 0
  
  name          = "aivida-public-subnet-${count.index + 1}"
  ip_cidr_range = cidrsubnet(var.cidr_block, 8, count.index + 1)
  region        = var.gcp_region
  network       = google_compute_network.main[0].id
}

resource "google_compute_subnetwork" "private" {
  count = var.cloud_provider == "gcp" ? var.availability_zones : 0
  
  name          = "aivida-private-subnet-${count.index + 1}"
  ip_cidr_range = cidrsubnet(var.cidr_block, 8, count.index + 11)
  region        = var.gcp_region
  network       = google_compute_network.main[0].id
  
  private_ip_google_access = true
}

# Data sources
data "aws_availability_zones" "available" {
  count = var.cloud_provider == "aws" ? 1 : 0
  state = "available"
}

# Outputs
output "vpc_id" {
  description = "VPC/VNet ID"
  value = (
    var.cloud_provider == "aws" ? aws_vpc.main[0].id :
    var.cloud_provider == "azure" ? azurerm_virtual_network.main[0].id :
    var.cloud_provider == "gcp" ? google_compute_network.main[0].id :
    null
  )
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value = (
    var.cloud_provider == "aws" ? aws_subnet.public[*].id :
    var.cloud_provider == "azure" ? azurerm_subnet.public[*].id :
    var.cloud_provider == "gcp" ? google_compute_subnetwork.public[*].id :
    []
  )
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value = (
    var.cloud_provider == "aws" ? aws_subnet.private[*].id :
    var.cloud_provider == "azure" ? azurerm_subnet.private[*].id :
    var.cloud_provider == "gcp" ? google_compute_subnetwork.private[*].id :
    []
  )
}
```

### 2. Kubernetes Cluster with HIPAA Compliance

#### EKS Configuration
```yaml
# terraform/modules/kubernetes/eks.tf
resource "aws_eks_cluster" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name     = "aivida-eks-${var.environment}"
  role_arn = aws_iam_role.eks_cluster[0].arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.allowed_cidr_blocks
    
    # Security group for additional control
    security_group_ids = [aws_security_group.eks_cluster[0].id]
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks[0].arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
    aws_cloudwatch_log_group.eks
  ]

  tags = {
    Name        = "aivida-eks-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
  }
}

# KMS key for EKS encryption
resource "aws_kms_key" "eks" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "aivida-eks-encryption-${var.environment}"
  }
}

resource "aws_kms_alias" "eks" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name          = "alias/aivida-eks-${var.environment}"
  target_key_id = aws_kms_key.eks[0].key_id
}

# CloudWatch Log Group for EKS
resource "aws_cloudwatch_log_group" "eks" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name              = "/aws/eks/aivida-${var.environment}/cluster"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.cloudwatch[0].arn

  tags = {
    Name        = "aivida-eks-logs-${var.environment}"
    Environment = var.environment
  }
}

# EKS Node Group with security hardening
resource "aws_eks_node_group" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  cluster_name    = aws_eks_cluster.main[0].name
  node_group_name = "aivida-nodes-${var.environment}"
  node_role_arn   = aws_iam_role.eks_node_group[0].arn
  subnet_ids      = var.private_subnet_ids

  capacity_type  = "ON_DEMAND"
  instance_types = ["c5.large", "c5.xlarge"]
  ami_type       = "AL2_x86_64"
  disk_size      = 50

  scaling_config {
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
    min_size     = var.node_min_size
  }

  update_config {
    max_unavailable = 1
  }

  # Ensure pods cannot run on nodes not ready
  launch_template {
    id      = aws_launch_template.eks_nodes[0].id
    version = aws_launch_template.eks_nodes[0].latest_version
  }

  # Taints for HIPAA compliance
  taint {
    key    = "hipaa-compliant"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  tags = {
    Name        = "aivida-eks-nodes-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}

# Launch template for EKS nodes with security hardening
resource "aws_launch_template" "eks_nodes" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name_prefix   = "aivida-eks-nodes-${var.environment}"
  image_id      = data.aws_ssm_parameter.eks_ami_release_version[0].value
  instance_type = "c5.large"

  vpc_security_group_ids = [aws_security_group.eks_nodes[0].id]

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 50
      volume_type          = "gp3"
      encrypted            = true
      kms_key_id          = aws_kms_key.ebs[0].arn
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 2
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    cluster_name = aws_eks_cluster.main[0].name
    endpoint     = aws_eks_cluster.main[0].endpoint
    ca_data      = aws_eks_cluster.main[0].certificate_authority[0].data
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "aivida-eks-node-${var.environment}"
      Environment = var.environment
      Compliance  = "HIPAA"
    }
  }
}
```

### 3. Database with Encryption

#### RDS PostgreSQL with HIPAA Compliance
```yaml
# terraform/modules/database/rds.tf
resource "aws_db_subnet_group" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name       = "aivida-db-subnet-group-${var.environment}"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name = "aivida-db-subnet-group-${var.environment}"
  }
}

resource "aws_db_parameter_group" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  family = "postgres14"
  name   = "aivida-db-params-${var.environment}"

  # HIPAA compliance parameters
  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries taking more than 1 second
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "ssl"
    value = "1"
  }

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  tags = {
    Name = "aivida-db-params-${var.environment}"
  }
}

resource "aws_db_instance" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  identifier = "aivida-db-${var.environment}"

  # Database configuration
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds[0].arn

  # Database credentials
  db_name  = "aivida"
  username = var.db_username
  password = var.db_password

  # Network configuration
  vpc_security_group_ids = [aws_security_group.database[0].id]
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  publicly_accessible    = false

  # Backup configuration
  backup_retention_period = 35  # 5 weeks for HIPAA
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  copy_tags_to_snapshot  = true
  delete_automated_backups = false

  # Monitoring and logging
  monitoring_interval    = 60
  monitoring_role_arn   = aws_iam_role.rds_monitoring[0].arn
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.rds[0].arn
  performance_insights_retention_period = 7

  enabled_cloudwatch_logs_exports = [
    "postgresql"
  ]

  # Security configuration
  parameter_group_name = aws_db_parameter_group.main[0].name
  ca_cert_identifier   = "rds-ca-2019"

  # Deletion protection for production
  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment == "production" ? false : true
  final_snapshot_identifier = var.environment == "production" ? "aivida-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  tags = {
    Name        = "aivida-db-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    BackupWindow = "03:00-04:00"
  }
}

# Read replica for disaster recovery
resource "aws_db_instance" "replica" {
  count = var.cloud_provider == "aws" && var.environment == "production" ? 1 : 0
  
  identifier = "aivida-db-replica-${var.environment}"
  
  replicate_source_db = aws_db_instance.main[0].identifier
  instance_class      = var.db_instance_class
  
  # Network configuration
  vpc_security_group_ids = [aws_security_group.database[0].id]
  publicly_accessible    = false

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring[0].arn
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.rds[0].arn

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  tags = {
    Name        = "aivida-db-replica-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    Role        = "ReadReplica"
  }
}

# KMS key for RDS encryption
resource "aws_kms_key" "rds" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  description             = "RDS encryption key for Aivida"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow RDS Service"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "aivida-rds-kms-${var.environment}"
  }
}

resource "aws_kms_alias" "rds" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name          = "alias/aivida-rds-${var.environment}"
  target_key_id = aws_kms_key.rds[0].key_id
}
```

### 4. Object Storage with Encryption

#### S3 Bucket with HIPAA Compliance
```yaml
# terraform/modules/storage/s3.tf
resource "aws_s3_bucket" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = "aivida-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "aivida-storage-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    DataClass   = "PHI"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.main[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for data protection
resource "aws_s3_bucket_versioning" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.main[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.main[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3[0].arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle configuration for cost optimization and compliance
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.main[0].id

  rule {
    id     = "hipaa_lifecycle"
    status = "Enabled"

    expiration {
      days = 2555  # 7 years for HIPAA compliance
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }

    transition {
      days          = 1095  # 3 years
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# Bucket notification for audit logging
resource "aws_s3_bucket_notification" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.main[0].id

  cloudwatchconfiguration {
    cloudwatch_configuration {
      events = [
        "s3:ObjectCreated:*",
        "s3:ObjectRemoved:*"
      ]
    }
  }
}

# Access logging
resource "aws_s3_bucket_logging" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.main[0].id

  target_bucket = aws_s3_bucket.access_logs[0].id
  target_prefix = "access-logs/"
}

# Separate bucket for access logs
resource "aws_s3_bucket" "access_logs" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = "aivida-access-logs-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "aivida-access-logs-${var.environment}"
    Environment = var.environment
    Purpose     = "AccessLogs"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  bucket = aws_s3_bucket.access_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3[0].arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# KMS key for S3 encryption
resource "aws_kms_key" "s3" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  description             = "S3 encryption key for Aivida"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow S3 Service"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "aivida-s3-kms-${var.environment}"
  }
}

resource "aws_kms_alias" "s3" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name          = "alias/aivida-s3-${var.environment}"
  target_key_id = aws_kms_key.s3[0].key_id
}
```

### 5. Security Groups and Network ACLs

```yaml
# terraform/modules/security/security_groups.tf
# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name_prefix = "aivida-alb-${var.environment}"
  vpc_id      = var.vpc_id

  # HTTPS from internet
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Redirect HTTP to HTTPS
  ingress {
    description = "HTTP redirect to HTTPS"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aivida-alb-sg-${var.environment}"
  }
}

# EKS cluster Security Group
resource "aws_security_group" "eks_cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name_prefix = "aivida-eks-cluster-${var.environment}"
  vpc_id      = var.vpc_id

  # Allow nodes to communicate with cluster API
  ingress {
    description = "Node communication"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    security_groups = [aws_security_group.eks_nodes[0].id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aivida-eks-cluster-sg-${var.environment}"
  }
}

# EKS nodes Security Group
resource "aws_security_group" "eks_nodes" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name_prefix = "aivida-eks-nodes-${var.environment}"
  vpc_id      = var.vpc_id

  # Allow communication between nodes
  ingress {
    description = "Node to node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Allow communication from ALB
  ingress {
    description = "ALB to nodes"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }

  # Allow cluster to communicate with nodes
  ingress {
    description = "Cluster API to nodes"
    from_port   = 1025
    to_port     = 65535
    protocol    = "tcp"
    security_groups = [aws_security_group.eks_cluster[0].id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aivida-eks-nodes-sg-${var.environment}"
  }
}

# Database Security Group
resource "aws_security_group" "database" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name_prefix = "aivida-database-${var.environment}"
  vpc_id      = var.vpc_id

  # PostgreSQL from application nodes only
  ingress {
    description = "PostgreSQL from EKS nodes"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.eks_nodes[0].id]
  }

  # No outbound rules needed for RDS
  tags = {
    Name = "aivida-database-sg-${var.environment}"
  }
}
```

### 6. Monitoring and Logging

```yaml
# terraform/modules/monitoring/cloudwatch.tf
# CloudWatch Log Groups for application logs
resource "aws_cloudwatch_log_group" "application" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name              = "/aws/aivida/${var.environment}/application"
  retention_in_days = 2555  # 7 years for HIPAA
  kms_key_id        = aws_kms_key.cloudwatch[0].arn

  tags = {
    Name        = "aivida-app-logs-${var.environment}"
    Environment = var.environment
    Purpose     = "ApplicationLogs"
  }
}

resource "aws_cloudwatch_log_group" "audit" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name              = "/aws/aivida/${var.environment}/audit"
  retention_in_days = 2555  # 7 years for HIPAA
  kms_key_id        = aws_kms_key.cloudwatch[0].arn

  tags = {
    Name        = "aivida-audit-logs-${var.environment}"
    Environment = var.environment
    Purpose     = "AuditLogs"
    Compliance  = "HIPAA"
  }
}

# CloudWatch Dashboard for monitoring
resource "aws_cloudwatch_dashboard" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  dashboard_name = "Aivida-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main[0].arn_suffix],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main[0].arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", aws_lb.main[0].arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.main[0].arn_suffix]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.main[0].id],
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.main[0].id],
            ["AWS/RDS", "FreeableMemory", "DBInstanceIdentifier", aws_db_instance.main[0].id]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "RDS Database Metrics"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms for critical metrics
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  alarm_name          = "aivida-high-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors 5xx errors from the load balancer"
  alarm_actions       = [aws_sns_topic.alerts[0].arn]

  dimensions = {
    LoadBalancer = aws_lb.main[0].arn_suffix
  }

  tags = {
    Name        = "aivida-high-error-rate-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  alarm_name          = "aivida-database-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors database CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts[0].arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main[0].id
  }

  tags = {
    Name        = "aivida-database-cpu-${var.environment}"
    Environment = var.environment
  }
}

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  name              = "aivida-alerts-${var.environment}"
  kms_master_key_id = aws_kms_key.sns[0].arn

  tags = {
    Name        = "aivida-alerts-${var.environment}"
    Environment = var.environment
  }
}

# KMS key for CloudWatch Logs encryption
resource "aws_kms_key" "cloudwatch" {
  count = var.cloud_provider == "aws" ? 1 : 0
  
  description             = "CloudWatch Logs encryption key for Aivida"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "aivida-cloudwatch-kms-${var.environment}"
  }
}
```

This cloud-agnostic infrastructure template provides a comprehensive foundation for deploying the Aivida Discharge Copilot platform with HIPAA compliance across AWS, Azure, and Google Cloud Platform. The templates include encryption at rest and in transit, comprehensive monitoring, security groups, and audit logging capabilities.
