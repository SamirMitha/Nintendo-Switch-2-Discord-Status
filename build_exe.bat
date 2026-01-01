@echo off
echo Building SwitchRPC Exe...
pyinstaller --noconfirm --onefile --windowed --name "Nintendo Switch 2 Discord Status" ^
    --hidden-import "PIL._tkinter_finder" ^
    --collect-all "customtkinter" ^
    main.py
echo Build Complete. Check dist/ folder.
pause
