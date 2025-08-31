# Cloud SQL PostgreSQL with HIPAA compliance

# Private service access for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "aivida-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.aivida_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.aivida_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Database encryption key
resource "google_kms_crypto_key" "database_key" {
  name     = "aivida-database-key-${var.environment}"
  key_ring = google_kms_key_ring.aivida_keyring.id
  purpose  = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
}

# Cloud SQL instance with HIPAA compliance
resource "google_sql_database_instance" "aivida_db" {
  name             = "aivida-db-${var.environment}"
  database_version = "POSTGRES_14"
  region           = var.region
  
  deletion_protection = true

  settings {
    tier              = "db-standard-2"
    availability_type = "REGIONAL"  # High availability for production
    disk_type         = "PD_SSD"
    disk_size         = 100
    disk_autoresize   = true

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }

    # IP configuration for private access
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.aivida_vpc.id
      enable_private_path_for_google_cloud_services = true
      require_ssl                                   = true

      authorized_networks {
        name  = "allow-gke"
        value = "10.0.0.0/16"
      }
    }

    # Database flags for security and compliance
    database_flags {
      name  = "log_statement"
      value = "all"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking more than 1 second
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    database_flags {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    }

    # Maintenance window
    maintenance_window {
      day          = 7  # Sunday
      hour         = 2  # 2 AM
      update_track = "stable"
    }

    # Insights configuration
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }

    # User labels
    user_labels = {
      environment = var.environment
      project     = "aivida"
      compliance  = "hipaa"
    }
  }

  # Encryption at rest
  encryption_key_name = google_kms_crypto_key.database_key.id

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_kms_crypto_key.database_key
  ]
}

# Database users
resource "google_sql_user" "aivida_app_user" {
  name     = "aivida_app"
  instance = google_sql_database_instance.aivida_db.name
  password = random_password.app_user_password.result
}

resource "random_password" "app_user_password" {
  length  = 32
  special = true
}

# Application databases
resource "google_sql_database" "aivida_main" {
  name     = "aivida_main"
  instance = google_sql_database_instance.aivida_db.name
}

resource "google_sql_database" "aivida_audit" {
  name     = "aivida_audit"
  instance = google_sql_database_instance.aivida_db.name
}

# Store database credentials in Secret Manager
resource "google_secret_manager_secret" "db_connection" {
  secret_id = "aivida-db-connection-${var.environment}"

  replication {
    automatic = true
  }

  labels = {
    environment = var.environment
    component   = "database"
  }
}

resource "google_secret_manager_secret_version" "db_connection" {
  secret = google_secret_manager_secret.db_connection.id
  secret_data = jsonencode({
    host     = google_sql_database_instance.aivida_db.private_ip_address
    port     = 5432
    database = google_sql_database.aivida_main.name
    username = google_sql_user.aivida_app_user.name
    password = google_sql_user.aivida_app_user.password
    ssl_mode = "require"
  })
}

# Outputs
output "database_connection_name" {
  description = "The connection name of the database instance"
  value       = google_sql_database_instance.aivida_db.connection_name
}

output "database_private_ip" {
  description = "The private IP address of the database instance"
  value       = google_sql_database_instance.aivida_db.private_ip_address
  sensitive   = true
}

output "database_secret_id" {
  description = "The Secret Manager secret ID for database connection"
  value       = google_secret_manager_secret.db_connection.secret_id
}
