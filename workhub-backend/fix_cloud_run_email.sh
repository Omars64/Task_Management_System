#!/bin/bash
# Script to fix Cloud Run email network connectivity issue
# This updates the Cloud Run service to ensure outbound internet access

PROJECT_ID="genai-workhub"
REGION="us-central1"
SERVICE_NAME="workhub-backend"

echo "=========================================="
echo "Fixing Cloud Run Email Network Access"
echo "=========================================="
echo ""

# Check if VPC connector exists
echo "Checking for VPC connector..."
VPC_CONNECTOR=$(gcloud compute networks vpc-access connectors list --region=$REGION --format="value(name)" 2>/dev/null | head -1)

if [ -n "$VPC_CONNECTOR" ]; then
    echo "VPC connector found: $VPC_CONNECTOR"
    echo "Updating Cloud Run service with VPC egress configuration..."
    gcloud run services update $SERVICE_NAME \
        --region=$REGION \
        --vpc-egress=all-traffic \
        --vpc-connector=$VPC_CONNECTOR \
        --quiet
    echo "✓ Service updated with VPC egress configuration"
else
    echo "No VPC connector found. Cloud Run should have outbound access by default."
    echo ""
    echo "If emails still fail, try one of these solutions:"
    echo ""
    echo "Option 1: Create a VPC connector (if needed for other services)"
    echo "  gcloud compute networks vpc-access connectors create workhub-connector \\"
    echo "    --region=$REGION \\"
    echo "    --network=default \\"
    echo "    --range=10.8.0.0/28"
    echo ""
    echo "Option 2: Use SendGrid instead of Gmail SMTP (recommended for Cloud Run)"
    echo "  - Sign up at https://sendgrid.com"
    echo "  - Get API key"
    echo "  - Update MAIL_SERVER to smtp.sendgrid.net"
    echo "  - Update MAIL_USERNAME to 'apikey'"
    echo "  - Update MAIL_PASSWORD to your SendGrid API key"
    echo ""
    echo "Option 3: Check Cloud Run service account permissions"
    echo "  - Ensure service account has proper IAM roles"
    echo "  - Check firewall rules allow outbound SMTP (port 587)"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="

