#!/bin/bash
# GCP Initial Setup Script for WorkHub
# This script sets up all required GCP resources for deploying WorkHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - EDIT THESE VALUES
PROJECT_ID="${GCP_PROJECT_ID:-genai-workhub}"
REGION="${GCP_REGION:-us-central1}"  # Most cost-effective region with good reliability
DB_INSTANCE_NAME="workhub-db"
DB_VERSION="SQLSERVER_2022_STANDARD"
DB_TIER="db-custom-1-3840"  # 1 vCPU, 3.75 GB RAM
STORAGE_BUCKET="${PROJECT_ID}-workhub-uploads"
ARTIFACT_REPO="workhub-repo"
SERVICE_ACCOUNT_NAME="workhub-cloud-run-sa"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WorkHub GCP Setup Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Confirm with user
read -p "Proceed with setup? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Setting active project...${NC}"
gcloud config set project $PROJECT_ID

echo ""
echo -e "${YELLOW}Step 1: Enabling required APIs...${NC}"
gcloud services enable \
    cloudrun.googleapis.com \
    sqladmin.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com

echo ""
echo -e "${YELLOW}Step 2: Creating Artifact Registry repository...${NC}"
if gcloud artifacts repositories describe $ARTIFACT_REPO --location=$REGION &>/dev/null; then
    echo "  Repository already exists, skipping..."
else
    gcloud artifacts repositories create $ARTIFACT_REPO \
        --repository-format=docker \
        --location=$REGION \
        --description="WorkHub Docker images"
    echo -e "${GREEN}  ✓ Artifact Registry repository created${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Creating Cloud Storage bucket for file uploads...${NC}"
if gsutil ls gs://$STORAGE_BUCKET &>/dev/null; then
    echo "  Bucket already exists, skipping..."
else
    gsutil mb -p $PROJECT_ID -l $REGION gs://$STORAGE_BUCKET
    gsutil iam ch allUsers:objectViewer gs://$STORAGE_BUCKET  # Optional: make public
    echo -e "${GREEN}  ✓ Storage bucket created${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Creating Cloud SQL instance (this may take 10-15 minutes)...${NC}"
if gcloud sql instances describe $DB_INSTANCE_NAME &>/dev/null; then
    echo "  SQL instance already exists, skipping..."
else
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=$DB_VERSION \
        --tier=$DB_TIER \
        --region=$REGION \
        --root-password=$(openssl rand -base64 32) \
        --backup-start-time=03:00 \
        --enable-bin-log \
        --retained-backups-count=7 \
        --database-flags=contained_database_authentication=on
    echo -e "${GREEN}  ✓ Cloud SQL instance created${NC}"
fi

echo ""
echo -e "${YELLOW}Step 5: Creating database...${NC}"
if gcloud sql databases describe workhub --instance=$DB_INSTANCE_NAME &>/dev/null; then
    echo "  Database already exists, skipping..."
else
    gcloud sql databases create workhub --instance=$DB_INSTANCE_NAME
    echo -e "${GREEN}  ✓ Database created${NC}"
fi

echo ""
echo -e "${YELLOW}Step 6: Creating SQL user...${NC}"
DB_PASSWORD=$(openssl rand -base64 24)
if gcloud sql users list --instance=$DB_INSTANCE_NAME | grep -q "sqlserver"; then
    echo "  User already exists, updating password..."
    gcloud sql users set-password sqlserver \
        --instance=$DB_INSTANCE_NAME \
        --password=$DB_PASSWORD
else
    gcloud sql users create sqlserver \
        --instance=$DB_INSTANCE_NAME \
        --password=$DB_PASSWORD
fi
echo -e "${GREEN}  ✓ SQL user configured${NC}"

echo ""
echo -e "${YELLOW}Step 7: Creating service account for Cloud Run...${NC}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    echo "  Service account already exists, skipping..."
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="WorkHub Cloud Run Service Account"
    echo -e "${GREEN}  ✓ Service account created${NC}"
fi

echo ""
echo -e "${YELLOW}Step 8: Granting IAM roles to service account...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectAdmin" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None

echo -e "${GREEN}  ✓ IAM roles granted${NC}"

echo ""
echo -e "${YELLOW}Step 9: Creating secrets in Secret Manager...${NC}"

# Helper function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if gcloud secrets describe $secret_name &>/dev/null; then
        echo "  Updating secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    else
        echo "  Creating secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=-
    fi
}

# Generate secure random keys
SECRET_KEY=$(openssl rand -base64 48)
JWT_SECRET=$(openssl rand -base64 48)

create_or_update_secret "workhub-db-password" "$DB_PASSWORD"
create_or_update_secret "workhub-secret-key" "$SECRET_KEY"
create_or_update_secret "workhub-jwt-secret" "$JWT_SECRET"

echo ""
echo -e "${YELLOW}Please enter your SMTP/email configuration:${NC}"
read -p "SMTP Password (or press Enter to skip): " SMTP_PASSWORD
if [ ! -z "$SMTP_PASSWORD" ]; then
    create_or_update_secret "workhub-mail-password" "$SMTP_PASSWORD"
fi

echo -e "${GREEN}  ✓ Secrets created${NC}"

echo ""
echo -e "${YELLOW}Step 10: Getting Cloud SQL connection name...${NC}"
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe $DB_INSTANCE_NAME --format="value(connectionName)")
echo "  Connection name: $CLOUD_SQL_CONNECTION"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ GCP Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Important Information:${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Cloud SQL Connection: $CLOUD_SQL_CONNECTION"
echo "Storage Bucket: gs://$STORAGE_BUCKET"
echo "Artifact Registry: $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_REGION: $REGION"
echo "   - CLOUD_SQL_CONNECTION_NAME: $CLOUD_SQL_CONNECTION"
echo "   - CLOUD_STORAGE_BUCKET: $STORAGE_BUCKET"
echo "   - GCP_SERVICE_ACCOUNT_EMAIL: $SERVICE_ACCOUNT_EMAIL"
echo "   - DB_USER: sqlserver"
echo ""
echo "2. Create a service account key for GitHub Actions:"
echo "   gcloud iam service-accounts keys create key.json --iam-account=$SERVICE_ACCOUNT_EMAIL"
echo "   Then add the contents of key.json as GCP_SA_KEY secret in GitHub"
echo ""
echo "3. Configure your domain and SSL certificate (optional)"
echo "4. Push to main branch to trigger deployment"
echo ""
echo -e "${GREEN}Setup script completed successfully!${NC}"

