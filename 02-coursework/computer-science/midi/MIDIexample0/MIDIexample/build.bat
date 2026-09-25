@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
cl main.cpp MIDIexample.cpp winmm.lib /Fe:MusicDemo.exe /EHsc
if %errorlevel% equ 0 (
    echo.
    echo ====== 编译成功！======
    echo.
) else (
    echo.
    echo ====== 编译失败，请检查错误 ======
    echo.
)
pause