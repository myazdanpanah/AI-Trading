@echo off
cd /d C:\Trading
set DJANGO_SETTINGS_MODULE=crypto_platform.settings.local
C:\Users\myazd\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe scripts\scheduler.py >> scheduler_output.log 2>&1
