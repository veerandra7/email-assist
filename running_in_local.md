# Manual Local Development - Email AI Assistant

## 🏠 Manual Local Development Setup (Without Docker)

This guide covers setting up the Email AI Assistant for manual local development without Docker. This approach gives you more control and faster iteration during development.

**Note**: For the simplest setup, use Docker Local instead: see [how_to_run.md](how_to_run.md) for Docker commands.

## 🐳 **Docker Commands for Local Development**

If you prefer Docker for local development, here are the key commands:

### **Quick Start Commands**
```bash
# Most common - build and start
docker-compose up --build

# Background mode
docker-compose up --build -d

# Clean rebuild (after code changes)
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Deep clean (remove everything and rebuild)
docker-compose down -v && docker system prune -f && docker-compose build --no-cache && docker-compose up -d
```

### **Development Workflow Commands**
```bash
# Daily development (no code changes)
docker-compose up -d

# With code changes
docker-compose down && docker-compose up --build -d

# With live logs (best for debugging)
docker-compose up --build

# Restart services
docker-compose restart

# Stop everything
docker-compose down
```

### **Management Commands**
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Health checks
curl http://localhost:8000/api/emails/health
curl http://localhost:3000/api/health

# Cleanup
docker-compose down -v
docker system prune -f
```

---

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** (recommended: 3.11 or 3.12)
- **Node.js 18+** (LTS version recommended)
- **npm 8+** or **yarn 1.22+**
- **Git** for version control

### Development Tools (Recommended)
- **VS Code** with Python and TypeScript extensions
- **Python extension** for VS Code
- **Docker Desktop** (for optional containerized services)
- **Postman** or **Insomnia** for API testing

## 🐍 Backend Development Setup

### 1. **Python Environment Setup**

#### Create Virtual Environment
```bash
# Navigate to project root
cd /path/to/email_assist

# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (should show venv in prompt)
which python  # Should point to venv/bin/python
```

#### Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### 2. **Environment Configuration**

#### Create Environment File
```bash
# Copy template
cp env_example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

#### Environment Variables
```env
# Claude AI API Key (Required)
CLAUDE_API_KEY=sk-ant-api03-your-actual-claude-api-key-here

# Gmail OAuth2 Configuration (Required)
GMAIL_CLIENT_ID=your-gmail-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your-gmail-client-secret

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# AI Service Configuration
MAX_EMAIL_LENGTH=10000
MAX_RESPONSE_LENGTH=2000

# CORS Settings (for development)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. **Gmail OAuth2 Setup**

#### Google Cloud Console Setup
1. **Create Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Note the project ID

2. **Enable Gmail API**:
   ```bash
   # Via console: APIs & Services → Library → Gmail API → Enable
   # Or via CLI:
   gcloud services enable gmail.googleapis.com
   ```

3. **Create OAuth2 Credentials**:
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type: Web application
   - Name: Email AI Assistant (Local Dev)
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:8000/auth/gmail/callback`

4. **Configure OAuth Consent Screen**:
   - APIs & Services → OAuth consent screen
   - Choose "External" (for testing with any Gmail account)
   - Fill required fields:
     - App name: Email AI Assistant
     - User support email: your-email@gmail.com
     - Developer contact: your-email@gmail.com
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.compose`

### 4. **Start Backend Development Server**

#### Development Mode (Recommended)
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Start with hot reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative with detailed logging
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

#### Verify Backend is Running
```bash
# Test health endpoint
curl http://localhost:8000/api/emails/health

# Expected response:
# {"status":"healthy","timestamp":"2024-01-01T12:00:00.000Z","service":"email-ai-backend"}

# Open API documentation
open http://localhost:8000/docs  # Swagger UI
open http://localhost:8000/redoc # ReDoc
```

## ⚛️ Frontend Development Setup

### 1. **Node.js Environment**

#### Navigate to Frontend Directory
```bash
# From project root
cd frontend

# Verify Node.js version
node --version  # Should be 18+
npm --version   # Should be 8+
```

#### Install Dependencies
```bash
# Install all dependencies
npm install

# Alternative: use yarn
yarn install

# Verify installation
npm list --depth=0
```

### 2. **Environment Configuration**

#### Create Environment File
```bash
# Copy template
cp env.local.example .env.local

# Edit environment file
nano .env.local
```

#### Environment Variables
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME="Email AI Assistant"
NEXT_PUBLIC_APP_VERSION="1.0.0"
NEXT_PUBLIC_AI_PROVIDER="Claude"

# Development Settings (optional)
NEXT_TELEMETRY_DISABLED=1
```

### 3. **Start Frontend Development Server**

#### Development Mode
```bash
# Start development server with hot reload
npm run dev

# Alternative: use yarn
yarn dev

# Alternative: specify port
npm run dev -- -p 3001

# With turbo mode (faster builds)
npm run dev --turbo
```

#### Verify Frontend is Running
```bash
# Test health endpoint
curl http://localhost:3000/api/health

# Open application
open http://localhost:3000
```

## 🔧 Development Workflow

### 1. **Code Organization**

#### Backend Structure
```
backend/
├── app/
│   ├── api/endpoints/     # API route handlers
│   ├── core/             # Configuration & exceptions
│   ├── models/           # Pydantic data models
│   ├── services/         # Business logic
│   └── main.py          # FastAPI application
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── .env                # Environment variables
```

#### Frontend Structure
```
frontend/
├── src/
│   ├── app/             # Next.js app router
│   ├── components/      # React components
│   ├── types/           # TypeScript definitions
│   └── utils/           # Utility functions
├── public/              # Static assets
├── package.json         # Dependencies
└── .env.local          # Environment variables
```

### 2. **Development Commands**

#### Backend Commands
```bash
# Start development server
python -m uvicorn app.main:app --reload

# Run tests
python -m pytest

# Run specific test
python -m pytest tests/test_ai_service.py

# Check code style
black app/
flake8 app/

# Type checking
mypy app/
```

#### Frontend Commands
```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix
```

### 3. **Hot Reload Configuration**

#### Backend Hot Reload
The `--reload` flag enables automatic reloading when Python files change:
```bash
# Files watched for changes:
# - app/**/*.py
# - .env file changes require manual restart
```

#### Frontend Hot Reload
Next.js automatically reloads on file changes:
```bash
# Files watched:
# - src/**/*.{js,ts,jsx,tsx}
# - .env.local (requires manual restart)
# - package.json changes require restart
```

## 🧪 Testing and Debugging

### 1. **API Testing**

#### Using curl
```bash
# Test health endpoints
curl http://localhost:8000/api/emails/health
curl http://localhost:8000/api/ai/health

# Test with authentication (after OAuth)
curl -H "Cookie: session_id=your_session" http://localhost:8000/api/emails/domains
```

#### Using Postman
1. Import API documentation from `http://localhost:8000/docs`
2. Set up environment variables for localhost
3. Test OAuth flow and protected endpoints

### 2. **Debug Configuration**

#### VS Code Debug Configuration (`.vscode/launch.json`)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/venv/bin/python",
      "args": ["-m", "uvicorn", "app.main:app", "--reload"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    },
    {
      "name": "Next.js: Debug",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/frontend/node_modules/next/dist/bin/next",
      "args": ["dev"],
      "cwd": "${workspaceFolder}/frontend",
      "console": "integratedTerminal"
    }
  ]
}
```

#### Backend Debugging
```python
# Add breakpoints in VS Code
# Or use pdb
import pdb; pdb.set_trace()

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Frontend Debugging
```typescript
// Browser DevTools
console.log('Debug info:', data);

// VS Code debugging with breakpoints
// React DevTools browser extension
```

### 3. **Common Development Issues**

#### Port Conflicts
```bash
# Check what's using a port
lsof -i :8000
lsof -i :3000

# Kill process using port
kill -9 $(lsof -t -i:8000)

# Use different ports
python -m uvicorn app.main:app --port 8001
npm run dev -- -p 3001
```

#### CORS Issues
```python
# In backend/app/core/config.py
allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
```

#### Environment Variable Issues
```bash
# Verify environment variables are loaded
# In Python
import os
print(os.getenv('CLAUDE_API_KEY'))

# In Node.js
console.log(process.env.NEXT_PUBLIC_API_URL)
```

## 📊 Performance Optimization

### 1. **Backend Optimization**

#### Enable Debug Mode
```python
# In .env
DEBUG=True

# Enables:
# - Detailed error messages
# - Auto-reload on code changes
# - Additional logging
```

#### Memory Monitoring
```bash
# Monitor Python memory usage
pip install memory-profiler
python -m memory_profiler your_script.py

# Monitor with htop
htop
```

### 2. **Frontend Optimization**

#### Development Build Analysis
```bash
# Analyze bundle size
npm run build -- --analyze

# Monitor build performance
npm run dev -- --debug

# Enable TypeScript strict mode for better DX
```

#### Browser DevTools
- Use React DevTools for component debugging
- Monitor Network tab for API calls
- Check Console for JavaScript errors

## 🔄 Git Workflow

### 1. **Branch Strategy**
```bash
# Feature development
git checkout -b feature/email-summarization
git commit -m "feat: add email summarization endpoint"
git push origin feature/email-summarization

# Bug fixes
git checkout -b fix/cors-issue
git commit -m "fix: resolve CORS configuration"
git push origin fix/cors-issue
```

### 2. **Pre-commit Hooks**
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Manual run
pre-commit run --all-files
```

## 🚀 Production Build Testing

### 1. **Backend Production Build**
```bash
# Test production settings
export DEBUG=False
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or with gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. **Frontend Production Build**
```bash
# Build for production
npm run build

# Test production build
npm start

# Analyze bundle
npm run build -- --analyze
```

---

*For Docker deployment, see [deployment_with_docker.md](deployment_with_docker.md)*
*For general running instructions, see [how_to_run.md](how_to_run.md)*
