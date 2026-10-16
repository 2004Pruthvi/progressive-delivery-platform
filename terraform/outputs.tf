output "vpc_id" {
  description = "ID of the provisioned VPC"
  value       = aws_vpc.main.id
}

output "eks_cluster_name" {
  description = "Name of the provisioned EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "Kubernetes API endpoint for the EKS cluster"
  value       = aws_eks_cluster.main.endpoint
}

output "ecr_repository_url" {
  description = "URL of the Amazon ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "oidc_provider_arn" {
  description = "IAM OIDC provider ARN for IRSA service accounts"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "configure_kubectl_command" {
  description = "AWS CLI command to update local kubeconfig"
  value       = "aws eks --region ${var.aws_region} update-kubeconfig --name ${aws_eks_cluster.main.name}"
}
