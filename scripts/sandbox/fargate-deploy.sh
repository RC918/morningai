#!/bin/bash

set -e

CLUSTER_NAME="morningai-sandbox-cluster"
SERVICE_NAME="ops-agent-sandbox"
TASK_FAMILY="ops-agent-sandbox-task"
REGION="${AWS_REGION:-us-west-2}"
ECR_REPO="morningai/sandbox-ops-agent"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install: https://aws.amazon.com/cli/"
        exit 1
    fi
    log_info "AWS CLI version: $(aws --version)"
}

check_auth() {
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "Not authenticated. Please run: aws configure"
        exit 1
    fi
    log_info "Authenticated as: $(aws sts get-caller-identity --query 'Arn' --output text)"
}

create_ecr_repo() {
    log_info "Creating ECR repository..."
    
    if aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$REGION" &> /dev/null; then
        log_info "ECR repository already exists"
    else
        aws ecr create-repository \
            --repository-name "$ECR_REPO" \
            --region "$REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        log_info "ECR repository created"
    fi
}

build_and_push_image() {
    log_info "Building and pushing Docker image to ECR..."
    
    aws ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin \
        "$(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.$REGION.amazonaws.com"
    
    docker build \
        -t "$ECR_REPO:latest" \
        -f handoff/20250928/40_App/orchestrator/sandbox/ops_agent/Dockerfile \
        handoff/20250928/40_App/orchestrator/sandbox/ops_agent/
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    ECR_URL="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:latest"
    
    docker tag "$ECR_REPO:latest" "$ECR_URL"
    docker push "$ECR_URL"
    
    log_info "Image pushed to: $ECR_URL"
    echo "$ECR_URL"
}

create_cluster() {
    log_info "Creating ECS cluster..."
    
    if aws ecs describe-clusters --clusters "$CLUSTER_NAME" --region "$REGION" | \
       grep -q "ACTIVE"; then
        log_info "Cluster already exists"
    else
        aws ecs create-cluster \
            --cluster-name "$CLUSTER_NAME" \
            --region "$REGION" \
            --capacity-providers FARGATE FARGATE_SPOT \
            --default-capacity-provider-strategy \
                capacityProvider=FARGATE,weight=1,base=1
        log_info "Cluster created"
    fi
}

create_task_definition() {
    log_info "Registering task definition..."
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    IMAGE_URL="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:latest"
    
    cat > /tmp/task-definition.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ops-agent-sandbox",
      "image": "$IMAGE_URL",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$TASK_FAMILY",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {"name": "AGENT_TYPE", "value": "ops_agent"},
        {"name": "MCP_SERVER_URL", "value": "http://localhost:8080"}
      ],
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "ulimits": [
        {
          "name": "nofile",
          "softLimit": 65536,
          "hardLimit": 65536
        }
      ],
      "linuxParameters": {
        "capabilities": {
          "drop": ["ALL"],
          "add": ["NET_BIND_SERVICE"]
        }
      }
    }
  ]
}
EOF
    
    aws ecs register-task-definition \
        --cli-input-json file:///tmp/task-definition.json \
        --region "$REGION" > /dev/null
    
    log_info "Task definition registered"
}

create_log_group() {
    log_info "Creating CloudWatch log group..."
    
    if aws logs describe-log-groups --log-group-name-prefix "/ecs/$TASK_FAMILY" --region "$REGION" | \
       grep -q "$TASK_FAMILY"; then
        log_info "Log group already exists"
    else
        aws logs create-log-group \
            --log-group-name "/ecs/$TASK_FAMILY" \
            --region "$REGION"
        
        aws logs put-retention-policy \
            --log-group-name "/ecs/$TASK_FAMILY" \
            --retention-in-days 7 \
            --region "$REGION"
        
        log_info "Log group created"
    fi
}

start_service() {
    log_info "Starting ECS service..."
    
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region "$REGION")
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region "$REGION")
    SUBNET_ID=$(echo "$SUBNET_IDS" | awk '{print $1}')
    
    if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$REGION" | \
       grep -q "ACTIVE"; then
        log_info "Service already running. Updating..."
        aws ecs update-service \
            --cluster "$CLUSTER_NAME" \
            --service "$SERVICE_NAME" \
            --desired-count 1 \
            --region "$REGION" > /dev/null
    else
        log_info "Creating new service..."
        aws ecs create-service \
            --cluster "$CLUSTER_NAME" \
            --service-name "$SERVICE_NAME" \
            --task-definition "$TASK_FAMILY" \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],assignPublicIp=ENABLED}" \
            --region "$REGION" > /dev/null
    fi
    
    log_info "✅ Service started successfully!"
}

stop_service() {
    log_info "Stopping ECS service..."
    
    if ! aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$REGION" | \
         grep -q "ACTIVE"; then
        log_warn "Service not found or already stopped"
        return
    fi
    
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --desired-count 0 \
        --region "$REGION" > /dev/null
    
    log_info "✅ Service stopped (scaled to 0)"
}

show_status() {
    log_info "📊 Service Status"
    echo ""
    
    aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$REGION" \
        --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" \
        --output table
    
    echo ""
    log_info "💰 Estimated Cost"
    RUNNING=$(aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$REGION" --query "services[0].runningCount" --output text)
    if [ "$RUNNING" -gt 0 ]; then
        echo "Running: $RUNNING task(s) × $9.01/month = ~\$$(echo "$RUNNING * 9.01" | bc)/month"
    else
        echo "Running: 0 tasks (cost: $0/month)"
    fi
}

show_logs() {
    log_info "📜 Recent Logs (last 20 lines)"
    
    aws logs tail "/ecs/$TASK_FAMILY" \
        --follow \
        --format short \
        --region "$REGION"
}

start_sandbox() {
    log_info "🚀 Deploying Ops_Agent Sandbox on AWS Fargate..."
    
    create_ecr_repo
    build_and_push_image
    create_cluster
    create_log_group
    create_task_definition
    start_service
    
    log_info "✅ Deployment complete!"
    log_info ""
    log_info "Next steps:"
    log_info "  - View logs: ./scripts/sandbox/fargate-deploy.sh logs"
    log_info "  - Check status: ./scripts/sandbox/fargate-deploy.sh status"
    log_info "  - Stop service: ./scripts/sandbox/fargate-deploy.sh stop"
}

case "${1:-}" in
    start)
        check_aws_cli
        check_auth
        start_sandbox
        ;;
    stop)
        check_aws_cli
        check_auth
        stop_service
        ;;
    status)
        check_aws_cli
        check_auth
        show_status
        ;;
    logs)
        check_aws_cli
        check_auth
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start  - Deploy/update sandbox (cost: ~$9/month)"
        echo "  stop   - Scale to 0 tasks (cost: $0/month)"
        echo "  status - Show service status and costs"
        echo "  logs   - Tail CloudWatch logs"
        exit 1
        ;;
esac
