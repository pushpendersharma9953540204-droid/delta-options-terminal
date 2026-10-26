@echo off
title Delta Exchange Historical Data Syncer
color 0B
cls

echo ===============================================================================
echo            DELTA EXCHANGE HISTORICAL CANDLE DATA SYNCER
echo.
echo    Connects to Delta Exchange API using your authenticated credentials.
echo    Fetches 8,760+ real hourly candles (last 365 days).
echo    Simulates 2-Day Strangle (Straddle * 2.5) with Strike Substitution.
echo ===============================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto NoPython

echo [*] Downloading historical candles directly from Delta Exchange API...
echo.

python -c "from delta_historical import DeltaHistoricalEngine; eng = DeltaHistoricalEngine(); eng.sync_and_save(days=365, output_csv='delta_api_synced_trades.csv')"

echo.
echo ===============================================================================
echo [SUCCESS] Historical sync complete!
echo Saved real Delta Exchange trades to: delta_api_synced_trades.csv
echo You can now view these trades in your Graphical Dashboard!
echo ===============================================================================
echo.

pause
goto :eof

:NoPython
color 0C
echo [ERROR] Python was not detected in your system PATH.
echo.
pause
exit /b 1
