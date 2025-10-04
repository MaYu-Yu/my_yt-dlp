@echo off
setlocal enabledelayedexpansion

:: ===== 1. Set output folder =====
:SET_OUTPUT
set /p OUTPUT_DIR=Please enter the default download folder (e.g., D:\Code\yd-dlp\output): 

if "!OUTPUT_DIR!"=="" (
    echo Folder cannot be empty. Please enter a valid path.
    goto SET_OUTPUT
)

if not exist "!OUTPUT_DIR!" (
    echo The path does not exist. Please enter a valid path.
    goto SET_OUTPUT
)

:: Replace backslashes with forward slashes for yt-dlp
set OUTPUT_DIR=!OUTPUT_DIR:\=/!

:: Automatically create base mp3/mp4 folders
if not exist "!OUTPUT_DIR!/mp3" mkdir "!OUTPUT_DIR!/mp3"
if not exist "!OUTPUT_DIR!/mp4" mkdir "!OUTPUT_DIR!/mp4"

echo Output folder set to: !OUTPUT_DIR!
echo.

:LOOP
:: ===== 2. Choose download mode =====
:MODE_INPUT
echo Select download mode (type exit at any prompt to return here):
echo 1. Single Video MP3
echo 2. Single Video MP4
echo 3. Playlist MP3
echo 4. Playlist MP4
set /p MODE=Enter your choice (1-4): 
if /I "!MODE!"=="exit" goto LOOP
if "!MODE!"=="" (
    echo Choice cannot be empty.
    goto MODE_INPUT
)

:: ===== 3. Input YouTube URL =====
:URL_INPUT
set /p URL=Please enter the YouTube's URL (type exit to return): 
if /I "!URL!"=="exit" goto LOOP
if "!URL!"=="" (
    echo URL cannot be empty.
    goto URL_INPUT
)

:: ===== 4. Set output file/folder & yt-dlp command =====
if "%MODE%"=="1" (
    set OUTPUT_FILE="!OUTPUT_DIR!/mp3/%%(uploader)s/%%(title)s.%%(ext)s"
    set CMD=yt-dlp --no-playlist -x --audio-format mp3 --embed-thumbnail --embed-metadata --no-overwrites -o !OUTPUT_FILE! "%URL%"
    set CLEAN_DIR=!OUTPUT_DIR!\mp3
) else if "%MODE%"=="2" (
    set OUTPUT_FILE="!OUTPUT_DIR!/mp4/%%(uploader)s/%%(title)s.%%(ext)s"
    set CMD=yt-dlp --no-playlist -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --embed-thumbnail --embed-metadata --no-overwrites -o !OUTPUT_FILE! "%URL%"
    set CLEAN_DIR=!OUTPUT_DIR!\mp4
) else if "%MODE%"=="3" (
    set OUTPUT_FILE="!OUTPUT_DIR!/mp3/%%(playlist_uploader)s/%%(playlist_title)s/%%(title)s.%%(ext)s"
    set CMD=yt-dlp -x --audio-format mp3 --embed-thumbnail --embed-metadata --no-overwrites -o !OUTPUT_FILE! "%URL%"
    set CLEAN_DIR=!OUTPUT_DIR!\mp3
) else if "%MODE%"=="4" (
    set OUTPUT_FILE="!OUTPUT_DIR!/mp4/%%(playlist_uploader)s/%%(playlist_title)s/%%(title)s.%%(ext)s"
    set CMD=yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --embed-thumbnail --embed-metadata --no-overwrites -o !OUTPUT_FILE! "%URL%"
    set CLEAN_DIR=!OUTPUT_DIR!\mp4
) else (
    echo Invalid choice! Returning to main menu.
    goto LOOP
)

:: ===== 5. Execute yt-dlp =====
echo.
echo Starting download...
%CMD%
echo Download completed!

:: ===== 6. Clean up leftover .webm files =====
echo Cleaning up leftover .webm files...
for /r "!CLEAN_DIR!" %%F in (*.webm) do (
    echo Deleting: %%F
    del /q "%%F"
)
echo Cleanup complete.
echo.

goto LOOP
