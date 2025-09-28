# How to Run - Email AI Assistant

## 🚀 Quick Start (Docker Local - Recommended)

The simplest way to get the Email AI Assistant running locally using Docker Compose.

### Prerequisites
- Docker Desktop installed and running
- Your API credentials (Claude API key and Gmail OAuth credentials)

### Step-by-Step Instructions

#### 1. **Configure Environment**
```bash
# Copy the environment template
cp docker.env.example .env

# Edit .env with your credentials
# Required:
# - CLAUDE_API_KEY=your_claude_api_key
# - GMAIL_CLIENT_ID=your_gmail_client_id  
# - GMAIL_CLIENT_SECRET=your_gmail_client_secret
```

#### 2. **Docker Commands - Choose Your Workflow**

##### 🎯 **Most Common - Build and Start**
```bash
# Build and start everything (foreground - see logs)
docker-compose up --build

# Build and start in background (detached mode)
docker-compose up --build -d
```

##### 🔄 **Clean Rebuild - Stop, Remove, Build, Start**
```bash
# Complete clean rebuild (recommended for code changes)
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# With logs (see what's happening)
docker-compose down && docker-compose build --no-cache && docker-compose up
```

##### 🧹 **Deep Clean - Remove Everything and Rebuild**
```bash
# Remove containers, volumes, and rebuild from scratch
docker-compose down -v && docker system prune -f && docker-compose build --no-cache && docker-compose up -d

# With logs
docker-compose down -v && docker system prune -f && docker-compose build --no-cache && docker-compose up
```

##### ⚡ **Quick Restart - Just Restart Services**
```bash
# Restart existing containers (no rebuild)
docker-compose restart

# Stop and start (clean restart)
docker-compose down && docker-compose up -d
```

##### 🔍 **Development Mode - With Live Logs**
```bash
# Start with live logs (best for development)
docker-compose up --build

# Start specific service with logs
docker-compose up --build backend
docker-compose up --build frontend
```

#### 3. **Access Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Docker Management Commands

### **Service Management**
```bash
# Check running containers
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### **Build Management**
```bash
# Build without starting
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend

# Rebuild without cache (clean build)
docker-compose build --no-cache

# Rebuild specific service without cache
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
```

### **Health Checks**
```bash
# Check service health
curl http://localhost:8000/api/emails/health
curl http://localhost:3000/api/health

# Check container status
docker-compose ps

# Check container logs for errors
docker-compose logs backend | grep -i error
docker-compose logs frontend | grep -i error
```

### **Cleanup Commands**
```bash
# Remove stopped containers
docker-compose rm

# Remove everything (containers, networks, volumes)
docker-compose down -v

# Clean up Docker system (removes unused images, containers, networks)
docker system prune -f

# Clean up everything (including volumes)
docker system prune -a -f --volumes

# Remove specific images
docker rmi $(docker images -q email_assist*)
```

## 🚨 Troubleshooting Commands

### **Port Conflicts**
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000

# Stop all Docker containers
docker stop $(docker ps -q)

# Kill processes using specific ports
kill -9 $(lsof -t -i:3000)
kill -9 $(lsof -t -i:8000)
```

### **Docker Issues**
```bash
# Check Docker is running
docker --version
docker ps

# Start Docker Desktop (macOS)
open /Applications/Docker.app

# Restart Docker daemon (Linux)
sudo systemctl restart docker
```

### **Environment Issues**
```bash
# Check environment file
cat .env

# Verify environment variables are loaded
docker-compose config

# Test with debug mode
DEBUG=true docker-compose up --build
```

### **Complete Reset**
```bash
# Nuclear option - remove everything and start fresh
docker-compose down -v
docker system prune -a -f --volumes
docker-compose build --no-cache
docker-compose up -d
```

## 🎯 **Recommended Workflows**

### **First Time Setup**
```bash
# 1. Configure environment
cp docker.env.example .env
# Edit .env with your credentials

# 2. Build and start
docker-compose up --build

# 3. Verify
curl http://localhost:8000/api/emails/health
open http://localhost:3000
```

### **Daily Development**
```bash
# Quick start (if no code changes)
docker-compose up -d

# With code changes
docker-compose down && docker-compose up --build -d

# With logs for debugging
docker-compose up --build
```

### **After Code Changes**
```bash
# Clean rebuild (recommended)
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Quick rebuild (faster)
docker-compose up --build -d
```

### **Production Testing**
```bash
# Build and test production mode
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check health
curl http://localhost:8000/api/emails/health
curl http://localhost:3000/api/health
```

## 🌐 Access URLs

### Application Access
- **Main Application**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Alternative Docs**: http://localhost:8000/redoc (ReDoc)

### Health Check Endpoints
- **Backend Health**: http://localhost:8000/api/emails/health
- **Frontend Health**: http://localhost:3000/api/health
- **AI Service Health**: http://localhost:8000/api/ai/health

## 🔍 Verification Steps

### 1. **Service Health Check**
```bash
# Check if services are running
curl http://localhost:8000/api/emails/health
curl http://localhost:3000/api/health

# Expected responses:
# Backend: {"status":"healthy","service":"email-ai-backend","version":"1.0.0"}
# Frontend: {"status":"healthy","timestamp":"2024-01-01T12:00:00.000Z","service":"email-ai-frontend"}
```

### 2. **Container Status Check**
```bash
# Check container health
docker-compose ps

# Expected output: All containers should show "Up" and "healthy"
```

### 3. **Gmail Authentication Test**
1. Open http://localhost:3000
2. Click "Connect Gmail" or authentication button
3. Complete OAuth flow
4. Verify you can see email domains

### 4. **AI Features Test**
1. Select an email domain
2. Choose an email
3. Click "Generate Summary"
4. Try "Generate Response"

## 🚨 Common Issues & Solutions

### **"Docker daemon not running"**
```bash
# Start Docker Desktop
open /Applications/Docker.app  # macOS
sudo systemctl start docker    # Linux
```

### **"Port already in use"**
```bash
# Find and stop conflicting processes
lsof -i :3000
lsof -i :8000
docker stop $(docker ps -q)
```

### **"API key not working"**
- Verify Claude API key is valid and active
- Check environment file format (no quotes around values)
- Restart services: `docker-compose restart`

### **"Gmail OAuth errors"**
- Verify redirect URI: `http://localhost:8000/auth/gmail/callback`
- Check Gmail API is enabled in Google Cloud Console
- Ensure OAuth consent screen is configured

### **"Frontend can't connect to backend"**
- Verify backend is running: `curl http://localhost:8000/api/emails/health`
- Check CORS configuration
- Restart both services: `docker-compose restart`

## 📊 Monitoring & Debugging

### **View Application Logs**
```bash
# All services with live updates
docker-compose logs -f

# Specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100

# Logs with timestamps
docker-compose logs -f -t
```

### **Container Status & Resources**
```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Container details
docker inspect email-ai-backend
docker inspect email-ai-frontend
```

### **Debug Mode**
```bash
# Start with debug logging
DEBUG=true docker-compose up --build

# Check environment variables
docker-compose config

# Execute commands in running container
docker-compose exec backend bash
docker-compose exec frontend sh
```

---

*For manual local development setup, see [running_in_local.md](running_in_local.md)*
*For cloud deployment instructions, see [deployment_with_docker.md](deployment_with_docker.md)*
