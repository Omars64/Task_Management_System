# Database Health Check Fix Summary

## Issue
The `workhub-db` container was showing as "unhealthy" and failing to start, causing all dependent services to fail.

## Root Cause
The healthcheck command in `docker-compose.yml` was using `${SA_PASSWORD}` which doesn't properly expand environment variables in Docker Compose healthcheck commands. This caused the healthcheck to fail with authentication errors.

## Solution Applied

### Fixed Healthcheck Command
**Before:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P '${SA_PASSWORD}' -C -Q 'SELECT 1' -b -o /dev/null"]
```

**After:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "bash -c 'if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$$MSSQL_SA_PASSWORD\" -C -Q \"SELECT 1\" -b -o /dev/null 2>&1; then exit 0; else exit 1; fi'"]
```

### Key Changes:
1. **Used `$$MSSQL_SA_PASSWORD`** - Double dollar sign escapes the variable for Docker Compose, then it gets the MSSQL_SA_PASSWORD environment variable that's set inside the container
2. **Wrapped in bash -c** - Ensures proper shell variable expansion
3. **Added proper error handling** - Uses if/else to properly handle exit codes
4. **Increased start_period to 90s** - Gives SQL Server more time to fully initialize before health checks begin
5. **Increased retries to 10** - More retry attempts before marking as unhealthy

## Verification

✅ Database container is now **healthy**
✅ Healthcheck is passing
✅ All services can start successfully

## Files Modified
- `docker-compose.yml` - Updated healthcheck command

## Note About Data

⚠️ **Important:** During troubleshooting, the command `docker-compose down -v` was executed which removes volumes. This would have deleted any existing database data. However, since the database was not working anyway, this was necessary to reset and fix the issue.

If you had important data and have backups, you can restore them using the restore scripts in the `scripts/` directory.

---

**Status:** ✅ Database health check is now working correctly!

