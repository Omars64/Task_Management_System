#!/bin/bash
# IMMEDIATE FIX: Update Cloud Run VPC egress to fix email connectivity
# Run this script to immediately fix the "Network is unreachable" error

PROJECT_ID="genai-workhub"
REGION="us-central1"
SERVICE_NAME="workhub-backend"

echo "=========================================="
echo "Fixing Cloud Run VPC Egress (IMMEDIATE FIX)"
echo "=========================================="
echo ""

echo "Updating Cloud Run service to allow outbound internet access..."
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --vpc-egress=all-traffic \
  --project=$PROJECT_ID

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! VPC egress updated to ALL_TRAFFIC"
    echo "✅ Cloud Run can now reach external SMTP servers"
    echo ""
    echo "The service will restart with the new configuration."
    echo "Email functionality should work now!"
    echo ""
    echo "Test by signing up a new user and checking for verification email."
else
    echo ""
    echo "❌ Failed to update VPC egress"
    echo "Please check:"
    echo "  1. You have permission to update Cloud Run services"
    echo "  2. The service name is correct: $SERVICE_NAME"
    echo "  3. The region is correct: $REGION"
    echo "  4. The project ID is correct: $PROJECT_ID"
fi

