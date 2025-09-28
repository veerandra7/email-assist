#!/bin/bash

# Email AI Assistant - Docker Deployment Script
# This script helps deploy the application using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f "docker.env.example" ]; then
            cp docker.env.example .env
            print_warning "Please edit .env file and add your API credentials:"
            print_warning "  - CLAUDE_API_KEY (required)"
            print_warning "  - GMAIL_CLIENT_ID (required)"
            print_warning "  - GMAIL_CLIENT_SECRET (required)"

            print_error "Deployment stopped. Please configure .env file first."
            exit 1
        else
            print_error "Template file docker.env.example not found"
            exit 1
        fi
    fi
    
    # Check if required variables are set
    source .env
    
    if [ -z "$CLAUDE_API_KEY" ] || [ "$CLAUDE_API_KEY" = "your_claude_api_key_here" ]; then
        print_error "CLAUDE_API_KEY not set in .env file"
        exit 1
    fi
    
    if [ -z "$GMAIL_CLIENT_ID" ] || [ "$GMAIL_CLIENT_ID" = "your_gmail_client_id_here" ]; then
        print_error "GMAIL_CLIENT_ID not set in .env file"
        exit 1
    fi
    
    if [ -z "$GMAIL_CLIENT_SECRET" ] || [ "$GMAIL_CLIENT_SECRET" = "your_gmail_client_secret_here" ]; then
        print_error "GMAIL_CLIENT_SECRET not set in .env file"
        exit 1
    fi
    

    
    print_success "Environment configuration is valid"
}

# Main deployment function
deploy() {
    print_status "Starting Email AI Assistant deployment..."
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose down 2>/dev/null || true
    
    # Build and start services
    print_status "Building and starting services..."
    docker-compose up --build -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    print_status "Checking service health..."
    
    # Check backend health
    for i in {1..30}; do
        if curl -sf http://localhost:8000/api/emails/health > /dev/null 2>&1; then
            print_success "Backend service is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend service health check failed"
            docker-compose logs backend
            exit 1
        fi
        sleep 2
    done
    
    # Check frontend health
    for i in {1..30}; do
        if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
            print_success "Frontend service is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Frontend service health check failed"
            docker-compose logs frontend
            exit 1
        fi
        sleep 2
    done
    
    print_success "Deployment completed successfully!"
    echo ""
    print_status "Application URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo ""
    print_status "To view logs: docker-compose logs -f"
    print_status "To stop: docker-compose down"
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker-compose logs -f
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# Function to clean up (remove volumes)
cleanup() {
    print_warning "This will remove all data including user credentials and sessions."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing services and volumes..."
        docker-compose down -v
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to show status
show_status() {
    print_status "Service status:"
    docker-compose ps
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        check_docker
        check_env_file
        deploy
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help")
        echo "Email AI Assistant - Docker Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy  (default) - Deploy the application"
        echo "  logs             - Show application logs"
        echo "  stop             - Stop services"
        echo "  status           - Show service status"
        echo "  cleanup          - Stop services and remove volumes"
        echo "  help             - Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        print_status "Run '$0 help' for usage information"
        exit 1
        ;;
esac 