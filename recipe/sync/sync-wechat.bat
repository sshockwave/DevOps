@echo off
rclone sync C:\Users\sshockwave\lib\calibre rsDanvers-openssh:/mnt/lib/calibre/ --dry-run
rclone sync "C:\Users\sshockwave\Documents\WeChat Files\Backup\android_2ce5f52de121b147e1f259e016b116a8" rsDanvers-openssh:/mnt/usr/social/wechat --dry-run
choice /c YN /m "Do you want to apply the changes? (Y/N)"
if %errorlevel%==2 goto ending
rclone sync C:\Users\sshockwave\lib\calibre rsDanvers-openssh:/mnt/lib/calibre/ -P
rclone sync "C:\Users\sshockwave\Documents\WeChat Files\Backup\android_2ce5f52de121b147e1f259e016b116a8" rsDanvers-openssh:/mnt/usr/social/wechat -P
choice /c YN /m "Do you want to check the files? (Y/N)"
if %errorlevel%==2 goto ending
rclone check C:\Users\sshockwave\lib\calibre rsDanvers-openssh:/mnt/lib/calibre/ -P
rclone check "C:\Users\sshockwave\Documents\WeChat Files\Backup\android_2ce5f52de121b147e1f259e016b116a8" rsDanvers-openssh:/mnt/usr/social/wechat -P
pause
goto EOF
:ending
echo Operation canceled
pause
