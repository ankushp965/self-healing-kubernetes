terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Cheapest VPC - Public Subnets only
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ai-agent-vpc"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  
  # Disable NAT gateway to save $32/mo
  enable_nat_gateway = false
  enable_vpn_gateway = false

  tags = {
    "kubernetes.io/cluster/ai-agent-cluster" = "shared"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "ai-agent-cluster"
  cluster_version = "1.30"

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.public_subnets
  control_plane_subnet_ids = module.vpc.public_subnets

  eks_managed_node_groups = {
    ai_agent_nodes = {
      instance_types = ["t3.medium"]
      
      min_size     = 1
      max_size     = 2
      desired_size = 1

      # Nodes in public subnet
      subnet_ids = module.vpc.public_subnets
    }
  }

  enable_cluster_creator_admin_permissions = true
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region ap-south-1 --name ai-agent-cluster"
}