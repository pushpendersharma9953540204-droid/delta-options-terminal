@echo off
title Today's Delta Exchange Strike Signals
color 0E
cls

echo ===============================================================================
echo                DELTA EXCHANGE -- TODAY'S STRIKE SIGNALS
echo.
echo    Fetching live Bitcoin price and 2-day option chain...
echo    Calculates ATM Straddle * 2.5 and outputs tonight's strikes to sell.
echo ===============================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto NoPython

python "%~dp0todays_strikes.py"

echo.
echo ===============================================================================
echo [SUCCESS] Full trade ticket saved to:
echo "%~dp0todays_trade_ticket.txt"
echo ===============================================================================
echo.

set /p OPEN_TICKET="Would you like to open this trade ticket in Notepad? (Y/N, default Y): "
if "%OPEN_TICKET%"=="" set OPEN_TICKET=Y
if /I "%OPEN_TICKET%"=="Y" (
    start notepad.exe "%~dp0todays_trade_ticket.txt"
)

echo.
echo Press any key to exit...
pause >nul
goto :eof

:NoPython
color 0C
echo [ERROR] Python was not detected in your system PATH.
echo.
pause
exit /b 1
