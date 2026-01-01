@echo off
echo Installing requirements...
pip install -r requirements.txt
cls
echo Starting Nintendo Switch 2 Discord Status...
python main.py
pause
