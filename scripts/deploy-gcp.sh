#!/bin/bash
# Manual deployment script for WorkHub to GCP
# Use this for manual deployments outside of CI/CD pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-genai-workhub}"
REGION="${GCP_REGION:-us-central1}"  # Most cost-effective region with good reliability
ARTIFACT_REPO="workhub-repo"
BACKEND_SERVICE="workhub-backend"
FRONTEND_SERVICE="workhub-frontend"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WorkHub GCP Deployment Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found. Please install it first.${NC}"
    exit 1
fi

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Confirm with user
read -p "Deploy to production? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Setting active project...${NC}"
gcloud config set project $PROJECT_ID

echo ""
echo -e "${YELLOW}Configuring Docker authentication...${NC}"
gcloud auth configure-docker $REGION-docker.pkg.dev

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Building Backend${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

BACKEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$BACKEND_SERVICE"
cd workhub-backend

echo -e "${YELLOW}Building backend Docker image...${NC}"
docker build -t $BACKEND_IMAGE:latest .

echo -e "${YELLOW}Pushing backend image to Artifact Registry...${NC}"
docker push $BACKEND_IMAGE:latest

cd ..

echo -e "${GREEN}✓ Backend image built and pushed${NC}"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Building Frontend${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)' 2>/dev/null || echo "https://$BACKEND_SERVICE-placeholder.a.run.app")

FRONTEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$FRONTEND_SERVICE"
cd workhub-frontend

echo -e "${YELLOW}Building frontend Docker image...${NC}"
echo "API URL: $BACKEND_URL"
docker build --build-arg VITE_API_URL=$BACKEND_URL -t $FRONTEND_IMAGE:latest .

echo -e "${YELLOW}Pushing frontend image to Artifact Registry...${NC}"
docker push $FRONTEND_IMAGE:latest

cd ..

echo -e "${GREEN}✓ Frontend image built and pushed${NC}"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploying to Cloud Run${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

# Get Cloud SQL connection name
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe workhub-db --format="value(connectionName)" 2>/dev/null || echo "")

if [ -z "$CLOUD_SQL_CONNECTION" ]; then
    echo -e "${RED}Warning: Cloud SQL instance not found. Deployment may fail.${NC}"
    read -p "Continue anyway? (yes/no): " continue_deploy
    if [ "$continue_deploy" != "yes" ]; then
        echo "Deployment cancelled."
        exit 0
    fi
fi

SERVICE_ACCOUNT_EMAIL="workhub-cloud-run-sa@${PROJECT_ID}.iam.gserviceaccount.com"
STORAGE_BUCKET="${PROJECT_ID}-workhub-uploads"

echo ""
echo -e "${YELLOW}Deploying backend to Cloud Run...${NC}"
gcloud run deploy $BACKEND_SERVICE \
    --image $BACKEND_IMAGE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 2 \
    --max-instances 10 \
    --concurrency 80 \
    --cpu-boost \
    --timeout 300 \
    --set-cloudsql-instances $CLOUD_SQL_CONNECTION \
    --set-secrets DB_PASSWORD=workhub-db-password:latest,SECRET_KEY=workhub-secret-key:latest,JWT_SECRET_KEY=workhub-jwt-secret:latest,MAIL_PASSWORD=workhub-mail-password:latest \
    --set-env-vars CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,DB_HOST=10.119.176.3,DB_PORT=1433,DB_NAME=workhub,DB_USER=sqlserver,DB_DIALECT=mssql,USE_CLOUD_STORAGE=true,CLOUD_STORAGE_BUCKET=$STORAGE_BUCKET,GCP_PROJECT=$PROJECT_ID,FLASK_ENV=production,EMAIL_NOTIFICATIONS_ENABLED=true \
    --service-account $SERVICE_ACCOUNT_EMAIL

echo -e "${GREEN}✓ Backend deployed${NC}"

# Get the actual backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')

echo ""
echo -e "${YELLOW}Deploying frontend to Cloud Run...${NC}"
gcloud run deploy $FRONTEND_SERVICE \
    --image $FRONTEND_IMAGE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 2 \
    --max-instances 5 \
    --timeout 60 \
    --port 80 \
    --service-account $SERVICE_ACCOUNT_EMAIL

echo -e "${GREEN}✓ Frontend deployed${NC}"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Verifying Deployment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

echo ""
echo -e "${YELLOW}Testing backend health endpoint...${NC}"
if curl -f "$BACKEND_URL/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

echo ""
echo -e "${YELLOW}Testing frontend...${NC}"
if curl -f "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend check failed${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Your WorkHub instance is now live:${NC}"
echo ""
echo -e "${BLUE}Backend:${NC}  $BACKEND_URL"
echo -e "${BLUE}Frontend:${NC} $FRONTEND_URL"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the application at: $FRONTEND_URL"
echo "2. Configure custom domain (optional)"
echo "3. Set up monitoring and alerts"
echo "4. Review logs: gcloud logging read --limit 50"
echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"

