@echo off
title Delta Exchange Live Market Scanner
color 0E
cls

echo ===============================================================================
echo                DELTA EXCHANGE LIVE MARKET SCANNER
echo.
echo    Fetches live BTC price, 2-day option chain, and ATM Straddle.
echo    Calculates Straddle * 2.5 strikes and evaluates live order books.
echo ===============================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto NoPython

echo [*] Connecting to Delta Exchange API...
echo.

python "%~dp0check_live_delta.py"

echo.
echo ===============================================================================
echo [SUCCESS] Live evaluation completed!
echo A detailed copy was saved to:
echo "%~dp0live_trade_plan.txt"
echo ===============================================================================
echo.

set /p OPEN_TXT="Would you like to open the live trade plan in Notepad? (Y/N, default Y): "
if "%OPEN_TXT%"=="" set OPEN_TXT=Y
if /I "%OPEN_TXT%"=="Y" (
    start notepad.exe "%~dp0live_trade_plan.txt"
)

echo.
echo Press any key to exit this window...
pause >nul
goto :eof

:NoPython
color 0C
echo [ERROR] Python was not detected in your system PATH.
echo.
pause
exit /b 1
