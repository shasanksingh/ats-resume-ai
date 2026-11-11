param(
    [string]$NodePath = 'D:\NodeJS\node-v22.23.2-win-x64\node.exe',
    [string]$PythonPath = (Join-Path $PSScriptRoot '..\.local\venv\Scripts\python.exe')
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtimeRoot = Join-Path $projectRoot '.local'
foreach ($path in @($projectRoot, $NodePath, $PythonPath)) {
    if ([IO.Path]::GetFullPath($path) -notlike 'D:\*') {
        throw 'The project and runtimes must be on D:.'
    }
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing path: $path" }
}

$env:Path = (Split-Path $NodePath) + ';' + $env:Path
$env:TEMP = Join-Path $runtimeRoot 'tmp'
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $runtimeRoot 'pip-cache'
$env:npm_config_cache = Join-Path $runtimeRoot 'npm-cache'
$env:npm_config_prefix = Join-Path $runtimeRoot 'npm-global'
$env:HF_HOME = Join-Path $runtimeRoot 'huggingface'
$env:TORCH_HOME = Join-Path $runtimeRoot 'torch'
$env:XDG_CACHE_HOME = Join-Path $runtimeRoot 'cache'
$env:TECTONIC_CACHE_DIR = Join-Path $runtimeRoot 'tectonic-cache'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $runtimeRoot 'browsers'
$env:PYTHONNOUSERSITE = '1'
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:BACKEND_URL = 'http://127.0.0.1:8000'
foreach ($path in @($env:TEMP, $env:HF_HOME, $env:TORCH_HOME, $env:XDG_CACHE_HOME)) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

foreach ($service in @(
    @{ Name = 'backend'; Port = 8000; File = $PythonPath; Args = '-m uvicorn app.main:app --host 127.0.0.1 --port 8000' },
    @{ Name = 'frontend'; Port = 3000; File = $NodePath; Args = '--max-old-space-size=2048 node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3000' }
)) {
    if (Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue) {
        Write-Output "$($service.Name): port $($service.Port) is already in use; leaving the existing process running."
        continue
    }
    $process = Start-Process -FilePath $service.File -ArgumentList $service.Args `
        -WorkingDirectory (Join-Path $projectRoot $service.Name) -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $runtimeRoot "$($service.Name).log") `
        -RedirectStandardError (Join-Path $runtimeRoot "$($service.Name).err.log")
    $process.Id | Set-Content -LiteralPath (Join-Path $runtimeRoot "$($service.Name).pid")
    Write-Output "$($service.Name): started process $($process.Id)"
}
Write-Output 'UI: http://127.0.0.1:3000 | API: http://127.0.0.1:8000/docs'
Write-Output "Logs and caches: $runtimeRoot"
