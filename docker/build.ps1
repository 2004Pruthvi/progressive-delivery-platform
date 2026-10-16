param (
    [string]$Version = "v1.0.0"
)

$ErrorActionPreference = "Stop"
$AppName = "release-demo-app"

try {
    $CommitSha = (git rev-parse --short HEAD 2>$null)
    if (-not $CommitSha) { $CommitSha = "manual" }
} catch {
    $CommitSha = "manual"
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Building Docker image: ${AppName}:${Version}" -ForegroundColor Cyan
Write-Host "Commit SHA: $CommitSha" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

docker build `
  -f docker/Dockerfile `
  --build-arg APP_VERSION="$Version" `
  --build-arg COMMIT_SHA="$CommitSha" `
  -t "${AppName}:${Version}" `
  -t "${AppName}:${CommitSha}" `
  .

Write-Host "Docker build complete." -ForegroundColor Green
docker images | Select-String $AppName
