provider "aws" {
  region = "ap-northeast-1"
}

########################################
# VPC
########################################
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "example-vpc"
  }
}

########################################
# Subnets (ap-northeast-1a, c, d)
########################################
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "ap-northeast-1a"

  tags = {
    Name = "public-a"
  }
}

resource "aws_subnet" "public_c" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "ap-northeast-1c"

  tags = {
    Name = "public-c"
  }
}

resource "aws_subnet" "public_d" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "ap-northeast-1d"

  tags = {
    Name = "public-d"
  }
}

########################################
# Internet Gateway
########################################
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "example-igw"
  }
}

########################################
# Route Table
########################################
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public-rt"
  }
}

########################################
# Route Table Association
########################################
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_c" {
  subnet_id      = aws_subnet.public_c.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_d" {
  subnet_id      = aws_subnet.public_d.id
  route_table_id = aws_route_table.public.id
}

########################################
# Security Group
########################################
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Allow HTTP and SSH"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web-sg"
  }
}

########################################
# Launch Template
########################################
resource "aws_launch_template" "example" {
  name = "example-lt"

  image_id      = "ami-0c3fd0f5d33134a76" # Amazon Linux 2 (例)
  instance_type = "t2.micro"

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.web.id]
  }

  user_data = base64encode("#!/bin/bash\nyum install -y httpd\nsystemctl enable httpd\nsystemctl start httpd")

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "example-ec2"
    }
  }
}

########################################
# Auto Scaling Group
########################################
resource "aws_autoscaling_group" "example" {
  name               = "example-asg"
  max_size           = 3
  min_size           = 1
  desired_capacity   = 1

  # 複数サブネット → AWS が空いている AZ で自動起動
  vpc_zone_identifier = [
    aws_subnet.public_a.id,
    aws_subnet.public_c.id,
    aws_subnet.public_d.id,
  ]

  launch_template {
    id      = aws_launch_template.example.id
    version = "$Latest"
  }

  health_check_type = "EC2"

  tag {
    key                 = "Name"
    value               = "example-asg-instance"
    propagate_at_launch = true
  }
}
