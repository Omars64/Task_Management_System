#!/bin/bash
# COMPLETE FIX: Configure VPC connector for database AND email
# VPC connector is REQUIRED for Cloud SQL private IP (10.119.176.3)
# But must have vpc-egress=all-traffic for email to work

PROJECT_ID="genai-workhub"
REGION="us-central1"
SERVICE_NAME="workhub-backend"

echo "=========================================="
echo "Complete Database + Email Network Fix"
echo "=========================================="
echo ""

# Check if VPC connector exists
VPC_CONNECTOR=$(gcloud compute networks vpc-access connectors list \
  --region=$REGION \
  --format="value(name)" 2>/dev/null | head -1)

if [ -z "$VPC_CONNECTOR" ]; then
    echo "Creating VPC connector for Cloud SQL access..."
    gcloud compute networks vpc-access connectors create workhub-connector \
      --region=$REGION \
      --network=default \
      --range=10.8.0.0/28 \
      --project=$PROJECT_ID
    
    if [ $? -eq 0 ]; then
        VPC_CONNECTOR="workhub-connector"
        echo "✅ VPC connector created: $VPC_CONNECTOR"
    else
        echo "❌ Failed to create VPC connector"
        exit 1
    fi
else
    echo "✅ VPC connector found: $VPC_CONNECTOR"
fi

echo ""
echo "Updating Cloud Run service with VPC connector and all-traffic egress..."
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --vpc-connector=$VPC_CONNECTOR \
  --vpc-egress=all-traffic \
  --project=$PROJECT_ID

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Service updated"
    echo "✅ Database: VPC connector enables private IP access (10.119.176.3)"
    echo "✅ Email: all-traffic egress enables outbound internet"
    echo ""
    echo "The service will restart with the new configuration."
    echo "Both database and email should work now!"
else
    echo ""
    echo "❌ Failed to update service"
    exit 1
fi

echo ""
echo "=========================================="
echo "Done!"

