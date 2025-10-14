provider "aws" {
  region = "ap-northeast-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# サブネット
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = false
}

# -----------------------------------------------------------------------------
# Amazon S3 Gateway Endpoint
# -----------------------------------------------------------------------------
resource "aws_vpc_endpoint" "s3_gateway" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.ap-northeast-1.s3" # リージョンを指定
  vpc_endpoint_type = "Gateway"

  # オプション: エンドポイントポリシー (デフォルトではフルアクセス)
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:*"
        Resource  = "*"
      },
    ]
  })

  tags = {
    Name = "s3-gateway-endpoint"
  }
}

# -----------------------------------------------------------------------------
# ルートテーブルとの関連付け
# -----------------------------------------------------------------------------
resource "aws_vpc_endpoint_route_table_association" "s3_private_assoc" {
  vpc_endpoint_id = aws_vpc_endpoint.s3_gateway.id
  # S3エンドポイントをプライベートサブネットのルートテーブルに関連付け
  route_table_id  = "rtb-0d6fb23ff667c4579"
}

# Security Group
resource "aws_security_group" "ec2_sg" {
  name        = "ec2-sg"
  description = "Allow Lambda access"
  vpc_id      = aws_vpc.main.id

  # インバウンドルール: EICEのセキュリティグループからのSSH（ポート22）を許可
  ingress {
    description     = "Allow SSH from EICE"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.eice_sg.id] # EICEのSGをソースに指定
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Private-EC2-Instance-SG"
  }
}

# EICEに適用するセキュリティグループ
resource "aws_security_group" "eice_sg" {
  name        = "eice-endpoint-sg"
  description = "Security group for EC2 Instance Connect Endpoint"
  vpc_id      = aws_vpc.main.id # 既存のVPC IDを指定

  ingress {
    description = "Allow SSH from client IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # アウトバウンドルール: デフォルトではすべて許可（必要に応じて制限）
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "eice-endpoint-sg"
  }
}

# EC2 Instance Connect Endpoint
resource "aws_ec2_instance_connect_endpoint" "example" {
  # 必須: エンドポイントを配置するプライベートサブネットのID
  subnet_id          = aws_subnet.private.id

  # オプション: 適用するセキュリティグループ
  security_group_ids = [aws_security_group.eice_sg.id]

  # オプション: クライアントのIPアドレスをソースとして維持するかどうか (デフォルト: true)
  # falseに設定すると、接続はVPCのCIDRブロックから来るように見えます。
  preserve_client_ip = true 

  tags = {
    Name = "Private-EC2-Connect-Endpoint"
  }
}

# 出力: 作成されたエンドポイントのID
output "ec2_instance_connect_endpoint_id" {
  description = "The ID of the EC2 Instance Connect Endpoint"
  value       = aws_ec2_instance_connect_endpoint.example.id
}

# EC2 インスタンス
resource "aws_instance" "ec2" {
  ami           = "ami-0f6c4e13703daa864" # 適切なLinux AMI
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.private.id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = false
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  tags = {
    Name = "InferenceServer"
  }
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "EC2-SSM-S3-InstanceProfile"
  role = "EC2-SSM-S3-Role"  # 既存ロール名
}

# 下記memo
# EC2サービス用 VPCエンドポイント (Interface Endpoint)
resource "aws_vpc_endpoint" "ec2_api" {
  vpc_id              = aws_vpc.main.id
  # サービス名はリージョン固有のため、providerのregionを参照
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ec2" 
  vpc_endpoint_type   = "Interface"

  # LambdaやEC2が配置されているプライベートサブネットを指定
  subnet_ids          = [aws_subnet.private.id]

  # EndpointにアタッチするSecurity Group (LambdaからのTCP/443を許可するSGが必要です)
  # ※ここでは既存のEC2 SGを流用しますが、専用SGの作成を推奨
  security_group_ids  = [aws_security_group.ec2_sg.id] 
  
  private_dns_enabled = true
  
  # VPCエンドポイントのタグ
  tags = {
    Name = "ec2-api-interface-endpoint"
  }
}

aws_instance.cpu_ec2_web.public_ip

TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PRIVATE_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4)
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)
echo "PUBLIC_IP:$PUBLIC_IP,PRIVATE_IP:$PRIVATE_IP" >> /opt/prefect/log/common.log