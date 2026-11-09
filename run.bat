@echo off
setlocal

set PYTHON_BIN=C:\Users\Asus\AppData\Local\Programs\Python\Python312\python.exe
if exist "%PYTHON_BIN%" goto have_python

set PYTHON_BIN=python
where python >nul 2>&1
if %ERRORLEVEL% equ 0 goto have_python

set PYTHON_BIN=py
where py >nul 2>&1
if %ERRORLEVEL% equ 0 goto have_python

echo Error: Python interpreter was not found.
pause
exit /b 1

:have_python
if "%~1"=="test" goto run_tests
if not "%~1"=="" goto run_args

"%PYTHON_BIN%" -m src.main --config config.json
echo.
echo -------------------------------------------------------------
echo Stage 5 execution completed.
echo To run specific stages from command prompt:
echo   run.bat --stage 1
echo   run.bat --stage 2
echo   run.bat --stage 3
echo   run.bat --stage 4
echo   run.bat --stage 5 --demo
echo   run.bat test
echo -------------------------------------------------------------
pause
goto :eof

:run_tests
"%PYTHON_BIN%" -m unittest discover -s tests -p "test_*.py" -v
goto :eof

:run_args
"%PYTHON_BIN%" -m src.main %*
goto :eof
