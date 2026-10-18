@echo off
rem Runs the in-engine tests (Module A7). Windows. No Python needed.
rem Tell it where Godot is, ONE of:
rem   1) set GODOT_EXE=C:\path\Godot_v4.7.2-stable_win64_console.exe
rem   2) put that path alone on one line in tools\godot_path.txt
setlocal
set "HERE=%~dp0"
set "GAME=%HERE%..\game"
if not defined GODOT_EXE if exist "%HERE%godot_path.txt" set /p GODOT_EXE=<"%HERE%godot_path.txt"
if not defined GODOT_EXE (
  echo Godot not found. Set GODOT_EXE or write its path into tools\godot_path.txt
  exit /b 2
)
if not exist "%HERE%..\build" mkdir "%HERE%..\build"
set "OUT=%HERE%..\build\godot_tests.txt"
echo Importing project...
"%GODOT_EXE%" --headless --path "%GAME%" --import > "%OUT%" 2>&1
echo Running tests...
"%GODOT_EXE%" --headless --path "%GAME%" --script res://tests/run_all.gd >> "%OUT%" 2>&1
type "%OUT%"
findstr /C:"SCRIPT ERROR" /C:"Parse Error" "%OUT%" >nul && (echo. & echo ENGINE ERRORS FOUND - see build\godot_tests.txt & exit /b 1)
findstr /R /C:"TESTS: .* checks, 0 failed" "%OUT%" >nul && (echo. & echo ALL TESTS PASSED & exit /b 0)
echo.
echo TESTS FAILED OR DID NOT FINISH - see build\godot_tests.txt
exit /b 1
