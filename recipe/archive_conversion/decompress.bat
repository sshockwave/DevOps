@echo off
for /R %%F in (*.7z) do (
	"C:\Program Files\7-Zip\7z.exe" x -y -o"%%~nF" "%%F" *
	if errorlevel 0 goto error
	echo "%%F"
)
pause
error:
echo Error!
pause
