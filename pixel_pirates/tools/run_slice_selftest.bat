@echo off
rem Scripted self-test of the E1 slice (Windows): steering, pause, chart, weather checkpoints, frame times, GPU info.
rem Takes about 40 seconds and opens a window. Same Godot lookup as run_slice.bat (GODOT_EXE or tools\godot_path.txt).
rem The report is written to the project's user folder; this script prints it and copies it to build\slice_selftest.txt.
setlocal
set "HERE=%~dp0"
set "GAME=%HERE%..\game"
if not defined GODOT_EXE if exist "%HERE%godot_path.txt" set /p GODOT_EXE=<"%HERE%godot_path.txt"
if not defined GODOT_EXE (
  echo Godot not found. Set GODOT_EXE or write its path into tools\godot_path.txt
  exit /b 2
)
if not exist "%HERE%..\build" mkdir "%HERE%..\build"
set "REPORT=%APPDATA%\Godot\app_userdata\Crown of the Seas\slice_selftest.txt"
if exist "%REPORT%" del "%REPORT%"
"%GODOT_EXE%" --path "%GAME%" res://ui/ocean_slice.tscn -- --selftest > "%HERE%..\build\slice_selftest_console.txt" 2>&1
set "CODE=%ERRORLEVEL%"
if exist "%REPORT%" (
  copy /y "%REPORT%" "%HERE%..\build\slice_selftest.txt" >nul
  type "%REPORT%"
) else (
  echo No report file was written: the scene probably failed before the test finished.
  echo Send build\slice_selftest_console.txt  ^(the Godot output^) instead.
)
echo.
echo Godot exit code %CODE%  ^(0 = all checks passed^)
exit /b %CODE%
