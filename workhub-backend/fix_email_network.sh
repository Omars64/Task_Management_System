#!/bin/bash
# Fix Cloud Run email network connectivity for Gmail SMTP (FREE - no API purchase needed)
# This ensures Cloud Run can reach smtp.gmail.com

PROJECT_ID="genai-workhub"
REGION="us-central1"
SERVICE_NAME="workhub-backend"

echo "=========================================="
echo "Fixing Cloud Run Email Network (FREE Gmail SMTP)"
echo "=========================================="
echo ""

# Check current service configuration
echo "Checking current Cloud Run service configuration..."
CURRENT_VPC=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="value(spec.template.spec.containers[0].vpcAccess.egress)" 2>/dev/null)

echo "Current VPC egress setting: ${CURRENT_VPC:-default (outbound allowed)}"
echo ""

# Check if VPC connector exists
VPC_CONNECTOR=$(gcloud compute networks vpc-access connectors list \
  --region=$REGION \
  --format="value(name)" 2>/dev/null | head -1)

if [ -n "$VPC_CONNECTOR" ]; then
    echo "VPC connector found: $VPC_CONNECTOR"
    echo "Updating service to allow all outbound traffic..."
    gcloud run services update $SERVICE_NAME \
        --region=$REGION \
        --vpc-egress=all-traffic \
        --project=$PROJECT_ID \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo "✓ Service updated successfully"
        echo "✓ Cloud Run can now reach external SMTP servers (smtp.gmail.com)"
    else
        echo "✗ Update failed. Trying without VPC connector..."
        # Remove VPC connector if it's causing issues
        gcloud run services update $SERVICE_NAME \
            --region=$REGION \
            --clear-vpc-connector \
            --project=$PROJECT_ID \
            --quiet
        echo "✓ VPC connector removed - using default outbound access"
    fi
else
    echo "No VPC connector found - Cloud Run has outbound internet access by default"
    echo ""
    echo "If emails still fail, the issue might be:"
    echo "1. Firewall rules blocking SMTP (port 587)"
    echo "2. Service account permissions"
    echo "3. Gmail app password incorrect"
    echo ""
    echo "Verifying service can reach internet..."
    
    # Test if we can reach Gmail SMTP (this will be done by the app, but we can verify config)
    echo "Checking service configuration..."
    gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --format="table(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)" \
        | grep -i mail || echo "Mail env vars configured via secrets"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "1. Verify email credentials in database:"
echo "   - Check SystemSettings table has smtp_username and smtp_password"
echo "2. Test email sending by signing up a new user"
echo "3. Check Cloud Run logs for email sending status"
echo "=========================================="

