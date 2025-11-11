#!/bin/bash
# COMPLETE FIX: Remove VPC connector to enable default outbound internet access
# Cloud Run has outbound internet access by default when no VPC connector is attached

PROJECT_ID="genai-workhub"
REGION="us-central1"
SERVICE_NAME="workhub-backend"

echo "=========================================="
echo "Complete Email Network Fix"
echo "=========================================="
echo ""

# Check current configuration
echo "Checking current Cloud Run service configuration..."
CURRENT_VPC_CONNECTOR=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="value(spec.template.spec.containers[0].vpcAccess.connector)" 2>/dev/null || echo "")

CURRENT_VPC_EGRESS=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="value(spec.template.spec.containers[0].vpcAccess.egress)" 2>/dev/null || echo "NONE")

echo "Current VPC connector: ${CURRENT_VPC_CONNECTOR:-none}"
echo "Current VPC egress: ${CURRENT_VPC_EGRESS:-default}"
echo ""

# The fix: Remove VPC connector to use default outbound internet access
# Cloud Run has outbound internet access by default when no VPC connector is attached
if [ -n "$CURRENT_VPC_CONNECTOR" ]; then
    echo "Removing VPC connector to enable default outbound internet access..."
    gcloud run services update $SERVICE_NAME \
      --region=$REGION \
      --clear-vpc-connector \
      --project=$PROJECT_ID
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ SUCCESS! VPC connector removed"
        echo "✅ Cloud Run now uses default outbound internet access"
        echo "✅ Email connectivity should work now"
        echo ""
        echo "The service will restart with the new configuration."
        echo "Test by signing up a new user and checking for verification email."
    else
        echo ""
        echo "❌ Failed to remove VPC connector"
        exit 1
    fi
else
    echo "No VPC connector attached - Cloud Run should have default outbound internet access"
    echo ""
    echo "If email still fails, the issue might be:"
    echo "  1. Firewall rules blocking outbound SMTP (port 587)"
    echo "  2. Service account permissions"
    echo "  3. Email credentials not configured correctly"
    echo ""
    echo "Check email configuration in Settings → System Settings"
fi

echo ""
echo "=========================================="
echo "Done!"

