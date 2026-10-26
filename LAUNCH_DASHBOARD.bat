@echo off
title Delta Exchange Graphical Dashboard
color 0A
cls

echo ===============================================================================
echo                DELTA EXCHANGE DAILY EXECUTION DASHBOARD
echo.
echo    Launching interactive visual dashboard in your browser...
echo    - Today's Live Decision (Sell CE, PE, or Both at 10:00 PM IST)
echo    - Locked 10:00 PM Candle Data (in $ USD, Fixed Without Live Drift)
echo    - 4-Step Mechanical Flowchart Audit & Exact Executable Orders
echo ===============================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto NoPython

echo [*] Starting Streamlit server...
echo.
echo Please wait, your browser will open automatically in a few seconds...
echo (Keep this window open while using the dashboard)
echo.

python -m streamlit run "%~dp0app.py" --server.headless=false --browser.gatherUsageStats=false

pause
goto :eof

:NoPython
color 0C
echo [ERROR] Python was not detected in your system PATH.
echo.
pause
exit /b 1
