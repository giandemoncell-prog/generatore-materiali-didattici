#!/usr/bin/env python3
"""
build_zip.py — Genera i pacchetti distribuibili nella cartella dist/

Uso:
    python scripts/build_zip.py

Output nella cartella dist/:
    generatore_chromebook.zip   — per Chromebook / Linux / Mac
    generatore_windows.zip      — per Windows 10/11

Ogni ZIP contiene tutto il progetto meno file di sviluppo
(__pycache__, tests/, .github/, campioni/, .claude/, ecc.).
"""

import zipfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

INCLUDI = [
    "app",
    "profili",
    "testi",
    "docs",
    "README.md",
    "install.sh",
    "install.bat",
]

ESCLUDI_PATTERN = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".omc",
    ".claude",
    ".github",
    "campioni",
    "tests",
    "scripts",
    "dist",
    "output",
    ".env",
    ".venv",
    "venv",
    "pytest_output.txt",
    "AGENT_BRIEF.md",
}

ESCLUDI_EXT = {".pyc", ".pyo"}


def _da_includere(path: Path) -> bool:
    for parte in path.parts:
        if parte in ESCLUDI_PATTERN:
            return False
    return path.suffix not in ESCLUDI_EXT


def _aggiungi_dir(zf: zipfile.ZipFile, src: Path, base: Path) -> None:
    if src.is_file():
        if _da_includere(src.relative_to(ROOT)):
            zf.write(src, src.relative_to(base))
        return
    for item in sorted(src.rglob("*")):
        if item.is_file() and _da_includere(item.relative_to(ROOT)):
            zf.write(item, item.relative_to(base))


def _crea_output_placeholder(zf: zipfile.ZipFile) -> None:
    """Crea la cartella output/ vuota nel ZIP."""
    info = zipfile.ZipInfo("output/.gitkeep")
    zf.writestr(info, "")


def build(nome_zip: str, escludi_extra: set[str] | None = None) -> Path:
    DIST.mkdir(exist_ok=True)
    dest = DIST / nome_zip
    dest.unlink(missing_ok=True)

    extra = escludi_extra or set()

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for voce in INCLUDI:
            src = ROOT / voce
            if not src.exists():
                continue
            if voce in extra:
                continue
            if src.is_file():
                if _da_includere(Path(voce)):
                    zf.write(src, voce)
            else:
                _aggiungi_dir(zf, src, ROOT)
        _crea_output_placeholder(zf)

    print(f"  OK  {dest.relative_to(ROOT)}  ({dest.stat().st_size // 1024} KB)")
    return dest


def main() -> None:
    print("Generazione pacchetti distribuibili...\n")

    # Chromebook / Linux — include install.sh, escludi install.bat
    build("generatore_chromebook.zip", escludi_extra={"install.bat"})

    # Windows — include install.bat, escludi install.sh
    build("generatore_windows.zip", escludi_extra={"install.sh"})

    print(f"\nFile pronti in:  {DIST.relative_to(ROOT)}/")
    print("  >> Carica su Google Drive e condividi il link.")


if __name__ == "__main__":
    main()
