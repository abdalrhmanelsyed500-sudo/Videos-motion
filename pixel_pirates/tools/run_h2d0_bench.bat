@echo off
rem H2D-0 benchmark for the user's PC (Windows). Takes about 80 seconds and opens a window: do not touch anything.
rem   run_h2d0_bench.bat          normal start
rem   run_h2d0_bench.bat angle    force the ANGLE (Direct3D 11) OpenGL driver
rem Output (copied to build\): h2d0_bench.txt (the numbers), h2d0_bench_01.png ... (one screenshot per phase),
rem h2d0_console.txt (everything Godot printed). Send these files.
setlocal
set "HERE=%~dp0"
set "GAME=%HERE%..\game"
if not defined GODOT_EXE if exist "%HERE%godot_path.txt" set /p GODOT_EXE=<"%HERE%godot_path.txt"
if not defined GODOT_EXE (
  echo Godot not found. Set GODOT_EXE or write its path into tools\godot_path.txt
  exit /b 2
)
if not exist "%HERE%..\build" mkdir "%HERE%..\build"
set "EXTRA="
if /i "%~1"=="angle" set "EXTRA=--rendering-driver opengl3_angle"
set "UDIR=%APPDATA%\Godot\app_userdata\Crown of the Seas"
if exist "%UDIR%\h2d0_bench.txt" del "%UDIR%\h2d0_bench.txt"
if exist "%UDIR%\h2d0_bench_*.png" del "%UDIR%\h2d0_bench_*.png"
"%GODOT_EXE%" --path "%GAME%" %EXTRA% res://h2d/h2d0.tscn -- --bench > "%HERE%..\build\h2d0_console.txt" 2>&1
set "CODE=%ERRORLEVEL%"
if exist "%UDIR%\h2d0_bench_*.png" copy /y "%UDIR%\h2d0_bench_*.png" "%HERE%..\build\" >nul
if exist "%UDIR%\h2d0_bench.txt" (
  copy /y "%UDIR%\h2d0_bench.txt" "%HERE%..\build\h2d0_bench.txt" >nul
  type "%UDIR%\h2d0_bench.txt"
) else (
  echo No benchmark file was written: the scene probably failed before it finished.
  echo Send build\h2d0_console.txt  ^(the Godot output^) instead.
)
echo.
echo Godot exit code %CODE%
exit /b %CODE%
