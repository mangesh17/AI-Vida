# GCP HIPAA-Eligible Infrastructure Setup

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.84"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.84"
    }
  }
}

# Project configuration
variable "project_id" {
  description = "GCP Project ID for AI-Vida"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs for HIPAA compliance
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudasset.googleapis.com",
    "dlp.googleapis.com",
    "healthcare.googleapis.com",
    "artifactregistry.googleapis.com",
    "servicenetworking.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
}

# VPC Network with private subnets
resource "google_compute_network" "aivida_vpc" {
  name                    = "aivida-vpc-${var.environment}"
  auto_create_subnetworks = false
  mtu                     = 1460

  depends_on = [google_project_service.required_apis]
}

# Private subnet for GKE cluster
resource "google_compute_subnetwork" "gke_subnet" {
  name          = "aivida-gke-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network       = google_compute_network.aivida_vpc.id

  # Enable private Google access for HIPAA compliance
  private_ip_google_access = true

  # Secondary IP ranges for GKE pods and services
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# Cloud NAT for outbound internet access
resource "google_compute_router" "aivida_router" {
  name    = "aivida-router-${var.environment}"
  region  = var.region
  network = google_compute_network.aivida_vpc.id
}

resource "google_compute_router_nat" "aivida_nat" {
  name   = "aivida-nat-${var.environment}"
  router = google_compute_router.aivida_router.name
  region = var.region

  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rules for secure access
resource "google_compute_firewall" "allow_internal" {
  name    = "aivida-allow-internal-${var.environment}"
  network = google_compute_network.aivida_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/16", "10.1.0.0/16", "10.2.0.0/16"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "aivida-allow-ssh-${var.environment}"
  network = google_compute_network.aivida_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # Restrict SSH access to specific IP ranges
  source_ranges = ["35.235.240.0/20"] # Google Cloud Shell
  target_tags   = ["ssh-access"]
}

# Outputs
output "vpc_network_id" {
  description = "The ID of the VPC network"
  value       = google_compute_network.aivida_vpc.id
}

output "gke_subnet_id" {
  description = "The ID of the GKE subnet"
  value       = google_compute_subnetwork.gke_subnet.id
}
