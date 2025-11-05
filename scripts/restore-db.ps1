Param(
    [string]$ContainerName = "workhub-db",
    [string]$DatabaseName = "workhub",
    [string]$SaPassword = $env:SA_PASSWORD,
    [Parameter(Mandatory=$true)][string]$BackupPath
)

if ([string]::IsNullOrEmpty($SaPassword)) {
    Write-Error "SA_PASSWORD not set. Set it in .env or pass -SaPassword."
    exit 1
}

if (-not (Test-Path $BackupPath)) {
    Write-Error "Backup file not found: $BackupPath"
    exit 1
}

$containerPath = "/var/opt/mssql/data/restore.bak"

Write-Host "Copying backup into container..."
docker cp "$BackupPath" "$ContainerName:$containerPath"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$tsql = @"
ALTER DATABASE [$DatabaseName] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
RESTORE DATABASE [$DatabaseName] FROM DISK = '$containerPath' WITH REPLACE;
ALTER DATABASE [$DatabaseName] SET MULTI_USER;
"@

Write-Host "Restoring database..."
docker exec $ContainerName /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $SaPassword -C -Q $tsql

if ($LASTEXITCODE -ne 0) {
    Write-Error "Restore failed."
    exit $LASTEXITCODE
}

Write-Host "Restore completed."

