resource "aws_s3_bucket" "labels" {
  bucket = "courier-api-labels"
}

resource "aws_security_group" "api" {
  name = "courier-api"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
