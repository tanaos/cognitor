$ErrorActionPreference = "Stop"

$CONTAINER_NAME = "cognitor"
$LOG_FILE = ".\logs\cognitor.log"

Write-Host "Stopping Cognitor dev container..."

# Check if container is running
$running = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $CONTAINER_NAME }

if ($running) {
    docker stop $CONTAINER_NAME | Out-Null
    Write-Host "Stopped running container: $CONTAINER_NAME"
} else {
    Write-Host "No running container found: $CONTAINER_NAME"
}

# Check if container exists (stopped or running)
$exists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $CONTAINER_NAME }

if ($exists) {
    docker rm $CONTAINER_NAME | Out-Null
    Write-Host "Removed container: $CONTAINER_NAME"
} else {
    Write-Host "No container to remove: $CONTAINER_NAME"
}

# Kill background docker logs tail if it exists
$logJobs = Get-Job | Where-Object {
    $_.Command -like "*docker logs -f $CONTAINER_NAME*"
}

if ($logJobs) {
    $logJobs | Stop-Job | Out-Null
    $logJobs | Remove-Job | Out-Null
    Write-Host "Stopped log tail process."
}

Write-Host ""
Write-Host "Dev environment shut down cleanly."
Write-Host "Logs preserved at: $LOG_FILE"