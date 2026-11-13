param([switch]$SkipDatasetValidation)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Write-Host 'MediSign local setup' -ForegroundColor Cyan

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if (-not $pythonLauncher) { throw 'Python launcher (py.exe) is required. Install Python 3.11 from python.org.' }
& py -3.11 --version
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 was not found. Install Python 3.11 and rerun setup.' }
$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) { throw 'Node.js 20 or newer and npm are required. Install Node.js and rerun setup.' }
Write-Host "Node: $(& node --version)   npm: $(& npm --version)"

$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) { & py -3.11 -m venv (Join-Path $projectRoot '.venv') }
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
