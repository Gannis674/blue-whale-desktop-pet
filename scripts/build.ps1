$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
python -m PyInstaller --noconfirm --clean blue_whale_pet.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Built: dist/BlueWhalePet.exe'
