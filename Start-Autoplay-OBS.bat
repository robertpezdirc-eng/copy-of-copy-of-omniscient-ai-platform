@echo off
setlocal
set URL=http://localhost:8009/omni-platform/docs/overlays/demo_autoplay.html
set OBS_PATH="%ProgramFiles%\obs-studio\bin\64bit\obs64.exe"
if not exist %OBS_PATH% set OBS_PATH="%ProgramFiles(x86)%\obs-studio\bin\64bit\obs64.exe"

echo Odpiram demo autoplay stran...
for %%P in ("%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe","%ProgramFiles%\Microsoft\Edge\Application\msedge.exe") do (
  if exist %%~P (
    start "Edge" %%~P --start-fullscreen --new-window %URL%
    goto :startobs
  )
)
start "Browser" %URL%

:startobs
echo Zagon OBS snemanja...
if not exist %OBS_PATH% (
  echo OBS Studio ni najden. Zaženite ga ročno in dodajte Browser Source na %URL%.
  pause
  exit /b 1
)
start "OBS" /B %OBS_PATH% --startrecording --minimize-to-tray
echo Snemanje v teku. Za ustavitev snemanja uporabite OBS.
exit /b 0