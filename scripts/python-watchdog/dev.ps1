<#
PowerShell dev launcher (Windows)
- Ensures Python watchdog is installed (user site)
- Runs the converter once
- Starts the watcher in a background process
- Launches `bundle exec jekyll serve --livereload`
#>

# Change to repo root (script is in ./scripts)
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)\..

Write-Host "Ensuring watchdog is available..."
python -c "import importlib.util; exit(0) if importlib.util.find_spec('watchdog') else exit(1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing watchdog (user site)..."
    python -m pip install --user watchdog
}

Write-Host "Running converter once..."
python scripts\obsidian_to_jekyll.py
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Converter exited with non-zero code. Check output above."
}

Write-Host "Starting watcher in background..."
$watchArgs = 'scripts\python-watchdog\watch_and_build.py -v .\absurdly-goud-obsidian -c scripts\obsidian_to_jekyll.py'
Start-Process -FilePath (Get-Command python).Source -ArgumentList $watchArgs -WindowStyle Hidden

Write-Host "Starting Jekyll server (foreground). Ctrl+C to stop both server+watcher."
# If you use bundler, this will call the project's Gemfile. Adjust as needed.
& bundle exec jekyll serve --source site_src --config _config.yml --destination site --livereload
