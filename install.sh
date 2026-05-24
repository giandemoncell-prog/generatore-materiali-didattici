#!/usr/bin/env bash
# install.sh — Autoinstaller per Chromebook (Linux / Crostini)
# Uso: bash install.sh

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✓ $*${NC}"; }
info() { echo -e "${YELLOW}▸ $*${NC}"; }
err()  { echo -e "${RED}✗ $*${NC}" >&2; exit 1; }

echo -e "${BOLD}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║  Generatore di Materiali Inclusivi — Installazione ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── 1. Dipendenze di sistema ─────────────────────────────────────────────────
info "Aggiorno i pacchetti di sistema..."
sudo apt-get update -qq

PACCHETTI_MANCANTI=()
for pkg in python3 python3-pip python3-venv python3-tk; do
    dpkg -s "$pkg" &>/dev/null || PACCHETTI_MANCANTI+=("$pkg")
done

if [ ${#PACCHETTI_MANCANTI[@]} -gt 0 ]; then
    info "Installo: ${PACCHETTI_MANCANTI[*]}"
    sudo apt-get install -y "${PACCHETTI_MANCANTI[@]}"
fi

# Verifica tkinter (serve alla GUI)
python3 -c "import tkinter" 2>/dev/null || {
    info "Installo python3-tk (GUI Tkinter)..."
    sudo apt-get install -y python3-tk
}
ok "Dipendenze di sistema OK"

# ─── 2. Ambiente virtuale Python ─────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    info "Creo ambiente virtuale Python..."
    python3 -m venv .venv
fi

info "Aggiorno pip..."
.venv/bin/pip install --quiet --upgrade pip

info "Installo dipendenze Python (potrebbe richiedere 1-2 minuti)..."
.venv/bin/pip install --quiet -r app/requirements_pro.txt
ok "Dipendenze Python installate"

# ─── 3. Chiave API Gemini ─────────────────────────────────────────────────────
if [ -f ".env" ] && grep -q "GEMINI_API_KEY=." ".env"; then
    ok "Chiave API già configurata (.env)"
else
    echo ""
    echo -e "${BOLD}Configurazione chiave API Gemini${NC}"
    echo "  La chiave è gratuita — ottienila su:"
    echo -e "  ${YELLOW}https://aistudio.google.com/apikey${NC}"
    echo ""
    read -rp "  Incolla qui la tua chiave (es. AIzaSy...): " API_KEY
    if [ -n "$API_KEY" ]; then
        echo "GEMINI_API_KEY=$API_KEY" > .env
        ok "Chiave salvata in .env"
    else
        echo "  (Chiave non inserita — puoi aggiungerla dopo modificando il file .env)"
    fi
fi

# ─── 4. Script di avvio ───────────────────────────────────────────────────────
cat > avvia.sh << 'LAUNCHER'
#!/usr/bin/env bash
# Avvia la GUI del Generatore di Materiali Inclusivi
cd "$(dirname "$(readlink -f "$0")")"
if [ -f ".env" ]; then
    export "$(grep -v '^#' .env | xargs)"
fi
exec .venv/bin/python app/gui_generatore.py "$@"
LAUNCHER
chmod +x avvia.sh
ok "Script avvia.sh creato"

# Launcher CLI
cat > avvia_cli.sh << 'CLI'
#!/usr/bin/env bash
# Avvia il generatore da riga di comando
cd "$(dirname "$(readlink -f "$0")")"
if [ -f ".env" ]; then
    export "$(grep -v '^#' .env | xargs)"
fi
exec .venv/bin/python app/generatore_pro.py "$@"
CLI
chmod +x avvia_cli.sh

# Launcher Streamlit (web)
cat > avvia_web.sh << 'WEB'
#!/usr/bin/env bash
# Avvia la versione web (Streamlit) — apri http://localhost:8501 nel browser
cd "$(dirname "$(readlink -f "$0")")"
if [ -f ".env" ]; then
    export "$(grep -v '^#' .env | xargs)"
fi
exec .venv/bin/streamlit run app/streamlit_demo.py "$@"
WEB
chmod +x avvia_web.sh

# ─── 5. Collegamento sul Desktop (opzionale, Crostini) ───────────────────────
DESKTOP_DIR="$HOME/Desktop"
DESKTOP_FILE="$DESKTOP_DIR/GeneratoreDSA.desktop"

if [ -d "$DESKTOP_DIR" ]; then
    INSTALL_DIR="$(pwd)"
    cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Generatore Materiali Inclusivi
Comment=Genera materiali didattici per studenti con DSA/BES
Exec=bash ${INSTALL_DIR}/avvia.sh
Icon=applications-education
Terminal=false
Categories=Education;
DESKTOP
    chmod +x "$DESKTOP_FILE"
    ok "Collegamento Desktop creato"
fi

# ─── Riepilogo ────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════╗"
echo "║  Installazione completata con successo! ║"
echo -e "╚═══════════════════════════════════════╝${NC}"
echo ""
echo "  Come avviare il programma:"
echo -e "  ${BOLD}GUI desktop:${NC}  bash avvia.sh"
echo -e "  ${BOLD}Web browser:${NC}  bash avvia_web.sh  →  apri http://localhost:8501"
echo -e "  ${BOLD}CLI:${NC}          bash avvia_cli.sh --studente mario --testo testi/esempio_investiture.txt"
echo ""
echo "  Profili di esempio disponibili in:  profili/"
echo "  Testi di esempio disponibili in:    testi/"
echo "  Output generati in:                 output/"
echo ""
