@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Первый запуск: создаю окружение, подождите...
  python -m venv .venv
  if errorlevel 1 (
    echo Не найден Python. Установите Python 3 с python.org и повторите.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo Не удалось поставить библиотеки. Проверьте интернет и повторите.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
)

python -m pipeline %*
echo.
pause
