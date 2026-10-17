param([int]$Port = 18000)
$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot
$demoDir = Join-Path $repoDir '.local-demo'
$tokenFile = Join-Path $demoDir 'proxy-token.txt'
if (-not (Test-Path -LiteralPath $tokenFile)) {
    throw 'Create the private .local-demo/proxy-token.txt and set the matching DEMO_PROXY_TOKEN secret on Vercel first.'
}
$env:DATA_DIR = Join-Path $demoDir 'data'
$env:DATABASE_PATH = Join-Path $env:DATA_DIR 'book2course.db'
$env:DEMO_PROXY_TOKEN_FILE = $tokenFile
$env:COOKIE_SECURE = 'true'
$env:ALLOWED_ORIGINS = 'https://4next-study.vercel.app,http://localhost:3100,http://127.0.0.1:3100'
Set-Location (Join-Path $repoDir 'backend')
& '.\.venv\Scripts\python.exe' -m uvicorn app.demo_gateway:create_demo_app --factory --host 127.0.0.1 --port $Port
