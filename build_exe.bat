@echo off
echo Building FitGirlDownloader executable...
echo This might take a minute or two.
echo.

pip install pyinstaller
pyinstaller --noconsole --onefile --add-binary "7z.exe;." --add-binary "7z.dll;." --name "FitGirlDownloader" pyqt_downloader.py

echo.
echo Build complete! You can find the executable in the 'dist' folder.
pause
