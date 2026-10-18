@echo off
rem Starts the H2D-0 HD-2D prototype (Windows). Godot lookup: GODOT_EXE or tools\godot_path.txt (same as run_slice.bat).
rem   run_h2d0.bat          normal start
rem   run_h2d0.bat angle    force the ANGLE (Direct3D 11) OpenGL driver, for GPUs whose own OpenGL driver is too old
rem Keys: A/D steer, 1-7 weather, F1 quality, F2 3D/2D, F3 HUD, F4 colour transfer, F12 screenshot, B benchmark.
rem Everything Godot prints goes to build\h2d0_console.txt (shader errors would show up there).
rem Screenshots (F12) are copied to build\ when you close the window.
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
"%GODOT_EXE%" --path "%GAME%" %EXTRA% res://h2d/h2d0.tscn > "%HERE%..\build\h2d0_console.txt" 2>&1
set "CODE=%ERRORLEVEL%"
if exist "%UDIR%\h2d0_shot_*.png" copy /y "%UDIR%\h2d0_shot_*.png" "%HERE%..\build\" >nul
echo Godot exit code %CODE%. Console output: build\h2d0_console.txt
exit /b %CODE%
