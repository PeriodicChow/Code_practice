@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
cl main.cpp MIDIexample.cpp winmm.lib /Fe:MusicDemo.exe /EHsc
if %errorlevel% equ 0 (
    echo.
    echo ====== ±‡“Î≥…π¶£°======
    echo.
) else (
    echo.
    echo ====== ±‡“Î ß∞‹£¨«ÎºÏ≤È¥ÌŒÛ ======
    echo.
)
pause