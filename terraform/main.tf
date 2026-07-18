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
    docker = {
      source  = "kreuzwerker/docker"
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
        container {
          name              = "server-api"
          image             = "${var.image_name}:${var.image_tag}"
          image_pull_policy = "IfNotPresent"  # use local image in cluster

          port {
            container_port = 8000
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
        container {
          name  = "postgres"
          image = "postgres:14"

          port {
            container_port = 5432
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
          empty_dir {}
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
