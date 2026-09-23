@echo off
rem Copy the project to the Pi over SSH.  Usage:  deploy [user@host]
rem The first time, also run on the Pi:  bash ~/clock/pi/install.sh
setlocal
set TARGET=%1
if "%TARGET%"=="" set TARGET=pi@clock.local
for /d /r %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"
ssh %TARGET% "mkdir -p clock"
scp -r clock assets tools pi config.default.json run.py requirements.txt README.md %TARGET%:clock/
if errorlevel 1 (echo Copy failed. & exit /b 1)
echo Copied to %TARGET%:~/clock
ssh %TARGET% "bash ~/clock/pi/restart.sh"
endlocal
