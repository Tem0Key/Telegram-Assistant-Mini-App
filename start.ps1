$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env. Fill BOT_TOKEN, GEMINI_API_KEY and OAuth settings, then run start.ps1 again." -ForegroundColor Yellow
    exit 1
}

& .\.venv\Scripts\python.exe main.py
