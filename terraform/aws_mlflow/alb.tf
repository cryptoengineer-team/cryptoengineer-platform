# alb.tf | Load Balancer Configuration

resource "aws_alb" "application_load_balancer" {
  name               = "${var.tracker_name}-${var.app_environment}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = aws_subnet.public.*.id
  security_groups    = [aws_security_group.load_balancer_security_group.id]

  tags = {
    Name        = "${var.tracker_name}-alb"
    Environment = var.app_environment
  }
}

data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}

resource "aws_security_group" "load_balancer_security_group" {
  vpc_id = aws_vpc.aws-vpc.id

ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32", "${var.MYLOCALIP}"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  tags = {
    Name        = "${var.tracker_name}-sg"
    Environment = var.app_environment
  }
}

resource "aws_lb_target_group" "target_group" {
  name        = "${var.tracker_name}-${var.app_environment}-tg"
  port        = 5000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.aws-vpc.id

  tags = {
    Name        = "${var.tracker_name}-lb-tg"
    Environment = var.app_environment
  }
}

resource "aws_lb_listener" "listener" {
  load_balancer_arn = aws_alb.application_load_balancer.id
  port              = "5000"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.target_group.id
  }
}

output "load_balancer_dns_name" {
  value = "http://${aws_alb.application_load_balancer.dns_name}"
}
