@echo off
setlocal EnableDelayedExpansion
set LOG=C:\Users\User\Desktop\GrafikRaboty\_reg_com_1c_log2.txt
set TL={88511CA9-1078-460E-B99A-79528B8F0A17}
set BIN=C:\Program Files\1cv8\8.5.1.1522\bin

reg add "HKCR\TypeLib\%TL%\1.0\0\win64" /ve /d "%BIN%\comcntr.dll" /f >nul
echo typlib64_win64=!ERRORLEVEL! > "%LOG%"

reg add "HKCR\TypeLib\%TL%\1.0\HELPDIR" /ve /d "%BIN%" /f >nul
echo typlib64_helpdir=!ERRORLEVEL! >> "%LOG%"

reg add "HKCR\WOW6432Node\TypeLib\%TL%\1.0\0\win64" /ve /d "%BIN%\comcntr.dll" /f >nul
echo typlib32_win64=!ERRORLEVEL! >> "%LOG%"

reg add "HKCR\WOW6432Node\TypeLib\%TL%\1.0\HELPDIR" /ve /d "%BIN%" /f >nul
echo typlib32_helpdir=!ERRORLEVEL! >> "%LOG%"