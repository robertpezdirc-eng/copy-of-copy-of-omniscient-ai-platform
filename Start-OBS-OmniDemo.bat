@echo off
setlocal
set OBS_PATH="%ProgramFiles%\obs-studio\bin\64bit\obs64.exe"
if not exist %OBS_PATH% set OBS_PATH="%ProgramFiles(x86)%\obs-studio\bin\64bit\obs64.exe"
if not exist %OBS_PATH% (
  echo OBS Studio ni najden v privzetem imeniku.
  echo Prosimo, namestite OBS ali posodobite pot v datoteki Start-OBS-OmniDemo.bat.
  pause
  exit /b 1
)
rem Zaženi OBS in takoj začni snemati
start "OBS" /B %OBS_PATH% --startrecording --minimize-to-tray
exit /b 0