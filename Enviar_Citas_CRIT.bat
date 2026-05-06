@echo off
:: La ruta a tu python.exe pero usando pythonw.exe (la 'w' es de Windowed/sin consola)
set PYTHON_EXE="C:\Users\Dalia\PycharmProjects\PythonProject\.venv\Scripts\pythonw.exe"

:: Ruta a tu script
set SCRIPT_PY="C:\Users\Dalia\PycharmProjects\PythonProject\.venv\Interfaz.py"

:: Ejecutar sin mostrar ventana
start "" %PYTHON_EXE% %SCRIPT_PY%
exit