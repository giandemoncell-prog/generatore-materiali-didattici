#!/usr/bin/env python3
# gui_generatore.py — Interfaccia grafica per Generatore da Profili AI (v2)
# Avvio: python3 gui_generatore.py (con venv attivo)

import os
import sys
import glob
import yaml
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

CARTELLA_BASE = Path(__file__).parent
SCRIPT = CARTELLA_BASE / "generatore_pro.py"

# ─── PALETTE ──────────────────────────────────────────────────────────────────
BG      = "#F5F3EE"
BG2     = "#EDEAE3"
BG3     = "#E0DDD5"
VERDE   = "#2E7D4F"
VERDE_H = "#1F5C39"
VERDE_L = "#E8F5ED"
TESTO   = "#1A1A1A"
TESTO2  = "#666666"
BORDO   = "#D0CCC4"
ERRORE  = "#C0392B"
OK      = "#27AE60"


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def ottieni_studenti() -> list[str]:
    profili = glob.glob(str(CARTELLA_BASE / "profili" / "profilo_*.yaml"))
    nomi = []
    for p in sorted(profili):
        nome = Path(p).stem.replace("profilo_", "").replace("_", " ").title()
        nomi.append(nome)
    return nomi if nomi else ["(nessun profilo trovato)"]


def leggi_profilo(nome_studente: str) -> dict:
    key = nome_studente.lower().replace(" ", "_")
    percorso = CARTELLA_BASE / "profili" / f"profilo_{key}.yaml"
    try:
        with open(percorso, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def riassumi_profilo(profilo: dict) -> str:
    if not profilo:
        return "Nessun profilo caricato."
    righe = []

    diff = profilo.get("profilo_cognitivo", {}).get("aree_difficolta", {})
    forza = profilo.get("profilo_cognitivo", {}).get("aree_forza", {})
    strumenti = profilo.get("strumenti_compensativi", {})
    note = [n for n in profilo.get("note_osservazioni", []) if n]

    if diff:
        etichette = {"lettura": "Lettura", "scrittura": "Scrittura",
                     "calcolo": "Calcolo", "memoria_di_lavoro": "Memoria lavoro",
                     "attenzione": "Attenzione"}
        parti = [f"{etichette.get(k, k)}: {v}" for k, v in diff.items() if v]
        if parti:
            righe.append("Difficoltà: " + " · ".join(parti))

    if forza:
        buoni = [k.replace("_", " ") for k, v in forza.items()
                 if v and str(v).lower() not in ("", "bassa", "nella norma")]
        if buoni:
            righe.append("Punti di forza: " + ", ".join(buoni))

    attivi = [k.replace("_", " ") for k, v in strumenti.items()
              if v and str(v).lower() not in ("false", "no", "")]
    if attivi:
        righe.append("Strumenti: " + ", ".join(attivi[:4]))

    if note:
        righe.append("Nota: " + note[0][:80] + ("…" if len(note[0]) > 80 else ""))

    return "\n".join(righe) if righe else "Profilo caricato."


def apri_cartella(percorso: str) -> None:
    try:
        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", percorso])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", percorso])
        else:
            os.startfile(percorso)
    except Exception:
        pass


# ─── APP ──────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generatore da Profili AI")
        self.geometry("720x860")
        self.minsize(600, 700)
        self.configure(bg=BG)

        self._percorso_testo = tk.StringVar()
        self._studente       = tk.StringVar()
        self._tag            = tk.StringVar()
        self._nota           = tk.StringVar()
        self._glossario      = tk.BooleanVar()
        self._quiz           = tk.BooleanVar()
        self._tipo_quiz      = tk.StringVar(value="A")
        self._classroom      = tk.BooleanVar()
        self._video          = tk.BooleanVar()
        self._in_esecuzione  = False
        self._ultima_cartella = ""

        self._studente.trace_add("write", self._aggiorna_profilo)
        self.bind("<Control-g>", lambda e: self._avvia())
        self.bind("<Control-G>", lambda e: self._avvia())

        self._costruisci_ui()

        studenti = ottieni_studenti()
        if studenti:
            self._studente.set(studenti[0])

    # ─── UI ───────────────────────────────────────────────────────────────────

    def _costruisci_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg=VERDE, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="📚  Generatore da Profili AI",
                 font=("Georgia", 19, "bold"), fg="white", bg=VERDE
                 ).pack(side="left", padx=20, pady=14)
        tk.Label(header, text="Ctrl+G per generare",
                 font=("Helvetica", 10), fg="#A8D5BA", bg=VERDE
                 ).pack(side="right", padx=20)

        # ── Scrollable body ──
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._corpo = tk.Frame(canvas, bg=BG, padx=24, pady=16)

        self._corpo.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._corpo, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con rotella del mouse
        self.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.bind_all("<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units"))
        self.bind_all("<Button-5>",
            lambda e: canvas.yview_scroll(1, "units"))

        corpo = self._corpo

        # ── Studente ──
        self._sezione(corpo, "👤  Studente")
        studenti = ottieni_studenti()
        n = len(studenti)
        lbl_n = f"{n} profilo disponibile" if n == 1 else f"{n} profili disponibili"
        tk.Label(corpo, text=lbl_n, bg=BG, fg=TESTO2,
                 font=("Helvetica", 10)).pack(anchor="w")

        style = ttk.Style()
        style.configure("DSA.TCombobox", font=("Helvetica", 13))
        menu = ttk.Combobox(corpo, textvariable=self._studente,
                            values=studenti, state="readonly",
                            font=("Helvetica", 13))
        menu.pack(fill="x", pady=(4, 6))

        # Anteprima profilo
        self._frame_profilo = tk.Frame(corpo, bg=VERDE_L,
                                       highlightthickness=1,
                                       highlightbackground="#A8D5BA")
        self._frame_profilo.pack(fill="x", pady=(0, 14))
        self._lbl_profilo = tk.Label(self._frame_profilo, text="",
                                     bg=VERDE_L, fg="#1F5C39",
                                     font=("Helvetica", 11),
                                     justify="left", anchor="w",
                                     wraplength=640, padx=12, pady=8)
        self._lbl_profilo.pack(fill="x")

        # ── File testo ──
        self._sezione(corpo, "📄  Testo da adattare")
        riga_file = tk.Frame(corpo, bg=BG)
        riga_file.pack(fill="x", pady=(4, 14))
        tk.Entry(riga_file, textvariable=self._percorso_testo,
                 font=("Helvetica", 12), bg=BG2, relief="flat",
                 bd=0, highlightthickness=1,
                 highlightbackground=BORDO).pack(
                     side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
        tk.Button(riga_file, text="Sfoglia…", command=self._sfoglia,
                  bg=BG3, fg=TESTO, relief="flat",
                  font=("Helvetica", 12), cursor="hand2",
                  padx=12, pady=4).pack(side="left")

        # ── Etichetta ──
        self._sezione(corpo, "🏷️  Etichetta output  (opzionale)")
        tk.Entry(corpo, textvariable=self._tag,
                 font=("Helvetica", 12), bg=BG2, relief="flat",
                 bd=0, highlightthickness=1,
                 highlightbackground=BORDO).pack(
                     fill="x", ipady=7, pady=(4, 14))

        # ── Opzioni Pro ──
        self._sezione(corpo, "⚙️  Opzioni Pro")
        frame_opt = tk.Frame(corpo, bg=BG2,
                             highlightthickness=1, highlightbackground=BORDO)
        frame_opt.pack(fill="x", pady=(4, 14))

        self._cb(frame_opt, "📖  Glossario calibrato sul profilo (F.1)", self._glossario)

        riga_quiz = tk.Frame(frame_opt, bg=BG2)
        riga_quiz.pack(fill="x", padx=12, pady=6)
        self._cb_inline(riga_quiz, "✏️  Quiz", self._quiz)
        tk.Label(riga_quiz, text="  Tipo:", bg=BG2, fg=TESTO2,
                 font=("Helvetica", 12)).pack(side="left")
        for t, descr in (("A", "multipla"), ("B", "vero/falso"), ("C", "aperte")):
            tk.Radiobutton(riga_quiz, text=f"{t}", variable=self._tipo_quiz, value=t,
                           bg=BG2, fg=TESTO, font=("Helvetica", 12, "bold"),
                           activebackground=BG2, selectcolor=VERDE_L,
                           indicatoron=True).pack(side="left", padx=(8, 0))
            tk.Label(riga_quiz, text=f"={descr}", bg=BG2, fg=TESTO2,
                     font=("Helvetica", 10)).pack(side="left", padx=(0, 4))

        self._cb(frame_opt, "🎬  Video con voce narrante (F.5) — richiede Google TTS",
                 self._video)
        self._cb(frame_opt, "🏫  Pubblica su Google Classroom (F.3)",
                 self._classroom)

        # ── Nota ──
        self._sezione(corpo, "💬  Nota aggiuntiva  (opzionale)")
        tk.Entry(corpo, textvariable=self._nota,
                 font=("Helvetica", 12), bg=BG2, relief="flat",
                 bd=0, highlightthickness=1,
                 highlightbackground=BORDO).pack(
                     fill="x", ipady=7, pady=(4, 16))

        # ── Bottone genera ──
        self._btn_genera = tk.Button(
            corpo, text="▶   Genera materiali",
            command=self._avvia,
            bg=VERDE, fg="white", font=("Helvetica", 15, "bold"),
            relief="flat", cursor="hand2", pady=14,
            activebackground=VERDE_H, activeforeground="white"
        )
        self._btn_genera.pack(fill="x", pady=(0, 6))

        # Progress bar
        self._progress = ttk.Progressbar(corpo, mode="indeterminate", length=200)
        self._progress.pack(fill="x", pady=(0, 4))

        # Pulsante apri cartella (nascosto inizialmente)
        self._btn_apri = tk.Button(
            corpo, text="📁  Apri cartella output",
            command=self._apri_output,
            bg=VERDE_L, fg=VERDE_H, font=("Helvetica", 12, "bold"),
            relief="flat", cursor="hand2", pady=8,
            activebackground="#C8ECD5", activeforeground=VERDE_H
        )

        # ── Log ──
        self._sezione(corpo, "📋  Log")
        frame_log = tk.Frame(corpo, bg=BG)
        frame_log.pack(fill="both", expand=True, pady=(4, 8))
        self._log = tk.Text(frame_log, height=12, font=("Courier", 11),
                            bg="#1E1E1E", fg="#D4D4D4", relief="flat",
                            bd=0, wrap="word", state="disabled")
        self._log.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame_log, command=self._log.yview)
        sb.pack(side="right", fill="y")
        self._log["yscrollcommand"] = sb.set
        self._log.tag_config("ok",   foreground="#6EC07A")
        self._log.tag_config("err",  foreground="#F47F7F")
        self._log.tag_config("info", foreground="#9CDCFE")
        self._log.tag_config("warn", foreground="#E5C07B")

        # ── Status bar ──
        self._status = tk.Label(self, text="Pronto.",
                                bg=BG3, fg=TESTO2,
                                font=("Helvetica", 10),
                                anchor="w", padx=12, pady=4)
        self._status.pack(fill="x", side="bottom")

    def _sezione(self, parent, testo):
        tk.Label(parent, text=testo, bg=BG, fg=TESTO2,
                 font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(6, 0))

    def _cb(self, parent, testo, var):
        f = tk.Frame(parent, bg=parent["bg"])
        f.pack(fill="x", padx=12, pady=4)
        ind = tk.Label(f, text="☐", bg=parent["bg"], fg=TESTO2,
                       font=("Helvetica", 14), cursor="hand2", width=2)
        ind.pack(side="left")
        lbl = tk.Label(f, text=testo, bg=parent["bg"], fg=TESTO,
                       font=("Helvetica", 13), cursor="hand2", anchor="w")
        lbl.pack(side="left", fill="x", expand=True)

        def aggiorna(*_):
            if var.get():
                ind.config(text="☑", fg=VERDE)
                lbl.config(fg=TESTO)
            else:
                ind.config(text="☐", fg=TESTO2)
                lbl.config(fg=TESTO2)

        def toggle(_=None):
            var.set(not var.get())
            aggiorna()

        ind.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)
        var.trace_add("write", aggiorna)

    def _cb_inline(self, parent, testo, var):
        ind = tk.Label(parent, text="☐", bg=parent["bg"], fg=TESTO2,
                       font=("Helvetica", 14), cursor="hand2", width=2)
        ind.pack(side="left")
        lbl = tk.Label(parent, text=testo, bg=parent["bg"], fg=TESTO,
                       font=("Helvetica", 13), cursor="hand2")
        lbl.pack(side="left")

        def aggiorna(*_):
            if var.get():
                ind.config(text="☑", fg=VERDE)
                lbl.config(fg=TESTO)
            else:
                ind.config(text="☐", fg=TESTO2)
                lbl.config(fg=TESTO2)

        def toggle(_=None):
            var.set(not var.get())
            aggiorna()

        ind.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)
        var.trace_add("write", aggiorna)

    # ─── LOGICA ───────────────────────────────────────────────────────────────

    def _aggiorna_profilo(self, *_):
        nome = self._studente.get()
        if not nome or nome.startswith("("):
            self._lbl_profilo.config(text="Nessun profilo selezionato.")
            return
        profilo = leggi_profilo(nome)
        testo = riassumi_profilo(profilo)
        self._lbl_profilo.config(text=testo)

    def _sfoglia(self):
        percorso = filedialog.askopenfilename(
            initialdir=str(CARTELLA_BASE / "testi"),
            title="Seleziona il file testo",
            filetypes=[("File testo", "*.txt"), ("Tutti", "*.*")]
        )
        if percorso:
            self._percorso_testo.set(percorso)

    def _log_scrivi(self, testo, tag=None):
        self._log.configure(state="normal")
        self._log.insert("end", testo + "\n", tag or "")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _set_status(self, testo):
        self._status.config(text=testo)

    def _apri_output(self):
        if self._ultima_cartella and Path(self._ultima_cartella).exists():
            apri_cartella(self._ultima_cartella)

    def _avvia(self):
        if self._in_esecuzione:
            return

        studente = self._studente.get().lower().replace(" ", "_")
        testo = self._percorso_testo.get().strip()

        if not testo:
            messagebox.showwarning("Attenzione", "Seleziona prima un file testo.")
            return
        if not Path(testo).exists():
            messagebox.showerror("Errore", f"File non trovato:\n{testo}")
            return

        cmd = [sys.executable, str(SCRIPT), "--studente", studente, "--testo", testo]
        if self._tag.get().strip():
            cmd += ["--tag", self._tag.get().strip()]
        if self._nota.get().strip():
            cmd += ["--nota", self._nota.get().strip()]
        if self._glossario.get():
            cmd.append("--glossario-pro")
        if self._quiz.get():
            cmd += ["--quiz", self._tipo_quiz.get()]
        if self._classroom.get():
            cmd.append("--classroom")
        if self._video.get():
            cmd.append("--video")

        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._btn_apri.pack_forget()
        self._log_scrivi(f"▶ Avvio per: {self._studente.get()}", "info")

        self._in_esecuzione = True
        self._btn_genera.configure(text="⏳  In elaborazione…",
                                   state="disabled", bg="#888")
        self._progress.start(12)
        self._set_status("Elaborazione in corso…")

        from datetime import datetime
        tag_val = self._tag.get().strip()
        suffisso = f"_{tag_val}" if tag_val else ""
        data = datetime.now().strftime("%Y-%m-%d")
        self._ultima_cartella = str(
            CARTELLA_BASE / "output" / studente / f"{data}{suffisso}"
        )

        thread = threading.Thread(target=self._esegui, args=(cmd,), daemon=True)
        thread.start()

    def _esegui(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(CARTELLA_BASE),
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )
            for riga in proc.stdout:
                riga = riga.rstrip()
                if not riga:
                    continue
                if any(x in riga for x in (
                    "violations {", "quota_metric", "quota_id", "quota_dimensions",
                    "retry_delay", "links {", "url:", "seconds:"
                )) or riga.strip() in ("}", "{"):
                    continue
                if "429" in riga and "quota" in riga.lower():
                    self.after(0, self._log_scrivi,
                               "  ⏳ Limite API — attendo e riprovo…", "warn")
                    continue
                if any(x in riga for x in (
                    "FutureWarning", "DeprecationWarning",
                    "deprecated", "README"
                )):
                    continue

                if riga.startswith("✓") or "Salvato:" in riga or "Completato" in riga:
                    self.after(0, self._log_scrivi, riga, "ok")
                elif "Errore" in riga or "✗" in riga:
                    self.after(0, self._log_scrivi, riga, "err")
                elif any(riga.startswith(p) for p in (
                    "===", "[Pro]", "1/", "2/", "3/", "•", "▶"
                )):
                    self.after(0, self._log_scrivi, riga, "info")
                else:
                    self.after(0, self._log_scrivi, riga)

            proc.wait()
            if proc.returncode == 0:
                self.after(0, self._log_scrivi, "\n✓ Tutto completato!", "ok")
                self.after(0, self._set_status, "✓ Generazione completata.")
                self.after(0, lambda: self._btn_apri.pack(fill="x", pady=(0, 8),
                                                          before=self._progress))
            else:
                self.after(0, self._log_scrivi, "\n✗ Terminato con errori.", "err")
                self.after(0, self._set_status, "✗ Errore durante la generazione.")
        except Exception as e:
            self.after(0, self._log_scrivi, f"Errore interno: {e}", "err")
            self.after(0, self._set_status, "✗ Errore interno.")
        finally:
            self._in_esecuzione = False
            self.after(0, self._progress.stop)
            self.after(0, lambda: self._btn_genera.configure(
                text="▶   Genera materiali", state="normal", bg=VERDE))


if __name__ == "__main__":
    app = App()
    app.mainloop()
