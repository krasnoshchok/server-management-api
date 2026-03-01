output "api_service_nodeport" {
  description = "NodePort exposed by the server-api service."
  value       = kubernetes_service.api.spec[0].port[0].node_port
}
