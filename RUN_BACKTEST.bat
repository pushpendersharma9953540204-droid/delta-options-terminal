@echo off
title Delta Exchange Options Strategy Backtester
color 0B
cls

echo ===============================================================================
echo                DELTA EXCHANGE BTC OPTIONS BACKTESTER
echo.
echo    Strategy:  Short Strangle - Sell 1 CE + Sell 1 PE
echo    Expiry:    2-Day Expiry - 17:30 IST Settlement
echo    Formula:   ATM Straddle * 2.5 Strike Offset
echo    Stop-Loss: 200%% Premium Loss - 3x Entry Price
echo ===============================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 goto NoPython

echo [*] Starting backtest on historical trade data...
echo.

:: Run the backtest script
python "%~dp0run_backtest.py"

echo.
echo ===============================================================================
echo [SUCCESS] Backtest completed!
echo A detailed copy of this report was saved to:
echo "%~dp0backtest_report.txt"
echo ===============================================================================
echo.

:: Offer to open the report in Notepad
set /p OPEN_TXT="Would you like to open the report in Notepad? (Y/N, default Y): "
if "%OPEN_TXT%"=="" set OPEN_TXT=Y
if /I "%OPEN_TXT%"=="Y" (
    start notepad.exe "%~dp0backtest_report.txt"
)

echo.
echo Press any key to exit this window...
pause >nul
goto :eof

:NoPython
color 0C
echo [ERROR] Python was not detected in your system PATH.
echo Please make sure Python is installed and added to your environment variables.
echo.
pause
exit /b 1
