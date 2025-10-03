@echo off
setlocal

:: ===== 0. Change to the folder where the .bat is located =====
cd /d "%~dp0"
echo Current directory: %CD%

:: ===== 1. Download yt-dlp.exe =====
echo Downloading yt-dlp.exe...
if not exist yt-dlp.exe (
    echo Downloading yt-dlp.exe using curl...
    curl -L -o yt-dlp.exe "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
) else (
    echo yt-dlp.exe already exists, skipping download.
)

:: ===== 2. Verify yt-dlp.exe =====
if not exist "yt-dlp.exe" (
    echo ERROR: yt-dlp.exe not found! Please check download.
    pause
    exit /b 1
) else (
    echo yt-dlp.exe found successfully.
)

:: ===== 3. Download ffmpeg zip =====
echo Downloading ffmpeg zip...
if not exist ffmpeg-master-latest-win64-gpl.zip (
    echo Downloading ffmpeg zip using curl...
    curl -L -o ffmpeg-master-latest-win64-gpl.zip "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
) else (
    echo ffmpeg zip already exists, skipping download.
)

:: ===== 4. Extract ffmpeg zip =====
echo Extracting ffmpeg zip...
if exist "ffmpeg-master-latest-win64-gpl" (
    echo ffmpeg folder already exists, skipping extraction.
) else (
    tar -xf ffmpeg-master-latest-win64-gpl.zip
)

:: ===== 5. Rename folder to ffmpeg =====
if exist ffmpeg rd /s /q ffmpeg
if exist "ffmpeg-master-latest-win64-gpl" ren "ffmpeg-master-latest-win64-gpl" ffmpeg

:: ===== 6. Verify ffmpeg.exe =====
if not exist "ffmpeg\bin\ffmpeg.exe" (
    echo ERROR: ffmpeg.exe not found! Please check download and extraction.
    pause
    exit /b 1
) else (
    echo ffmpeg.exe found successfully.
)

:: ===== 7. Append current folder and ffmpeg\bin to user PATH =====
echo Adding current folder and ffmpeg\bin to user PATH...
:: Get existing user PATH
for /f "tokens=2* delims= " %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"
:: Append new paths if not already included
echo %USER_PATH% | find /I "%CD%" >nul || set "USER_PATH=%USER_PATH%;%CD%"
echo %USER_PATH% | find /I "%CD%\ffmpeg\bin" >nul || set "USER_PATH=%USER_PATH%;%CD%\ffmpeg\bin"
:: Set user PATH
setx PATH "%USER_PATH%"

echo Done! yt-dlp and ffmpeg are ready to use.
pause
