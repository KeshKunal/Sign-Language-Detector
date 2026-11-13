param([string[]]$TrainingArgs = @())
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Python environment not found. Run .\setup.ps1 first.' }
& $python -m ml.training.train @TrainingArgs
if ($LASTEXITCODE -ne 0) { throw 'Training did not complete. Review the error above.' }
