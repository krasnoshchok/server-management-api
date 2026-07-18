variable "kubeconfig_path" {
  description = "Path to the kubeconfig file for the cluster."
  type        = string
  default     = "~/.kube/config"
}

variable "docker_host" {
  description = "Docker daemon URI (used by the docker provider)."
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "image_name" {
  description = "Name of the Docker image to build/push."
  type        = string
  default     = "server-management-api"
}

variable "image_tag" {
  description = "Tag to use for the Docker image."
  type        = string
  default     = "latest"
}

variable "db_name" {
  description = "Database name used by the API and Postgres container."
  type        = string
  default     = "server_management"
}

variable "db_user" {
  description = "Database user used by the API and Postgres container."
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database password used by the API and Postgres container."
  type        = string
  sensitive   = true
}

