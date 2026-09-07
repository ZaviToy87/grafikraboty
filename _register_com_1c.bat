@echo off
setlocal EnableDelayedExpansion
set LOG=C:\Users\User\Desktop\GrafikRaboty\_reg_com_1c_log.txt
regsvr32 /u /s "C:\Program Files\1cv8\8.5.1.1343\bin\comcntr.dll"
echo unregister_1343_comcntr=!ERRORLEVEL! > "%LOG%"
regsvr32 /s "C:\Program Files\1cv8\8.5.1.1522\bin\comcntr.dll"
echo register_1522_comcntr=!ERRORLEVEL! >> "%LOG%"