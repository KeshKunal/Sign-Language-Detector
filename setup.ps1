param([switch]$SkipDatasetValidation)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Write-Host 'MediSign local setup' -ForegroundColor Cyan

$pythonCommand = $null
$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pythonLauncher) {
  try { $pythonCommand = (& py -3.11 -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1) }
  catch { $pythonCommand = $null }
}
if (-not $pythonCommand) {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $pythonVersion = (& $python.Source --version 2>&1 | Select-Object -Last 1)
    if ($pythonVersion -match '^Python 3\.11\.') { $pythonCommand = $python.Source }
  }
}
if (-not $pythonCommand) {
  $detectedVersion = 'no Python command'
  try { $detectedVersion = (& python --version 2>&1 | Select-Object -Last 1) } catch {}
  throw "Python 3.11 is required for TensorFlow compatibility, but it was not found. Detected: $detectedVersion. Install Python 3.11 from python.org, ensure the Python launcher is enabled, and rerun setup."
}
Write-Host "Python: $(& $pythonCommand --version)"
$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) { throw 'Node.js 20 or newer and npm are required. Install Node.js and rerun setup.' }
Write-Host "Node: $(& node --version)   npm: $(& npm --version)"

$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) { & $pythonCommand -m venv (Join-Path $projectRoot '.venv') }
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not upgrade pip.' }
& $venvPython -m pip install -r (Join-Path $projectRoot 'backend\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependencies did not install. Review the error above and check your internet connection.' }

Push-Location (Join-Path $projectRoot 'frontend')
try { & npm install; if ($LASTEXITCODE -ne 0) { throw 'Frontend dependencies did not install.' } }
finally { Pop-Location }

if (-not $SkipDatasetValidation) {
  & $venvPython -m ml.preprocessing.validate_dataset
  if ($LASTEXITCODE -ne 0) { throw 'Dataset validation failed. See the reported frame or shape error.' }
}
$model = Join-Path $projectRoot 'models\sign_language_model.keras'
if (Test-Path $model) { Write-Host "Model checkpoint found: $model" -ForegroundColor Green }
else { Write-Host 'No trained model checkpoint found. The application can open, but recognition requires training.' -ForegroundColor Yellow }
Write-Host "`nSetup complete. Start the application with: .\run.ps1" -ForegroundColor Green
