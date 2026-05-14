@echo off
cd /d "%~dp0"

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)" >nul 2>&1
    if not errorlevel 1 (
        py -3 install.py %*
        goto :eof
    )
)

where python3 >nul 2>&1
if not errorlevel 1 (
    python3 -c "import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)" >nul 2>&1
    if not errorlevel 1 (
        python3 install.py %*
        goto :eof
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)" >nul 2>&1
    if not errorlevel 1 (
        python install.py %*
        goto :eof
    )
)

echo Error: Python 3 is required
exit /b 1
