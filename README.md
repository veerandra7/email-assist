# Email AI Assistant

A modern, AI-powered email management and response system built with React (Next.js) frontend and Python (FastAPI) backend, powered by Anthropic's Claude AI.

## 🎬 Demo

Watch a quick demonstration of the Email AI Assistant in action:

[![Demo Video](Demo.mp4)](Demo.mp4)

*Note: Download or view the [Demo.mp4](Demo.mp4) file to see the application in action.*

## 📋 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[how_to_run.md](how_to_run.md)** | Docker setup & commands | Quick local setup with Docker |
| **[running_in_local.md](running_in_local.md)** | Manual development setup | Development without Docker |
| **[deployment_with_docker.md](deployment_with_docker.md)** | Cloud deployment guide | Production deployment |
| **[api_documentation.md](api_documentation.md)** | Complete API reference | API integration & testing |
| **[product_description.md](product_description.md)** | Product features & capabilities | Understanding what the app does |

## 🎯 Key Features

- **🧠 AI Email Summarization**: Get concise summaries with key points and action items
- **✍️ Intelligent Response Generation**: Create context-aware replies with customizable tone
- **📊 Smart Domain Analysis**: Automatically rank email domains by importance
- **🔒 Secure Gmail Integration**: OAuth2 authentication with Gmail API
- **🎨 Modern UI**: Beautiful, responsive interface built with React and Tailwind CSS
- **🐳 Docker Ready**: Fully containerized for easy deployment


## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Claude API key from Anthropic
- Gmail OAuth credentials from Google Cloud Console

### Get Running in 5 Minutes
```bash
# 1. Clone and navigate to project
git clone <repository-url>
cd email_assist

# 2. Configure environment
cp docker.env.example .env
# Edit .env with your API credentials

# 3. Build and start everything
docker-compose up --build

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🏗️ Architecture

### Technology Stack
- **Frontend**: React 18, Next.js 14, TypeScript, Tailwind CSS
- **Backend**: Python 3.12, FastAPI, Pydantic
- **AI**: Anthropic Claude API
- **Authentication**: Gmail OAuth2
- **Deployment**: Docker, Docker Compose

### Project Structure
```
email_assist/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/endpoints/   # API route handlers
│   │   ├── core/           # Configuration & exceptions
│   │   ├── models/         # Pydantic data models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container config
├── frontend/               # React Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   ├── types/         # TypeScript definitions
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Frontend container config
├── docker-compose.yml      # Multi-container orchestration
└── deploy.sh              # Deployment script
```

## 🔧 Development

### Docker Commands (Recommended)
```bash
# Daily development
docker-compose up --build -d

# With live logs
docker-compose up --build

# Clean rebuild
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Stop everything
docker-compose down
```

### Manual Development
For detailed manual setup without Docker, see [running_in_local.md](running_in_local.md).

## 🚀 Deployment

### Local Testing
Use Docker commands above for local development and testing.

### Production Deployment
See [deployment_with_docker.md](deployment_with_docker.md) for comprehensive cloud deployment instructions covering:
- AWS ECS, EKS
- Google Cloud Run, GKE
- Azure Container Instances, AKS
- DigitalOcean Apps Platform
- Railway, Heroku

## 🔐 Configuration

### Required Environment Variables
```env
# Claude AI API Key (Required)
CLAUDE_API_KEY=sk-ant-api03-your-actual-claude-api-key

# Gmail OAuth2 Configuration (Required)
GMAIL_CLIENT_ID=your-gmail-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your-gmail-client-secret

# Application Settings (Optional)
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Getting API Credentials
1. **Claude API**: Sign up at [Anthropic Console](https://console.anthropic.com/)
2. **Gmail OAuth**: Create credentials in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs

## 🧪 Testing

### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/emails/health

# Frontend health
curl http://localhost:3000/api/health

# API documentation
open http://localhost:8000/docs
```

### Development Tools
- **Backend**: FastAPI interactive docs at `/docs`
- **Frontend**: React DevTools browser extension
- **API Testing**: Use Postman or Insomnia

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- 📖 **Documentation**: Check the [Documentation Index](#-documentation-index) above
- 🐛 **Issues**: Create an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions for questions

---

**Quick Links:**
- [🚀 How to Run](how_to_run.md) - Get started with Docker
- [💻 Local Development](running_in_local.md) - Manual setup guide
- [☁️ Cloud Deployment](deployment_with_docker.md) - Production deployment
- [📚 API Documentation](api_documentation.md) - Complete API reference
