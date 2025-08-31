# Environment-specific Terraform variables for Development

# GCP Project Configuration
project_id = "aivida-dev-project"
region     = "us-central1"
environment = "dev"

# Network Configuration
vpc_cidr = "10.0.0.0/16"
gke_subnet_cidr = "10.0.0.0/16"
pods_cidr = "10.1.0.0/16"
services_cidr = "10.2.0.0/16"

# GKE Configuration
gke_node_count = 3
gke_machine_type = "e2-standard-4"
gke_disk_size = 100
gke_min_nodes = 3
gke_max_nodes = 10

# Database Configuration
db_tier = "db-standard-2"
db_disk_size = 100
db_backup_retention_days = 30
db_maintenance_window = {
  day  = 7
  hour = 2
}

# Security Configuration
enable_binary_authorization = true
enable_network_policy = true
enable_private_nodes = true
enable_shielded_nodes = true

# Monitoring Configuration
enable_logging = true
enable_monitoring = true
log_retention_days = 30

# Labels
labels = {
  environment = "dev"
  project     = "aivida"
  compliance  = "hipaa"
  team        = "engineering"
  cost_center = "development"
}
