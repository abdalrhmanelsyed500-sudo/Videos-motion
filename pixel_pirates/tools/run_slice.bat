@echo off
rem Starts the E1 ocean slice "The Three Weathers" (Windows). Same Godot lookup as run_godot_tests.bat.
rem   1) set GODOT_EXE=C:\path\Godot_v4.7.2-stable_win64.exe   (the NON-console exe is fine)
rem   2) or put that path alone on one line in tools\godot_path.txt
rem Keys: A/D steer, P pause, M chart, 1-7 debug jump to a checkpoint, N reveal chart (debug), ` console.
setlocal
set "HERE=%~dp0"
set "GAME=%HERE%..\game"
if not defined GODOT_EXE if exist "%HERE%godot_path.txt" set /p GODOT_EXE=<"%HERE%godot_path.txt"
if not defined GODOT_EXE (
  echo Godot not found. Set GODOT_EXE or write its path into tools\godot_path.txt
  exit /b 2
)
"%GODOT_EXE%" --path "%GAME%" res://ui/ocean_slice.tscn
