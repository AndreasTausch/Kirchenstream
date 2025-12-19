@echo off
echo Beende alle python.exe und pythonw.exe Prozesse...

taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1

echo Alle Python-Prozesse wurden (falls vorhanden) beendet.
pause