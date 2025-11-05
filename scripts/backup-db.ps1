Param(
    [string]$ContainerName = "workhub-db",
    [string]$DatabaseName = "workhub",
    [string]$SaPassword = $env:SA_PASSWORD,
    [string]$OutFile = (Join-Path (Get-Location) ("backup-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".bak"))
)

if ([string]::IsNullOrEmpty($SaPassword)) {
    Write-Error "SA_PASSWORD not set. Set it in .env or pass -SaPassword."
    exit 1
}

$containerPath = "/var/opt/mssql/data/workhub-backup.bak"

Write-Host "Creating backup inside container $ContainerName ..."
docker exec $ContainerName /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $SaPassword -C -Q "BACKUP DATABASE [$DatabaseName] TO DISK = '$containerPath' WITH INIT" | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backup command failed inside container."
    exit $LASTEXITCODE
}

Write-Host "Copying backup to host: $OutFile"
docker cp "$ContainerName:$containerPath" "$OutFile"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to copy backup to host."
    exit $LASTEXITCODE
}

Write-Host "Backup completed: $OutFile"

