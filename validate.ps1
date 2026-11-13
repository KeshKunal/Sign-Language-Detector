$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Python environment not found. Run .\setup.ps1 first.' }
& $python -m ml.preprocessing.validate_dataset
if ($LASTEXITCODE -ne 0) { throw 'Dataset validation failed.' }
Push-Location (Join-Path $projectRoot 'frontend')
try { & npm run build; if ($LASTEXITCODE -ne 0) { throw 'Frontend production build failed.' } }
finally { Pop-Location }
Write-Host 'Dataset and frontend validation completed.' -ForegroundColor Green
