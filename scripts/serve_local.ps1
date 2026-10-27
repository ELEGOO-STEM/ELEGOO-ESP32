param([int]$Port = 8123)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskDist = Join-Path $taskRoot 'dist'
$taskPython = (Get-Command python -ErrorAction Stop).Source
$taskBaseUrl = "http://127.0.0.1:$Port"
& $taskPython (Join-Path $PSScriptRoot 'build_package.py') --base-url $taskBaseUrl
if ($LASTEXITCODE -ne 0) { throw 'Package build failed.' }
Write-Host "Arduino IDE additional Boards Manager URL: $taskBaseUrl/package_elegoo_esp32c6_index.json"
Write-Host 'Keep this window open while installing. Ctrl+C stops the local server.'
& $taskPython -m http.server $Port --bind 127.0.0.1 --directory $taskDist
