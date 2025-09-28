# Cloud Deployment - Email AI Assistant

## 🌐 Overview

This guide covers deploying the Email AI Assistant to various cloud platforms using Docker containers. The application is designed to be cloud-native and platform-agnostic.

**Note**: This is for production cloud deployment. For local development, see [how_to_run.md](how_to_run.md)

## 🏗️ Deployment Architecture

### Container Structure
- **Backend Container**: FastAPI application with Python runtime
- **Frontend Container**: Next.js application with Node.js runtime
- **Volumes**: Persistent storage for user credentials and sessions
- **Networks**: Isolated container communication

### Resource Requirements
- **Backend**: 512MB RAM, 1 vCPU minimum
- **Frontend**: 256MB RAM, 0.5 vCPU minimum
- **Storage**: 1GB for persistent volumes
- **Network**: HTTP/HTTPS traffic on ports 3000 and 8000

## 🚀 Quick Cloud Deployment

### Prerequisites
- Docker images built and tested locally
- Environment variables configured
- Cloud platform account and CLI tools

### Build and Push Images
```bash
# Build production images
docker build -t your-registry/email-ai-backend:latest ./backend
docker build -t your-registry/email-ai-frontend:latest ./frontend

# Push to registry
docker push your-registry/email-ai-backend:latest
docker push your-registry/email-ai-frontend:latest
```

## ☁️ Platform-Specific Deployment

### AWS Deployment

#### Option 1: AWS ECS (Recommended)

**1. Create ECS Cluster**
```bash
# Using AWS CLI
aws ecs create-cluster --cluster-name email-ai-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

**Task Definition Example** (`task-definition.json`):
```json
{
  "family": "email-ai-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/email-ai-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "CLAUDE_API_KEY", "value": "your-api-key"},
        {"name": "GMAIL_CLIENT_ID", "value": "your-client-id"},
        {"name": "GMAIL_CLIENT_SECRET", "value": "your-client-secret"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/email-ai",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "frontend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/email-ai-frontend:latest",
      "portMappings": [{"containerPort": 3000}],
      "environment": [
        {"name": "NEXT_PUBLIC_API_URL", "value": "https://api.yourdomain.com"}
      ],
      "dependsOn": [{"containerName": "backend", "condition": "HEALTHY"}]
    }
  ]
}
```

**2. Create Service with Load Balancer**
```bash
# Create service
aws ecs create-service \
  --cluster email-ai-cluster \
  --service-name email-ai-service \
  --task-definition email-ai-app \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:region:account:targetgroup/email-ai-tg/123456,containerName=frontend,containerPort=3000"
```

#### Option 2: AWS Lambda (Serverless)

**Using AWS SAM** (`template.yaml`):
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  EmailAIBackend:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      ImageUri: your-account.dkr.ecr.region.amazonaws.com/email-ai-backend:latest
      Environment:
        Variables:
          CLAUDE_API_KEY: !Ref ClaudeApiKey
          GMAIL_CLIENT_ID: !Ref GmailClientId
          GMAIL_CLIENT_SECRET: !Ref GmailClientSecret
      Events:
        Api:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

### Google Cloud Platform

#### Google Cloud Run (Recommended)

**1. Deploy Backend**
```bash
# Build and deploy backend
gcloud run deploy email-ai-backend \
  --image gcr.io/your-project/email-ai-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CLAUDE_API_KEY=your-api-key,GMAIL_CLIENT_ID=your-client-id,GMAIL_CLIENT_SECRET=your-client-secret \
  --memory 1Gi \
  --cpu 1
```

**2. Deploy Frontend**
```bash
# Deploy frontend with backend URL
gcloud run deploy email-ai-frontend \
  --image gcr.io/your-project/email-ai-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=https://email-ai-backend-hash-uc.a.run.app \
  --memory 512Mi \
  --cpu 0.5
```

**3. Configure Custom Domain**
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service email-ai-frontend \
  --domain yourdomain.com \
  --region us-central1
```

#### Google Kubernetes Engine (GKE)

**Deployment YAML** (`k8s-deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: email-ai-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: email-ai-backend
  template:
    metadata:
      labels:
        app: email-ai-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project/email-ai-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: email-ai-secrets
              key: claude-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: email-ai-backend-service
spec:
  selector:
    app: email-ai-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Microsoft Azure

#### Azure Container Instances

**1. Create Resource Group**
```bash
az group create --name email-ai-rg --location eastus
```

**2. Deploy Containers**
```bash
# Deploy using container group
az container create \
  --resource-group email-ai-rg \
  --name email-ai-app \
  --image your-registry/email-ai-backend:latest \
  --dns-name-label email-ai-unique \
  --ports 8000 3000 \
  --environment-variables \
    CLAUDE_API_KEY=your-api-key \
    GMAIL_CLIENT_ID=your-client-id \
    GMAIL_CLIENT_SECRET=your-client-secret \
  --memory 2 \
  --cpu 1
```

#### Azure Kubernetes Service (AKS)

**1. Create AKS Cluster**
```bash
az aks create \
  --resource-group email-ai-rg \
  --name email-ai-cluster \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

**2. Deploy Application**
```bash
# Get credentials
az aks get-credentials --resource-group email-ai-rg --name email-ai-cluster

# Apply Kubernetes manifests
kubectl apply -f k8s-deployment.yaml
```

### Digital Ocean

#### App Platform

**App Spec** (`.do/app.yaml`):
```yaml
name: email-ai-assistant
services:
- name: backend
  source_dir: /backend
  github:
    repo: your-username/email-ai-assistant
    branch: main
  run_command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: CLAUDE_API_KEY
    value: your-api-key
    type: SECRET
  - key: GMAIL_CLIENT_ID
    value: your-client-id
    type: SECRET
  - key: GMAIL_CLIENT_SECRET
    value: your-client-secret
    type: SECRET
  http_port: 8000
- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/email-ai-assistant
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: NEXT_PUBLIC_API_URL
    value: ${backend.PUBLIC_URL}
  http_port: 3000
```

**Deploy using CLI**
```bash
# Install doctl
# Create app
doctl apps create --spec .do/app.yaml

# Update app
doctl apps update YOUR_APP_ID --spec .do/app.yaml
```

### Heroku

#### Using Container Registry

**1. Login and Create Apps**
```bash
# Login to Heroku
heroku login
heroku container:login

# Create apps
heroku create email-ai-backend-app
heroku create email-ai-frontend-app
```

**2. Deploy Backend**
```bash
# Build and push
cd backend
heroku container:push web --app email-ai-backend-app
heroku container:release web --app email-ai-backend-app

# Set environment variables
heroku config:set CLAUDE_API_KEY=your-api-key --app email-ai-backend-app
heroku config:set GMAIL_CLIENT_ID=your-client-id --app email-ai-backend-app
heroku config:set GMAIL_CLIENT_SECRET=your-client-secret --app email-ai-backend-app
```

**3. Deploy Frontend**
```bash
# Build and push
cd frontend
heroku container:push web --app email-ai-frontend-app
heroku container:release web --app email-ai-frontend-app

# Set environment variables
heroku config:set NEXT_PUBLIC_API_URL=https://email-ai-backend-app.herokuapp.com --app email-ai-frontend-app
```

## 🔐 Security Best Practices

### Environment Variables
```bash
# Use secret management services
# AWS: AWS Secrets Manager or Parameter Store
# GCP: Secret Manager
# Azure: Key Vault
# Never hardcode secrets in images
```

### Network Security
```yaml
# Configure security groups/firewall rules
# Allow HTTPS (443) and HTTP (80) from internet
# Allow backend port (8000) only from frontend
# Block direct access to backend from internet
```

### SSL/TLS Configuration
```bash
# Use cloud provider's managed certificates
# AWS: ACM (AWS Certificate Manager)
# GCP: Google-managed certificates
# Azure: App Service certificates
```

## 📊 Monitoring and Logging

### Application Monitoring
```yaml
# Health check endpoints
healthCheck:
  path: /api/emails/health
  intervalSeconds: 30
  timeoutSeconds: 5
```

### Logging Configuration
```bash
# Centralized logging
# AWS: CloudWatch Logs
# GCP: Cloud Logging
# Azure: Azure Monitor
```

### Metrics and Alerts
```yaml
# Set up alerts for:
# - Container restarts
# - High CPU/memory usage
# - Application errors
# - Response time degradation
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy to Cloud
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push images
      run: |
        docker build -t $REGISTRY/email-ai-backend:$GITHUB_SHA ./backend
        docker build -t $REGISTRY/email-ai-frontend:$GITHUB_SHA ./frontend
        docker push $REGISTRY/email-ai-backend:$GITHUB_SHA
        docker push $REGISTRY/email-ai-frontend:$GITHUB_SHA
    
    - name: Deploy to cloud
      run: |
        # Cloud-specific deployment commands
```

## 💰 Cost Optimization

### Resource Right-sizing
- Start with minimal resources
- Monitor usage and scale as needed
- Use auto-scaling where available

### Reserved Instances
- Use reserved instances for production
- Consider spot instances for development

### Storage Optimization
- Use appropriate storage classes
- Implement lifecycle policies
- Regular cleanup of unused resources

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs container-id

# Common causes:
# - Missing environment variables
# - Port conflicts
# - Resource constraints
```

#### Application Unreachable
```bash
# Check network configuration
# Verify security groups/firewall rules
# Check load balancer health checks
```

#### Performance Issues
```bash
# Monitor resource usage
# Check application logs for errors
# Verify database connections
# Review AI API rate limits
```

---

*For local development, see [running_in_local.md](running_in_local.md)*
*For general running instructions, see [how_to_run.md](how_to_run.md)* 