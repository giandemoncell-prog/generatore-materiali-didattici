@echo off
REM install.bat — Installer per Windows 10/11
REM Doppio clic su install.bat (o esegui da cmd)

setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
REM Lavora sempre nella cartella del .bat (es. se lanciato come amministratore da System32)
cd /d "%~dp0"

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║  Generatore di Materiali Inclusivi — Installazione ║
echo ╚═══════════════════════════════════════════════════╝
echo.

REM ─── 1. Verifica Python ───────────────────────────────────────────────────────
REM Prova prima il launcher "py" (su alcuni PC "python" apre lo Store o non esiste)
set PYTHON=
py -3 --version >nul 2>&1 && set PYTHON=py -3
if "!PYTHON!"=="" (
    python --version >nul 2>&1 && set PYTHON=python
)
if "!PYTHON!"=="" (
    echo [ERRORE] Python non trovato.
    echo   Scaricalo da: https://www.python.org/downloads/
    echo   Durante l'installazione spunta "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('!PYTHON! --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python %PY_VER% trovato

REM Verifica versione minima 3.9
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo [ERRORE] Richiesto Python 3.9 o superiore.
    pause
    exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 9 (
    echo [ERRORE] Richiesto Python 3.9 o superiore. Trovato: %PY_VER%
    pause
    exit /b 1
)

REM ─── 2. Ambiente virtuale Python ─────────────────────────────────────────────
if not exist ".venv\" (
    echo.
    echo [INFO] Creo ambiente virtuale Python...
    !PYTHON! -m venv .venv
    if errorlevel 1 (
        echo [ERRORE] Impossibile creare il venv.
        pause
        exit /b 1
    )
)

echo [INFO] Aggiorno pip...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip

echo [INFO] Installo dipendenze Python (1-2 minuti)...
.venv\Scripts\pip.exe install --quiet -r app\requirements_pro.txt
if errorlevel 1 (
    echo [ERRORE] Installazione dipendenze fallita.
    pause
    exit /b 1
)
echo [OK] Dipendenze Python installate

REM ─── 3. Chiave API Gemini ─────────────────────────────────────────────────────
if exist ".env" (
    findstr /C:"GEMINI_API_KEY=" .env >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Chiave API gia' configurata ^(.env^)
        goto :crea_launcher
    )
)

echo.
echo Configurazione chiave API Gemini
echo   La chiave e' gratuita — ottienila su:
echo   https://aistudio.google.com/apikey
echo   Senza chiave puoi usare un modello locale con Ollama:
echo   avvia_cli.bat ... --backend ollama  (gratis, offline, dati sul PC)
echo.
set /p API_KEY="  Incolla qui la tua chiave (es. AIzaSy...): "
if not "!API_KEY!"=="" (
    echo GEMINI_API_KEY=!API_KEY!> .env
    echo [OK] Chiave salvata in .env
) else (
    echo   (Chiave non inserita — puoi aggiungerla dopo modificando .env)
)

REM ─── 4. Script di avvio ───────────────────────────────────────────────────────
:crea_launcher
echo.
echo [INFO] Creo i lanciatori...

REM avvia_gui.bat — GUI Tkinter
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo if exist ".env" for /f "tokens=*" %%%%i in ^(.env^) do set "%%%%i"
    echo .venv\Scripts\pythonw.exe app\gui_generatore.py %%*
) > avvia_gui.bat

REM avvia_web.bat — Streamlit
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo if exist ".env" for /f "tokens=*" %%%%i in ^(.env^) do set "%%%%i"
    echo echo Apri http://localhost:8501 nel browser
    echo .venv\Scripts\streamlit.exe run app\streamlit_demo.py %%*
) > avvia_web.bat

REM avvia_cli.bat — CLI
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo if exist ".env" for /f "tokens=*" %%%%i in ^(.env^) do set "%%%%i"
    echo .venv\Scripts\python.exe app\generatore_pro.py %%*
) > avvia_cli.bat

echo [OK] Lanciatori creati: avvia_gui.bat  avvia_web.bat  avvia_cli.bat

REM ─── 5. Collegamento Desktop (opzionale) ─────────────────────────────────────
set INSTALL_DIR=%~dp0
set SHORTCUT=%USERPROFILE%\Desktop\GeneratoreDSA.lnk

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath = '%INSTALL_DIR%avvia_web.bat'; ^
   $s.WorkingDirectory = '%INSTALL_DIR%'; ^
   $s.Description = 'Generatore Materiali Inclusivi'; ^
   $s.Save()" >nul 2>&1

if exist "%SHORTCUT%" (
    echo [OK] Collegamento Desktop creato
)

REM ─── Riepilogo ────────────────────────────────────────────────────────────────
echo.
echo ╔═══════════════════════════════════════╗
echo ║  Installazione completata!             ║
echo ╚═══════════════════════════════════════╝
echo.
echo   Come avviare il programma:
echo   GUI desktop :  doppio clic su avvia_gui.bat
echo   Web browser :  doppio clic su avvia_web.bat
echo                  poi apri http://localhost:8501
echo   CLI         :  avvia_cli.bat --studente mario --testo testi\esempio_investiture.txt
echo   CLI locale  :  aggiungi --backend ollama [--modello-ollama ministral-3:8b]
echo                  (richiede Ollama attivo su localhost:11434)
echo.
echo   Profili disponibili in:  profili\
echo   Testi di esempio in:     testi\
echo   Output generati in:      output\
echo.
pause
