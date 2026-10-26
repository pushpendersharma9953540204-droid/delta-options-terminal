@echo off
title Delta Options Public Web Terminal
color 0A
cls

echo ===============================================================================
echo            DELTA EXCHANGE OPTIONS TERMINAL -- PUBLIC WEB LAUNCHER
echo ===============================================================================
echo.
echo   Starting local Streamlit server and generating secure public HTTPS website...
echo   No credit card, no payment, no setup needed.
echo ===============================================================================
echo.

:: Start Streamlit in background if not already running
netstat -ano | findstr :8501 >nul
if errorlevel 1 (
    echo [1/2] Starting Streamlit server...
    start /B python -m streamlit run app.py --server.headless true --server.port 8501 >nul 2>&1
    timeout /t 3 /nobreak >nul
) else (
    echo [1/2] Streamlit is already running on port 8501.
)

echo [2/2] Connecting Cloudflare secure public tunnel...
echo.
cloudflared tunnel --url http://localhost:8501
