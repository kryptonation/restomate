# AWS Infrastructure Architecture - Tiger (Dev) & Cheetah (Staging)

## Table of Contents
1. [Infrastructure Overview](#infrastructure-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Components Breakdown](#components-breakdown)
4. [Network Architecture](#network-architecture)
5. [Security Architecture](#security-architecture)
6. [High Availability & Scalability](#high-availability--scalability)
7. [Cost Optimization](#cost-optimization)
8. [Environment Comparison](#environment-comparison)

---

## Infrastructure Overview

### Design Principles

1. **Environment Isolation**: Complete separation between Tiger (Dev) and Cheetah (Staging)
2. **Infrastructure as Code**: All resources managed via Terraform
3. **High Availability**: Multi-AZ deployment for critical components
4. **Security First**: VPC isolation, security groups, IAM least privilege
5. **Scalability**: Auto-scaling for application tier
6. **Cost Optimization**: Right-sized instances, scheduled scaling

### Technology Stack

- **Compute**: ECS Fargate (serverless containers)
- **Load Balancing**: Application Load Balancer (ALB)
- **Database**: RDS PostgreSQL (Multi-AZ for Staging)
- **Cache**: ElastiCache Redis (Multi-AZ for Staging)
- **Storage**: S3 for static assets, logs
- **CDN**: CloudFront for static content
- **Monitoring**: CloudWatch, CloudWatch Logs
- **Secrets**: AWS Secrets Manager
- **Email**: Amazon SES
- **SMS**: Amazon SNS
- **Container Registry**: ECR

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (Region: us-east-1)                   │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         VPC (10.0.0.0/16)                               │ │
│  │                                                                          │ │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                   │ │
│  │  │   Public Subnet 1    │  │   Public Subnet 2    │                   │ │
│  │  │   (10.0.1.0/24)      │  │   (10.0.2.0/24)      │                   │ │
│  │  │   AZ: us-east-1a     │  │   AZ: us-east-1b     │                   │ │
│  │  │                      │  │                      │                   │ │
│  │  │  ┌────────────────┐  │  │  ┌────────────────┐  │                   │ │
│  │  │  │      NAT       │  │  │  │      NAT       │  │                   │ │
│  │  │  │    Gateway     │  │  │  │    Gateway     │  │                   │ │
│  │  │  └────────────────┘  │  │  └────────────────┘  │                   │ │
│  │  └──────────┬───────────┘  └──────────┬───────────┘                   │ │
│  │             │                          │                               │ │
│  │  ┌──────────▼──────────────────────────▼───────────┐                  │ │
│  │  │              Application Load Balancer           │                  │ │
│  │  │           (internet-facing, multi-AZ)            │                  │ │
│  │  └──────────────────────┬───────────────────────────┘                  │ │
│  │                         │                                               │ │
│  │  ┌──────────────────────┴───────────────────────┐                     │ │
│  │  │            Private Subnet 1 & 2               │                     │ │
│  │  │         (10.0.10.0/24, 10.0.11.0/24)          │                     │ │
│  │  │              AZ: us-east-1a, 1b               │                     │ │
│  │  │                                               │                     │ │
│  │  │  ┌─────────────────────────────────────┐     │                     │ │
│  │  │  │       ECS Fargate Cluster           │     │                     │ │
│  │  │  │                                     │     │                     │ │
│  │  │  │  ┌──────────┐  ┌──────────┐        │     │                     │ │
│  │  │  │  │FastAPI   │  │FastAPI   │        │     │                     │ │
│  │  │  │  │Container │  │Container │        │     │                     │ │
│  │  │  │  │(Task 1)  │  │(Task 2)  │        │     │                     │ │
│  │  │  │  └──────────┘  └──────────┘        │     │                     │ │
│  │  │  │                                     │     │                     │ │
│  │  │  │  ┌──────────┐                      │     │                     │ │
│  │  │  │  │ Celery   │                      │     │                     │ │
│  │  │  │  │ Worker   │                      │     │                     │ │
│  │  │  │  └──────────┘                      │     │                     │ │
│  │  │  └─────────────────────────────────────┘     │                     │ │
│  │  └──────────────────────────────────────────────┘                     │ │
│  │                                                                          │ │
│  │  ┌──────────────────────────────────────────────┐                     │ │
│  │  │          Database Subnet 1 & 2                │                     │ │
│  │  │       (10.0.20.0/24, 10.0.21.0/24)            │                     │ │
│  │  │            AZ: us-east-1a, 1b                 │                     │ │
│  │  │                                               │                     │ │
│  │  │  ┌──────────────┐  ┌──────────────┐          │                     │ │
│  │  │  │ RDS Primary  │  │ RDS Standby  │          │                     │ │
│  │  │  │ PostgreSQL   │  │ PostgreSQL   │          │                     │ │
│  │  │  │ (Multi-AZ)   │  │              │          │                     │ │
│  │  │  └──────────────┘  └──────────────┘          │                     │ │
│  │  │                                               │                     │ │
│  │  │  ┌──────────────┐  ┌──────────────┐          │                     │ │
│  │  │  │ElastiCache   │  │ElastiCache   │          │                     │ │
│  │  │  │Redis Primary │  │Redis Replica │          │                     │ │
│  │  │  └──────────────┘  └──────────────┘          │                     │ │
│  │  └──────────────────────────────────────────────┘                     │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Additional Services                             │ │
│  │                                                                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │     ECR     │  │     S3      │  │ CloudFront  │  │   Secrets   │  │ │
│  │  │  Container  │  │   Bucket    │  │     CDN     │  │   Manager   │  │ │
│  │  │  Registry   │  │   (Logs)    │  │             │  │             │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  │                                                                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │  SES Email  │  │  SNS SMS    │  │ CloudWatch  │  │     IAM     │  │ │
│  │  │   Service   │  │   Service   │  │  Monitoring │  │    Roles    │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

                    Internet Gateway
                           ▲
                           │
                    ┌──────┴──────┐
                    │   Route 53  │
                    │     DNS     │
                    └─────────────┘
```

---

## Components Breakdown

### 1. Networking Components

#### VPC (Virtual Private Cloud)
- **CIDR**: 10.0.0.0/16
- **DNS**: Enabled
- **DNS Hostnames**: Enabled
- **Separate VPCs** for Tiger and Cheetah

#### Subnets

| Subnet Type | CIDR | Purpose | Internet Access |
|-------------|------|---------|-----------------|
| Public 1 | 10.0.1.0/24 | ALB, NAT Gateway | Yes (IGW) |
| Public 2 | 10.0.2.0/24 | ALB, NAT Gateway | Yes (IGW) |
| Private App 1 | 10.0.10.0/24 | ECS Tasks | Via NAT |
| Private App 2 | 10.0.11.0/24 | ECS Tasks | Via NAT |
| Private DB 1 | 10.0.20.0/24 | RDS, Redis | No |
| Private DB 2 | 10.0.21.0/24 | RDS, Redis | No |

#### Internet Gateway
- Provides internet access to public subnets
- Attached to VPC

#### NAT Gateways
- **Count**: 2 (one per AZ for HA)
- **Purpose**: Outbound internet access for private subnets
- **Elastic IPs**: Assigned for stable outbound IPs

#### Route Tables
- **Public RT**: Routes to IGW
- **Private RT 1**: Routes to NAT Gateway in AZ-1a
- **Private RT 2**: Routes to NAT Gateway in AZ-1b

### 2. Compute Components

#### ECS Cluster
- **Type**: Fargate (serverless)
- **Launch Type**: FARGATE
- **Container Insights**: Enabled

#### ECS Services

**FastAPI Service**:
- **Task Definition**: FastAPI container
- **Desired Count**: 
  - Tiger: 1
  - Cheetah: 2
- **CPU**: 512 (0.5 vCPU)
- **Memory**: 1024 MB (1 GB)
- **Auto Scaling**: 
  - Min: 1/2 (Tiger/Cheetah)
  - Max: 4/6 (Tiger/Cheetah)
  - Target CPU: 70%

**Celery Worker Service**:
- **Task Definition**: Celery container
- **Desired Count**: 1
- **CPU**: 256 (0.25 vCPU)
- **Memory**: 512 MB
- **Auto Scaling**: Disabled

#### Application Load Balancer
- **Scheme**: Internet-facing
- **Subnets**: Public subnets (multi-AZ)
- **Health Check**: `/health`
- **Listeners**: 
  - HTTP (80) → Redirect to HTTPS
  - HTTPS (443) → Target Group
- **SSL Certificate**: AWS Certificate Manager

### 3. Database Components

#### RDS PostgreSQL
- **Engine**: PostgreSQL 15
- **Instance Class**:
  - Tiger: db.t3.micro (1 vCPU, 1GB RAM)
  - Cheetah: db.t3.small (2 vCPU, 2GB RAM)
- **Multi-AZ**: 
  - Tiger: No
  - Cheetah: Yes
- **Storage**: 
  - Type: GP3
  - Size: 20GB (Tiger), 50GB (Cheetah)
  - Auto-scaling: Enabled
- **Backups**: 
  - Retention: 7 days (Tiger), 14 days (Cheetah)
  - Window: 03:00-04:00 UTC
- **Encryption**: Enabled (KMS)

#### ElastiCache Redis
- **Engine**: Redis 7.x
- **Node Type**:
  - Tiger: cache.t3.micro
  - Cheetah: cache.t3.small
- **Cluster Mode**: Disabled
- **Replication**:
  - Tiger: No replica
  - Cheetah: 1 replica (Multi-AZ)
- **Auto-failover**: Enabled (Cheetah only)
- **Encryption**: 
  - At-rest: Enabled
  - In-transit: Enabled

### 4. Storage Components

#### S3 Buckets

**Application Logs Bucket**:
- **Name**: `{env}-fastapi-logs-{account-id}`
- **Versioning**: Enabled
- **Lifecycle**: 
  - Transition to IA after 30 days
  - Delete after 90 days
- **Encryption**: AES-256

**Static Assets Bucket**:
- **Name**: `{env}-fastapi-assets-{account-id}`
- **Public Access**: Blocked
- **CloudFront**: Distribution configured
- **Versioning**: Enabled

#### ECR (Elastic Container Registry)
- **Repositories**:
  - `tiger-fastapi-app`
  - `cheetah-fastapi-app`
- **Image Scanning**: Enabled
- **Lifecycle Policy**: Keep last 10 images

### 5. Security Components

#### Security Groups

**ALB Security Group**:
- Inbound:
  - 80/tcp from 0.0.0.0/0
  - 443/tcp from 0.0.0.0/0
- Outbound: All traffic

**ECS Tasks Security Group**:
- Inbound:
  - 8000/tcp from ALB SG
- Outbound: All traffic

**RDS Security Group**:
- Inbound:
  - 5432/tcp from ECS Tasks SG
- Outbound: None

**Redis Security Group**:
- Inbound:
  - 6379/tcp from ECS Tasks SG
- Outbound: None

#### IAM Roles

**ECS Task Execution Role**:
- Permissions:
  - Pull images from ECR
  - Write logs to CloudWatch
  - Read secrets from Secrets Manager

**ECS Task Role**:
- Permissions:
  - Send emails via SES
  - Send SMS via SNS
  - Write to S3 buckets
  - Read from Secrets Manager

### 6. Monitoring & Logging

#### CloudWatch Log Groups
- `/ecs/tiger-fastapi-app`
- `/ecs/tiger-celery-worker`
- `/ecs/cheetah-fastapi-app`
- `/ecs/cheetah-celery-worker`
- **Retention**: 7 days (Tiger), 14 days (Cheetah)

#### CloudWatch Alarms
- CPU Utilization > 80%
- Memory Utilization > 80%
- ALB 5XX errors > 10
- RDS CPU > 75%
- Redis CPU > 75%

#### CloudWatch Metrics
- ECS Service metrics
- ALB metrics
- RDS metrics
- Redis metrics

### 7. Secrets Management

#### AWS Secrets Manager
Secrets stored:
- `{env}/fastapi/database-url`
- `{env}/fastapi/secret-key`
- `{env}/fastapi/aws-credentials`
- `{env}/fastapi/ses-config`

---

## Network Architecture

### Traffic Flow

```
Client Request
    ↓
Route 53 DNS
    ↓
CloudFront CDN (static content)
    ↓
Application Load Balancer (HTTPS)
    ↓
ECS Fargate Tasks (FastAPI)
    ↓
├─→ RDS PostgreSQL
├─→ ElastiCache Redis
├─→ S3 (for uploads)
├─→ SES (for emails)
└─→ SNS (for SMS)
```

### High Availability Design

1. **Multi-AZ Deployment**: All critical components in multiple AZs
2. **Load Balancing**: ALB distributes across AZ
3. **Auto-healing**: ECS replaces failed tasks
4. **Database Failover**: RDS Multi-AZ automatic failover
5. **Cache Failover**: Redis automatic failover (Cheetah)

---

## Security Architecture

### Defense in Depth

1. **Network Layer**:
   - VPC isolation
   - Public/Private subnet separation
   - Security groups (stateful firewall)
   - NACLs (optional, stateless firewall)

2. **Application Layer**:
   - ALB with WAF (optional)
   - HTTPS only (TLS 1.2+)
   - Security headers

3. **Data Layer**:
   - Encryption at rest (RDS, Redis, S3)
   - Encryption in transit (SSL/TLS)
   - Automated backups

4. **Access Control**:
   - IAM roles with least privilege
   - Secrets Manager for credentials
   - No hardcoded secrets

### Compliance Features

- **Encryption**: All data encrypted at rest and in transit
- **Audit Logging**: CloudTrail enabled
- **Backup**: Automated daily backups
- **Disaster Recovery**: Multi-AZ deployment

---

## High Availability & Scalability

### Availability Targets

| Environment | Target SLA | RPO | RTO |
|-------------|-----------|-----|-----|
| Tiger (Dev) | 95% | 24h | 4h |
| Cheetah (Staging) | 99% | 1h | 30m |

### Auto-Scaling Configuration

**ECS Service Auto-Scaling**:
```
Target Tracking Scaling Policy:
  - Metric: CPU Utilization
  - Target: 70%
  - Scale-out cooldown: 60s
  - Scale-in cooldown: 300s
```

**RDS Storage Auto-Scaling**:
```
- Maximum storage: 100GB
- Threshold: 90% usage
- Auto-grow by: 10GB
```

### Disaster Recovery

**Backup Strategy**:
- RDS automated backups: Daily
- Manual snapshots: Before deployments
- Redis snapshots: Daily
- S3 versioning: Enabled

**Recovery Procedures**:
1. Database: Restore from automated backup
2. Application: Redeploy from ECR
3. Configuration: Restore from Terraform state

---

## Cost Optimization

### Monthly Cost Estimates

#### Tiger (Development)
| Service | Configuration | Est. Monthly Cost |
|---------|--------------|-------------------|
| ECS Fargate | 1 task (0.5 vCPU, 1GB) | $15 |
| ALB | 1 ALB | $25 |
| RDS | db.t3.micro | $15 |
| ElastiCache | cache.t3.micro | $12 |
| NAT Gateway | 2 NAT Gateways | $70 |
| S3 | 10GB | $1 |
| Data Transfer | 100GB | $9 |
| **Total** | | **~$147/month** |

#### Cheetah (Staging)
| Service | Configuration | Est. Monthly Cost |
|---------|--------------|-------------------|
| ECS Fargate | 2 tasks (0.5 vCPU, 1GB each) | $30 |
| ALB | 1 ALB | $25 |
| RDS | db.t3.small (Multi-AZ) | $60 |
| ElastiCache | cache.t3.small (replica) | $48 |
| NAT Gateway | 2 NAT Gateways | $70 |
| S3 | 50GB | $2 |
| Data Transfer | 500GB | $45 |
| **Total** | | **~$280/month** |

### Cost Optimization Strategies

1. **Scheduled Scaling**:
   - Scale down Tiger during nights/weekends
   - Save ~30% on compute costs

2. **Reserved Capacity**:
   - Consider RDS Reserved Instances for Cheetah
   - 1-year term: ~40% savings

3. **S3 Lifecycle Policies**:
   - Automatic transition to Glacier
   - Delete old logs

4. **Right-Sizing**:
   - Monitor and adjust instance sizes
   - Use CloudWatch metrics

---

## Environment Comparison

| Feature | Tiger (Dev) | Cheetah (Staging) |
|---------|-------------|-------------------|
| **VPC CIDR** | 10.0.0.0/16 | 10.1.0.0/16 |
| **Availability Zones** | 2 | 2 |
| **ECS Tasks** | 1 (min) - 4 (max) | 2 (min) - 6 (max) |
| **Task CPU/Memory** | 0.5 vCPU / 1GB | 0.5 vCPU / 1GB |
| **RDS Instance** | db.t3.micro | db.t3.small |
| **RDS Multi-AZ** | No | Yes |
| **RDS Storage** | 20GB | 50GB |
| **Redis Instance** | cache.t3.micro | cache.t3.small |
| **Redis Replica** | No | Yes |
| **NAT Gateways** | 2 | 2 |
| **Backup Retention** | 7 days | 14 days |
| **Log Retention** | 7 days | 14 days |
| **CloudWatch Alarms** | Basic | Comprehensive |
| **SSL Certificate** | Self-signed | ACM |
| **Domain** | tiger.internal | staging.yourdomain.com |
| **Auto-scaling** | Yes | Yes |
| **Monthly Cost** | ~$147 | ~$280 |

This architecture provides a robust, scalable, and secure foundation for both development and staging environments.