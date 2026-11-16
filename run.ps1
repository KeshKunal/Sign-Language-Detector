$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$vite = Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js'
if (-not (Test-Path $python) -or -not (Test-Path $vite)) { throw 'Dependencies are missing. Run .\setup.ps1 first.' }
$logs = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$previousModel = $env:MEDISIGN_MODEL
$svmCandidate = Join-Path $projectRoot 'ml\models\sign_language_svm_candidate.joblib'
if ((Test-Path $svmCandidate) -and [string]::IsNullOrWhiteSpace($env:MEDISIGN_MODEL)) { $env:MEDISIGN_MODEL = $svmCandidate }
$backend = $null; $frontend = $null
try {
  $backend = Start-Process -FilePath $python -ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'backend.log') -RedirectStandardError (Join-Path $logs 'backend-error.log')
  $viteArguments = '"' + $vite + '" --host 127.0.0.1 --port 5173 --strictPort'
  $frontend = Start-Process -FilePath 'node.exe' -ArgumentList $viteArguments -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'frontend.log') -RedirectStandardError (Join-Path $logs 'frontend-error.log')
  $ready = $false
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if ($backend.HasExited -or $frontend.HasExited) { throw 'A service exited during startup. Review logs/backend-error.log and logs/frontend-error.log.' }
    try { Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2 | Out-Null; $ready = $true; break } catch { Start-Sleep -Seconds 1 }
  }
  if (-not $ready) { throw 'Frontend did not become ready. Review logs/frontend-error.log.' }
  Write-Host "MediSign is running at http://127.0.0.1:5173" -ForegroundColor Green
  Write-Host 'Press Enter to stop both services.'
  Start-Process 'http://127.0.0.1:5173'
  [void](Read-Host)
} finally {
  foreach ($process in @($frontend, $backend)) { if ($null -ne $process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue } }
  if ($null -eq $previousModel) { Remove-Item Env:MEDISIGN_MODEL -ErrorAction SilentlyContinue } else { $env:MEDISIGN_MODEL = $previousModel }
  Write-Host 'MediSign services stopped.'
}
