# Enforce Private IP for Database Connection

## Overview

The application is configured to **ONLY use private IP (10.119.176.3)** for database connections in production. This ensures:
- ✅ **Optimal Performance** - Private IP is faster than public IP
- ✅ **Better Security** - Traffic stays within GCP network
- ✅ **Lower Latency** - Direct connection without internet routing

## Configuration

### Private IP Address
- **Private IP**: `10.119.176.3` ✅ (Use this)
- **Public IP**: `34.31.203.11` ❌ (Blocked in production)

### Automatic Enforcement

The application automatically:
1. **Blocks public IP in production** - Raises error if public IP is detected
2. **Auto-switches in development** - Warns and switches to private IP
3. **Validates on startup** - Logs which IP is being used

## Deployment Configuration

### GitHub Actions (`.github/workflows/deploy-gcp.yml`)
✅ Already configured with private IP:
```yaml
--set-env-vars DB_HOST=10.119.176.3,DB_PORT=1433,...
```

### Cloud Build (`cloudbuild.yaml`)
✅ Already configured with private IP:
```yaml
--set-env-vars=...,DB_HOST=10.119.176.3,DB_PORT=1433,...
```

### Manual Deployment Script (`scripts/deploy-gcp.sh`)
✅ Updated to enforce private IP:
```bash
--set-env-vars ...,DB_HOST=10.119.176.3,DB_PORT=1433,...
```

## Verification

### Check Current Configuration

Run the diagnostic script:
```bash
cd workhub-backend
python check_db_connection.py
```

### Check Cloud Run Environment Variables

```bash
gcloud run services describe workhub-backend \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

Look for:
- `DB_HOST=10.119.176.3` ✅ (Correct)
- `DB_HOST=34.31.203.11` ❌ (Wrong - will be blocked)

### Check Application Logs

The application logs which IP is being used:
- `[INFO] Using PRIVATE IP: 10.119.176.3` ✅
- `ERROR: Public IP detected in production` ❌

## Troubleshooting

### If Application Fails to Start

**Error**: `Public IP cannot be used in production`

**Solution**: Update Cloud Run environment variable:
```bash
gcloud run services update workhub-backend \
  --region us-central1 \
  --update-env-vars DB_HOST=10.119.176.3
```

### If Still Using Public IP

1. Check GitHub Secrets:
   - Go to: https://github.com/Omars64/Task_Management_System/settings/secrets/actions
   - Verify `DB_HOST` secret is set to `10.119.176.3`

2. Update Cloud Run directly:
   ```bash
   gcloud run services update workhub-backend \
     --region us-central1 \
     --update-env-vars DB_HOST=10.119.176.3
   ```

3. Redeploy:
   ```bash
   git push origin main
   ```

## Best Practices

1. ✅ **Always use private IP in production** (`10.119.176.3`)
2. ✅ **Never commit public IP** to version control
3. ✅ **Use environment variables** for database configuration
4. ✅ **Verify on deployment** using diagnostic script
5. ✅ **Monitor application logs** for IP usage warnings

## Performance Impact

- **Private IP**: ~1-5ms latency, optimal performance ✅
- **Public IP**: ~50-200ms latency, slow performance ❌

Using private IP can improve response times by **10-40x** for database queries.

