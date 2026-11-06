@echo off
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0deploy_to_server.ps1" %*
pause
