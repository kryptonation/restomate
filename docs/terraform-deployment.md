# Food fleet AWS Infrastructure - Terraform Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Initial Setup](#initial-setup)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Process](#deployment-process)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [CI/CD Integration](#cicd-integration)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Cost Management](#cost-management)

---

## Prerequisites

### Required Tools

1. **Terraform** (>= 1.6.0)
   ```bash
   # Install Terraform
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   terraform version
   ```

2. **AWS CLI** (>= 2.0)
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   aws --version
   ```

3. **Docker** (>= 20.10)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

4. **Make** (optional, for using Makefile)
   ```bash
   sudo apt install make  # Ubuntu/Debian
   ```

### AWS Account Requirements

1. **AWS Account** with appropriate permissions
2. **IAM User** with following permissions:
   - EC2 (VPC, subnets, security groups)
   - ECS (clusters, services, tasks)
   - RDS (database instances)
   - ElastiCache (Redis clusters)
   - S3 (buckets, objects)
   - ECR (repositories)
   - IAM (roles, policies)
   - Secrets Manager
   - CloudWatch (logs, alarms)
   - Application Load Balancer

3. **AWS Access Keys** configured:
   ```bash
   aws configure
   # AWS Access Key ID: YOUR_ACCESS_KEY
   # AWS Secret Access Key: YOUR_SECRET_KEY
   # Default region: us-east-1
   # Default output format: json
   ```

---

## Project Structure

```
terraform/
├── main.tf                          # Main configuration
├── variables.tf                     # Input variables
├── outputs.tf                       # Output values
│
├── modules/
│   ├── networking/
│   │   └── main.tf                  # VPC, subnets, security groups
│   ├── compute/
│   │   ├── ecs.tf                   # ECS cluster and services
│   │   └── alb.tf                   # Application Load Balancer
│   ├── database/
│   │   ├── rds.tf                   # RDS PostgreSQL
│   │   └── redis.tf                 # ElastiCache Redis
│   ├── storage/
│   │   ├── s3.tf                    # S3 buckets
│   │   └── ecr.tf                   # ECR repository
│   └── security/
│       ├── secrets.tf               # Secrets Manager
│       └── iam.tf                   # IAM roles and policies
│
├── environments/
│   ├── tiger/                       # Development environment
│   │   ├── terraform.tfvars         # Tiger-specific variables
│   │   └── backend.tf               # Tiger state backend
│   └── cheetah/                     # Staging environment
│       ├── terraform.tfvars         # Cheetah-specific variables
│       └── backend.tf               # Cheetah state backend
│
└── scripts/
    ├── setup-terraform-backend.sh   # Setup S3 backend
    ├── build-and-push-image.sh      # Build & push Docker images
    └── deploy.sh                    # Deployment script
```

---

## Initial Setup

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd fastapi-infrastructure
```

### Step 2: Create Terraform State Backend

The Terraform state will be stored in S3 with DynamoDB for locking.

```bash
# Run the backend setup script
chmod +x scripts/setup-terraform-backend.sh
./scripts/setup-terraform-backend.sh
```

This creates:
- S3 bucket: `fastapi-terraform-state`
- DynamoDB table: `fastapi-terraform-locks`

**Manual creation (alternative)**:

```bash
# Create S3 bucket
aws s3api create-bucket \
    --bucket fastapi-terraform-state \
    --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket fastapi-terraform-state \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket fastapi-terraform-state \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Create DynamoDB table
aws dynamodb create-table \
    --table-name fastapi-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

### Step 3: Configure AWS SES (for emails)

```bash
# Verify sender email
aws ses verify-email-identity --email-address noreply-tiger@yourdomain.com
aws ses verify-email-identity --email-address noreply-staging@yourdomain.com

# Check verification status
aws ses get-identity-verification-attributes \
    --identities noreply-tiger@yourdomain.com noreply-staging@yourdomain.com
```

### Step 4: Build Initial Docker Image

```bash
# Build FastAPI application image
docker build -t fastapi-app:latest .

# Note: You'll need to push to ECR after creating the repository
# This happens automatically during Terraform deployment
```

---

## Environment Configuration

### Tiger (Development) Environment

**File**: `terraform/environments/tiger/terraform.tfvars`

Key configurations:
- Single-AZ RDS (cost optimization)
- Single Redis node
- 1-4 ECS tasks (auto-scaling)
- 7-day backup retention
- No deletion protection

**Expected Monthly Cost**: ~$147

### Cheetah (Staging) Environment

**File**: `terraform/environments/cheetah/terraform.tfvars`

Key configurations:
- Multi-AZ RDS (high availability)
- Redis with replica
- 2-6 ECS tasks (auto-scaling)
- 14-day backup retention
- Deletion protection enabled
- Domain configuration

**Expected Monthly Cost**: ~$280

### Customizing Variables

Edit the respective `terraform.tfvars` file:

```hcl
# Example customizations
ecs_min_capacity = 2            # Minimum tasks
ecs_max_capacity = 10           # Maximum tasks
rds_instance_class = "db.t3.medium"  # Larger database
redis_node_type = "cache.t3.medium"  # Larger cache
```

---

## Deployment Process

### Method 1: Using Scripts (Recommended)

#### Deploy Tiger (Development)

```bash
# Plan deployment
./scripts/deploy.sh tiger plan

# Apply deployment
./scripts/deploy.sh tiger apply

# The script will:
# 1. Initialize Terraform
# 2. Validate configuration
# 3. Show planned changes
# 4. Ask for confirmation
# 5. Apply changes
```

#### Deploy Cheetah (Staging)

```bash
# Plan deployment
./scripts/deploy.sh cheetah plan

# Apply deployment
./scripts/deploy.sh cheetah apply
```

### Method 2: Using Makefile

```bash
# Tiger environment
make plan-tiger      # Plan changes
make apply-tiger     # Apply changes

# Cheetah environment
make plan-cheetah    # Plan changes
make apply-cheetah   # Apply changes
```

### Method 3: Manual Terraform Commands

```bash
# Navigate to environment directory
cd terraform/environments/tiger

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# Clean up plan file
rm tfplan
```

---

## Deployment Steps in Detail

### Phase 1: Network Infrastructure (~5 minutes)

Creates:
- VPC with public/private subnets
- Internet Gateway
- NAT Gateways (2x for HA)
- Route tables
- Security groups
- VPC endpoints

**Verification**:
```bash
# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=tiger"

# Check subnets
aws ec2 describe-subnets --filters "Name=tag:Environment,Values=tiger"
```

### Phase 2: Database & Cache (~10-15 minutes)

Creates:
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- Security groups for databases
- Secrets in Secrets Manager

**Verification**:
```bash
# Check RDS
aws rds describe-db-instances --query "DBInstances[?DBInstanceIdentifier=='fastapi-tiger-postgres']"

# Check Redis
aws elasticache describe-cache-clusters --cache-cluster-id fastapi-tiger-redis
```

### Phase 3: Storage & Registry (~2 minutes)

Creates:
- S3 buckets (logs, assets)
- ECR repository
- Bucket policies

**Verification**:
```bash
# Check S3 buckets
aws s3 ls | grep fastapi-tiger

# Check ECR
aws ecr describe-repositories --repository-names fastapi-tiger-app
```

### Phase 4: Compute & Load Balancer (~5 minutes)

Creates:
- ECS cluster
- Application Load Balancer
- Target groups
- ECS task definitions
- ECS services

**Verification**:
```bash
# Check ECS cluster
aws ecs describe-clusters --clusters fastapi-tiger-cluster

# Check ALB
aws elbv2 describe-load-balancers --names fastapi-tiger-alb
```

### Total Deployment Time
- **Tiger**: ~20-25 minutes
- **Cheetah**: ~30-40 minutes (Multi-AZ takes longer)

---

## Post-Deployment Configuration

### Step 1: Get Outputs

```bash
cd terraform/environments/tiger
terraform output

# Important outputs:
# - alb_dns_name: Load balancer URL
# - ecr_repository_url: Docker registry URL
# - rds_endpoint: Database endpoint
# - redis_endpoint: Redis endpoint
```

### Step 2: Push Docker Image to ECR

```bash
# Get ECR repository URL from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin $ECR_URL

# Tag your image
docker tag fastapi-app:latest $ECR_URL:latest

# Push image
docker push $ECR_URL:latest
```

**Using the helper script**:
```bash
./scripts/build-and-push-image.sh tiger latest
```

### Step 3: Update ECS Service

```bash
# Force new deployment to use the new image
aws ecs update-service \
    --cluster fastapi-tiger-cluster \
    --service fastapi-tiger-app-service \
    --force-new-deployment
```

### Step 4: Verify Application

```bash
# Get ALB DNS name
ALB_DNS=$(cd terraform/environments/tiger && terraform output -raw alb_dns_name)

# Test health endpoint
curl http://$ALB_DNS/health

# Should return:
# {"status":"healthy","version":"1.0.0"}
```

### Step 5: Configure Database

```bash
# Get database connection details from Secrets Manager
aws secretsmanager get-secret-value \
    --secret-id fastapi-tiger-secrets-XXXXX \
    --query SecretString \
    --output text | jq -r '.database_url'

# Run migrations (from ECS task or locally)
# Connect to database and run alembic migrations
```

### Step 6: Setup DNS (for Cheetah with domain)

```bash
# Get ALB details
ALB_DNS=$(cd terraform/environments/cheetah && terraform output -raw alb_dns_name)
ALB_ZONE=$(cd terraform/environments/cheetah && terraform output -raw alb_zone_id)

# Create Route53 record
aws route53 change-resource-record-sets \
    --hosted-zone-id YOUR_ZONE_ID \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "staging.yourdomain.com",
                "Type": "A",
                "AliasTarget": {
                    "HostedZoneId": "'$ALB_ZONE'",
                    "DNSName": "'$ALB_DNS'",
                    "EvaluateTargetHealth": true
                }
            }
        }]
    }'
```

---

## CI/CD Integration

### GitHub Actions Example

**`.github/workflows/deploy-tiger.yml`**:

```yaml
name: Deploy to Tiger (Dev)

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: fastapi-tiger-app
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
                     $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster fastapi-tiger-cluster \
            --service fastapi-tiger-app-service \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster fastapi-tiger-cluster \
            --services fastapi-tiger-app-service
```

### GitLab CI Example

**`.gitlab-ci.yml`**:

```yaml
stages:
  - build
  - deploy

variables:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: fastapi-tiger-app

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add --no-cache python3 py3-pip
    - pip3 install awscli
    - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY/$ECR_REPOSITORY:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY/$ECR_REPOSITORY:$CI_COMMIT_SHA
    - docker tag $CI_REGISTRY/$ECR_REPOSITORY:$CI_COMMIT_SHA $CI_REGISTRY/$ECR_REPOSITORY:latest
    - docker push $CI_REGISTRY/$ECR_REPOSITORY:latest
  only:
    - develop

deploy-tiger:
  stage: deploy
  image: amazon/aws-cli:latest
  script:
    - aws ecs update-service --cluster fastapi-tiger-cluster --service fastapi-tiger-app-service --force-new-deployment
    - aws ecs wait services-stable --cluster fastapi-tiger-cluster --services fastapi-tiger-app-service
  only:
    - develop
```

---

## Monitoring & Maintenance

### CloudWatch Dashboards

Access CloudWatch console to view:
- ECS task metrics (CPU, memory)
- ALB metrics (request count, latency)
- RDS metrics (connections, CPU)
- Redis metrics (memory, connections)

### CloudWatch Alarms

Pre-configured alarms:
- ECS CPU > 80%
- RDS CPU > 75%
- Redis CPU > 75%
- RDS free storage < 5GB
- ALB 5XX errors > 10

**Add SNS notifications**:

```bash
# Create SNS topic
aws sns create-topic --name fastapi-tiger-alerts

# Subscribe email
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:fastapi-tiger-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com
```

### Log Analysis

```bash
# View ECS logs
aws logs tail /ecs/fastapi-tiger-app --follow

# Query logs
aws logs filter-log-events \
    --log-group-name /ecs/fastapi-tiger-app \
    --filter-pattern "ERROR" \
    --start-time $(date -d '1 hour ago' +%s)000
```

### Database Backups

```bash
# Create manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier fastapi-tiger-postgres \
    --db-snapshot-identifier fastapi-tiger-manual-$(date +%Y%m%d-%H%M%S)

# List snapshots
aws rds describe-db-snapshots \
    --db-instance-identifier fastapi-tiger-postgres
```

---

## Troubleshooting

### Common Issues

#### 1. ECS Tasks Failing to Start

**Symptoms**: Tasks start then immediately stop

**Debugging**:
```bash
# Check task logs
aws logs tail /ecs/fastapi-tiger-app --follow

# Check task stopped reason
aws ecs describe-tasks \
    --cluster fastapi-tiger-cluster \
    --tasks TASK_ID \
    --query 'tasks[0].stoppedReason'
```

**Common causes**:
- Docker image not found in ECR
- Secrets Manager access denied
- Database connection failed
- Port already in use

#### 2. Cannot Connect to RDS

**Symptoms**: Connection timeout or refused

**Debugging**:
```bash
# Check security group rules
aws ec2 describe-security-groups \
    --filters "Name=tag:Name,Values=fastapi-tiger-rds-sg"

# Verify RDS endpoint
aws rds describe-db-instances \
    --db-instance-identifier fastapi-tiger-postgres \
    --query 'DBInstances[0].Endpoint'
```

**Solutions**:
- Verify security group allows ECS tasks SG
- Check subnet routing
- Verify credentials in Secrets Manager

#### 3. ALB Health Checks Failing

**Symptoms**: Targets marked unhealthy

**Debugging**:
```bash
# Check target health
aws elbv2 describe-target-health \
    --target-group-arn TARGET_GROUP_ARN
```

**Solutions**:
- Verify `/health` endpoint responds with 200
- Check security group allows ALB traffic
- Increase health check timeout

#### 4. Terraform State Lock

**Symptoms**: "Error locking state" message

**Solution**:
```bash
# Force unlock (use carefully!)
cd terraform/environments/tiger
terraform force-unlock LOCK_ID
```

---

## Cost Management

### Cost Monitoring

```bash
# View costs by service (last 30 days)
aws ce get-cost-and-usage \
    --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=SERVICE
```

### Cost Optimization Tips

1. **Schedule ECS tasks** (dev environment):
   ```bash
   # Scale down during off-hours
   aws application-autoscaling register-scalable-target \
       --service-namespace ecs \
       --resource-id service/fastapi-tiger-cluster/fastapi-tiger-app-service \
       --scalable-dimension ecs:service:DesiredCount \
       --min-capacity 0 \
       --max-capacity 4
   ```

2. **Use Fargate Spot** for non-critical workloads:
   - Edit `terraform.tfvars`
   - Set `enable_spot_instances = true`
   - Save up to 70%

3. **RDS Reserved Instances** (for stable workloads):
   - Purchase 1-year or 3-year reservations
   - Save up to 40%

4. **Delete unused resources**:
   ```bash
   # Find unused EBS volumes
   aws ec2 describe-volumes \
       --filters Name=status,Values=available \
       --query 'Volumes[*].[VolumeId,Size,CreateTime]'
   ```

### Budget Alerts

```bash
# Create budget
aws budgets create-budget \
    --account-id ACCOUNT_ID \
    --budget file://budget.json \
    --notifications-with-subscribers file://notifications.json
```

---

## Destroying Infrastructure

### Tiger (Development)

```bash
# Using script
./scripts/deploy.sh tiger destroy

# Or using Makefile
make destroy-tiger

# Manual
cd terraform/environments/tiger
terraform destroy
```

### Cheetah (Staging)

⚠️ **Warning**: Deletion protection is enabled for Cheetah

```bash
# First, disable deletion protection
# Edit terraform.tfvars:
# enable_deletion_protection = false

# Apply change
terraform apply

# Then destroy
./scripts/deploy.sh cheetah destroy
```

### Clean Up State Backend

```bash
# Delete S3 bucket
aws s3 rb s3://fastapi-terraform-state --force

# Delete DynamoDB table
aws dynamodb delete-table --table-name fastapi-terraform-locks
```

---

## Summary

This infrastructure provides:

✅ **Two isolated environments** (Tiger dev, Cheetah staging)  
✅ **High availability** with Multi-AZ deployment  
✅ **Auto-scaling** based on CPU/memory  
✅ **Secure** with encryption at rest and in transit  
✅ **Monitored** with CloudWatch alarms and logs  
✅ **Cost-optimized** with right-sized resources  
✅ **Production-ready** with backups and DR  

**Next Steps**:
1. Deploy Tiger environment for development
2. Test thoroughly
3. Deploy Cheetah for staging/pre-production
4. Integrate with CI/CD pipeline
5. Monitor costs and optimize
6. Plan production deployment