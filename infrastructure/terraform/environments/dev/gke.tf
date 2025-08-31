# GKE Cluster Configuration for HIPAA Compliance

# HIPAA-compliant GKE cluster
resource "google_container_cluster" "aivida_gke" {
  name     = "aivida-gke-${var.environment}"
  location = var.region
  
  # Use VPC-native networking
  network    = google_compute_network.aivida_vpc.self_link
  subnetwork = google_compute_subnetwork.gke_subnet.self_link

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # HIPAA compliance settings
  enable_shielded_nodes = true
  
  # Network policy for security
  network_policy {
    enabled = true
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
    
    master_global_access_config {
      enabled = true
    }
  }

  # IP allocation policy for VPC-native networking
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Master authentication
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # Workload Identity for secure pod-to-GCP service authentication
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Binary authorization for container image security
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Database encryption
  database_encryption {
    state    = "ENCRYPTED"
    key_name = google_kms_crypto_key.gke_key.id
  }

  # Logging and monitoring
  logging_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "API_SERVER"
    ]
  }

  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "API_SERVER",
      "SCHEDULER",
      "CONTROLLER_MANAGER"
    ]
  }

  # Maintenance window
  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T02:00:00Z"
      end_time   = "2023-01-01T06:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SU"
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_kms_crypto_key.gke_key
  ]
}

# Node pool with security configurations
resource "google_container_node_pool" "aivida_nodes" {
  name       = "aivida-nodes-${var.environment}"
  location   = var.region
  cluster    = google_container_cluster.aivida_gke.name
  node_count = 3

  # Node configuration
  node_config {
    preemptible  = false
    machine_type = "e2-standard-4"
    disk_size_gb = 100
    disk_type    = "pd-ssd"
    image_type   = "COS_CONTAINERD"

    # Security configurations
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/trace.append"
    ]

    # Labels and tags
    labels = {
      environment = var.environment
      project     = "aivida"
      compliance  = "hipaa"
    }

    tags = ["aivida-nodes"]

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  # Auto-scaling
  autoscaling {
    min_node_count = 3
    max_node_count = 10
  }

  # Node management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# KMS key for encryption
resource "google_kms_key_ring" "aivida_keyring" {
  name     = "aivida-keyring-${var.environment}"
  location = "global"
}

resource "google_kms_crypto_key" "gke_key" {
  name     = "aivida-gke-key-${var.environment}"
  key_ring = google_kms_key_ring.aivida_keyring.id
  purpose  = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
}

# Outputs
output "gke_cluster_name" {
  description = "The name of the GKE cluster"
  value       = google_container_cluster.aivida_gke.name
}

output "gke_cluster_endpoint" {
  description = "The endpoint of the GKE cluster"
  value       = google_container_cluster.aivida_gke.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "The CA certificate of the GKE cluster"
  value       = google_container_cluster.aivida_gke.master_auth[0].cluster_ca_certificate
  sensitive   = true
}
