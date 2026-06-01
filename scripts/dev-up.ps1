$ErrorActionPreference = "Stop"

$PORT = 7530
$IMAGE = "cognitor:$(Get-Date -Format 'yyyy-MM-dd-HH-mm')"

$LOG_DIR = ".\logs"
$LOG_FILE = "$LOG_DIR\cognitor.log"

# Ensure logs directory exists
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

# Clean up Docker stuff
docker image prune -f
docker container prune -f

# Build image
docker build -t $IMAGE .

# Stop and remove existing container if it exists
$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq "cognitor" }

if ($existing) {
    docker stop cognitor | Out-Null
    docker rm cognitor | Out-Null
    Write-Host "Stopped and removed existing 'cognitor' container."
}

# Resolve current path for volume mount
$pwd = (Get-Location).Path

# Run container
docker run -d `
  --env-file ./.env `
  -e PYTHONPATH=/app `
  -v "${pwd}/src:/app/src" `
  -v cognitor_storage:/app/storage `
  --name cognitor `
  -p "$PORT`:$PORT" `
  --restart unless-stopped `
  $IMAGE `
  uvicorn src.server.app:app --host 0.0.0.0 --port $PORT --reload

Write-Host "Container started. Tailing logs into $LOG_FILE..."

# Start log tailing in background
Start-Job -ScriptBlock {
    param($logFile)
    docker logs -f cognitor *>> $logFile
} -ArgumentList $LOG_FILE | Out-Null

Write-Host ""
Write-Host "Cognitor development container is running on port $PORT."
Write-Host "- Visit docs at http://localhost:$PORT/docs"
Write-Host "- Logs are being written to $LOG_FILE"