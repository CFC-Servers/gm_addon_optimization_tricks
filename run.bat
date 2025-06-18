@echo off

REM Create a virtual env in a folder called "venv" if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    py -m venv venv
)

REM Activate the virtual env
call venv\Scripts\activate.bat

REM Install required packages for the env
python -m pip install -r requirements.txt

REM Run script
python main.py

pause
