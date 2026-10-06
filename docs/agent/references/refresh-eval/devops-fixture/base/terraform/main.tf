terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "shipments-api/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "eu-west-1"
  default_tags {
    tags = { service = "shipments-api" }
  }
}

variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_security_group" "db" {
  name   = "shipments-db"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

variable "vpc_id" {
  type = string
}

resource "aws_db_instance" "orders" {
  identifier             = "shipments-orders"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.medium"
  allocated_storage      = 50
  username               = "shipments"
  password               = var.db_password
  publicly_accessible    = true
  skip_final_snapshot    = true
  deletion_protection    = false
  backup_retention_period = 0
  vpc_security_group_ids = [aws_security_group.db.id]
}
