// Terraform configuration to manage Kubernetes resources for the Server Management API.
// The cluster itself is assumed to already exist (e.g. minikube, EKS, GKE, etc.).
// This file uses the official Kubernetes provider to create a Deployment and Service
// equivalent to the manifests kept in k8s/.  Running `terraform apply` will create or
// update the resources declaratively, making the setup portable across machines.

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

// NOTE: building the Docker image through Terraform has caused
// compatibility issues with varying Docker API versions.  Instead of
// managing the image with Terraform, build it manually (see README) and
// ensure the desired tag exists in the cluster before applying the k8s
// resources.

// If you prefer to push to a registry, simply remove this comment block
// and adjust the `image` field below accordingly.

resource "kubernetes_secret" "db_credentials" {
  metadata {
    name = "server-management-db"
  }

  data = {
    DB_NAME           = var.db_name
    DB_USER           = var.db_user
    DB_PASSWORD       = var.db_password
    POSTGRES_DB       = var.db_name
    POSTGRES_USER     = var.db_user
    POSTGRES_PASSWORD = var.db_password
  }

  type = "Opaque"
}

resource "kubernetes_persistent_volume_claim" "postgres_data" {
  metadata {
    name = "postgres-data"
  }

  spec {
    access_modes = ["ReadWriteOnce"]

    resources {
      requests = {
        storage = var.postgres_storage_size
      }
    }
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name = "server-api"
    labels = {
      app = "server-api"
    }
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "server-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "server-api"
        }
      }

      spec {
        automount_service_account_token = false

        security_context {
          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        container {
          name              = "server-api"
          image             = "${var.image_name}:${var.image_tag}"
          image_pull_policy = "IfNotPresent"  # use local image in cluster

          port {
            container_port = 8000
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          security_context {
            allow_privilege_escalation = false

            capabilities {
              drop = ["ALL"]
            }
          }

          startup_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            period_seconds    = 5
            failure_threshold = 12
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 5
            period_seconds        = 10
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 15
            period_seconds        = 20
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          env {
            name  = "DB_HOST"
            value = "postgres"
          }
          env {
            name  = "DB_NAME"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_credentials.metadata[0].name
                key  = "DB_NAME"
              }
            }
          }
          env {
            name  = "DB_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_credentials.metadata[0].name
                key  = "DB_USER"
              }
            }
          }
          env {
            name  = "DB_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_credentials.metadata[0].name
                key  = "DB_PASSWORD"
              }
            }
          }
          env {
            name  = "DB_PORT"
            value = "5432"
          }
          env {
            name  = "LOG_LEVEL"
            value = "INFO"
          }
          env {
            name  = "LOG_FILE"
            value = "/logs/app.log"
          }

          volume_mount {
            name       = "log-volume"
            mount_path = "/logs"
          }
        }

        volume {
          name = "log-volume"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "api" {
  metadata {
    name = "server-api"
  }

  spec {
    selector = {
      app = kubernetes_deployment.api.metadata[0].labels.app
    }

    port {
      port        = 8000
      target_port = 8000
      node_port   = 30080
    }

    type = "NodePort"
  }
}

resource "kubernetes_deployment" "postgres" {
  metadata {
    name = "postgres"
    labels = {
      app = "postgres"
    }
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }

      spec {
        security_context {
          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        container {
          name  = "postgres"
          image = "postgres:14"

          port {
            container_port = 5432
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }

          security_context {
            allow_privilege_escalation = false

            capabilities {
              drop = ["ALL"]
            }
          }

          startup_probe {
            exec {
              command = ["sh", "-c", "pg_isready -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\""]
            }
            period_seconds    = 5
            failure_threshold = 12
          }

          readiness_probe {
            exec {
              command = ["sh", "-c", "pg_isready -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\""]
            }
            initial_delay_seconds = 5
            period_seconds        = 10
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          liveness_probe {
            exec {
              command = ["sh", "-c", "pg_isready -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\""]
            }
            initial_delay_seconds = 20
            period_seconds        = 20
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          env {
            name  = "POSTGRES_DB"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_credentials.metadata[0].name
                key  = "POSTGRES_DB"
              }
            }
          }
          env {
            name  = "POSTGRES_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_credentials.metadata[0].name
                key  = "POSTGRES_USER"
              }
            }
          }
          env {
            name  = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_credentials.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }

          volume_mount {
            name       = "pgdata"
            mount_path = "/var/lib/postgresql/data"
          }
        }

        volume {
          name = "pgdata"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.postgres_data.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  metadata {
    name = "postgres"
  }

  spec {
    type = "ClusterIP"
    selector = {
      app = "postgres"
    }

    port {
      port        = 5432
      target_port = 5432
    }
  }
}
