@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   Agentic Bootstrapper IDE - Portable Build
echo   This will install missing deps and build ai_ide.exe
echo ============================================================
echo.

REM --- 1/6  Locate a Python interpreter ---
set "PYTHON_EXE="
for %%P in (python.exe python3.exe) do (
    if not defined PYTHON_EXE (
        where %%P >nul 2>&1 && set "PYTHON_EXE=%%P"
    )
)
if not defined PYTHON_EXE (
    py -3 --version >nul 2>&1 && set "PYTHON_EXE=py -3"
)
if not defined PYTHON_EXE (
    echo ERROR: Python not found on PATH.
    echo.
    echo Install Python 3.9+ from https://www.python.org/downloads/
    echo IMPORTANT: tick "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo Using: !PYTHON_EXE!
!PYTHON_EXE! --version
echo.

REM --- 2/6  Verify Python >= 3.9 ---
!PYTHON_EXE! -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.9 or newer required.
    pause
    exit /b 1
)

REM --- 3/6  Install missing dependencies ---
echo === Checking dependencies ===
!PYTHON_EXE! -c "import PyQt6" >nul 2>&1 || (
    echo Installing PyQt6...
    !PYTHON_EXE! -m pip install PyQt6
)
!PYTHON_EXE! -c "import psutil" >nul 2>&1 || (
    echo Installing psutil...
    !PYTHON_EXE! -m pip install psutil
)
!PYTHON_EXE! -c "import llama_cpp" >nul 2>&1 || (
    echo Installing llama-cpp-python CPU wheel...
    !PYTHON_EXE! -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
)
!PYTHON_EXE! -c "import PyInstaller" >nul 2>&1 || (
    echo Installing PyInstaller...
    !PYTHON_EXE! -m pip install pyinstaller
)

REM --- 4/6  Check model file ---
echo.
echo === Checking model ===
set "MODEL_MISSING="
if not exist "model\qwen2.5-coder-1.5b-instruct-q4_k_m.gguf" (
    set "MODEL_MISSING=1"
    echo WARNING: model file not found at:
    echo   !CD!\model\qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
    echo.
    echo The exe will still build, but chat stays disabled until you add the model.
    echo Download the GGUF from Hugging Face: Qwen2.5-Coder-1.5B-Instruct, Q4_K_M
    echo and drop it into the model\ folder, then rebuild.
    echo.
) else (
    echo Model file found.
)

REM --- 5/6  Build ---
echo.
echo === Building exe (3-6 min) ===
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
!PYTHON_EXE! -m PyInstaller --clean --noconfirm --windowed --name ai_ide ^
    --hidden-import psutil ^
    --hidden-import llama_cpp ^
    --collect-all llama_cpp ^
    ai_ide.py
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Scroll up for the first error.
    pause
    exit /b 1
)

REM --- 6/6  Copy model next to the exe ---
echo.
echo === Copying model ===
if exist "model" (
    if not exist "dist\ai_ide\model" mkdir "dist\ai_ide\model"
    xcopy /E /I /Y "model" "dist\ai_ide\model" >nul
    echo Model copied to dist\ai_ide\model
) else (
    echo Skipped - no model\ folder to copy.
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo   Launch:  dist\ai_ide\ai_ide.exe
echo ============================================================
if defined MODEL_MISSING (
    echo.
    echo NOTE: model was missing. Copy your GGUF into
    echo       dist\ai_ide\model\ after downloading it.
)
echo.
pause