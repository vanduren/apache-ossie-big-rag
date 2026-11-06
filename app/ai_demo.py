#!/usr/bin/env python3
"""ai_demo.py — échte AI-agent bovenop het Apache Ossie model (Knol & Bloei).

Versus webshop_demo.py: hier matcht géén keyword-truc, maar een echte LLM-stack:

  1. Elke metric/dimensie met zijn `ai_context` uit het Ossie-model wordt
     geëmbed met Qwen3-Embedding en opgeslagen in een lokale RAG-index (rag.db).
  2. Een vrijetekstvraag wordt dezelfde embedding in gestuurd; de meest
     vergelijkbare kandidaten gaan als context naar het chatmodel (Qwen3-8B).
  3. Het chatmodel kiest metric + dimensie (strikt JSON) — wél uit het model,
     want Ossie is de einzige waarheid → geen hallucinaties.
  4. De SQL compileert opnieuw via ossie_core (identiek aan BI/CLI) en draait
     op SQLite; het chatmodel formuleert tenslotte het antwoord in natuurlijke taal.

Starten:  uv run python ai_demo.py     (LLM-server op 127.0.0.1:8000 vereist)
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
import threading
import urllib.error
import urllib.request

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))
from ossie_core import OssieModel, DEFAULT_MODEL, DEFAULT_DB  # noqa: E402

# --------------------------------------------------------------------------
# LLM-configuratie (OpenAI-compatible API, lokaal — oMLX op poort 8000)
# --------------------------------------------------------------------------
API = "http://127.0.0.1:8000/v1"
API_KEY = os.environ.get("LLM_API_KEY", "dujo")
EMBED_MODEL = "Qwen3-Embedding-0.6B-4bit-DWQ"
CHAT_MODEL = "Qwen3-8B-4bit"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
DB_PATH = os.environ.get("RAG_DB", "rag.db")

VOORBEELDVRAAG_DEFAULTS = [
    "Wat is de omzet per categorie?",
    "Hoeveel orders zijn er per maand geplaatst?",
    "Welke stad geeft het meeste geld uit?",
    "Wat is de gemiddelde orderwaarde per klantsegment?",
    "Hoeveel stuks gaan er per maand weg?",
]

# --------------------------------------------------------------------------
# HTTP-laag (alleen Standaard Library, geen extra dependencies)
# --------------------------------------------------------------------------
def _post(pad: str, body: dict, timeout: int = 120):
    req = urllib.request.Request(
        API + pad,
        data=json.dumps(body).encode("utf-8"),
        headers={**HEADERS, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def embed(teksten: list[str]) -> list[list[float]]:
    uit = _post("/embeddings", {"model": EMBED_MODEL, "input": teksten})
    return [d["embedding"] for d in sorted(uit["data"], key=lambda d: d["index"])]


def chat(messages: list[dict], temperature: float = 0.1) -> str:
    uit = _post("/chat/completions", {
        "model": CHAT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 512,
        # Qwen3 in thinking-mode vult het hele antwoord met reasoning_content;
        # zonder thinking krijgen we direct bruikbare `content`
        "chat_template_kwargs": {"enable_thinking": False},
    })
    msg = uit["choices"][0]["message"]
    return (msg.get("content") or msg.get("reasoning_content") or "").strip()


# --------------------------------------------------------------------------
# RAG-index: ai_context uit het Ossie-model → embedding → rag.db
# --------------------------------------------------------------------------
def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


class RagIndex:
    """Embedding-store van de semantische ankerpunten uit het Ossie-model."""

    def __init__(self, db_path: str, model: OssieModel):
        self.db_path = db_path
        self.model = model
        self.con = sqlite3.connect(db_path, check_same_thread=False)
        self.con.execute("CREATE TABLE IF NOT EXISTS index_rows "
                         "(ref TEXT PRIMARY KEY, soort TEXT, tekst TEXT, embedding BLOB)")
        self.con.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")

    def _bronnen(self):
        """(ref, soort, tekst) per metric/dimensie — tekst uit de ai_context."""
        for ref, m, _ in self.model.alle_metrics():
            yield ref, "metric", self._omschrijf(m["name"], m)
        for ref in self.model.alle_dimensies():
            dds, dv = ref.split(".", 1)
            yield ref, "dimensie", self._omschrijf(dv.replace("_", " "), self.model.field(dds, dv))

    @staticmethod
    def _omschrijf(naam, node):
        ctx = node.get("ai_context") or {}
        syn = ctx.get("synonyms", []) if isinstance(ctx, dict) else []
        vb = ctx.get("examples", []) if isinstance(ctx, dict) else []
        return (f"{naam}: {node.get('description', '')}. "
                f"Synoniemen: {', '.join(map(str, syn))}. "
                f"Voorbeeldvragen: {', '.join(map(str, vb))}").strip()

    def fingerprint(self):
        with open(self.model.path, "rb") as f:
            return str(hash(f.read()))

    def bouw_indien_nodig(self, force=False):
        """Index (her)bouwen als het YAML-model gewijzigd is. Geeft aantal rijen."""
        fp = self.fingerprint()
        row = self.con.execute("SELECT v FROM meta WHERE k='fp'").fetchone()
        if not force and row and row[0] == fp:
            return self.con.execute("SELECT COUNT(*) FROM index_rows").fetchone()[0]
        bronnen = list(self._bronnen())
        embeddings = embed([t for _, _, t in bronnen])
        self.con.execute("DELETE FROM index_rows")
        for (ref, soort, tekst), vec in zip(bronnen, embeddings):
            self.con.execute("INSERT OR REPLACE INTO index_rows VALUES (?,?,?,?)",
                             (ref, soort, tekst, json.dumps(vec)))
        self.con.execute("INSERT OR REPLACE INTO meta VALUES ('fp', ?)", (fp,))
        self.con.commit()
        return len(bronnen)

    def zoek(self, vraag: str, top_k=8):
        """Cosine-similarity search → [(score, ref, soort, tekst)]."""
        q = embed([vraag])[0]
        rows = self.con.execute("SELECT ref, soort, tekst, embedding FROM index_rows").fetchall()
        scored = []
        for ref, soort, tekst, blob in rows:
            scored.append((_cosine(q, json.loads(blob)), ref, soort, tekst))
        scored.sort(reverse=True)
        return scored[:top_k]


# --------------------------------------------------------------------------
# De agent: vraag → RAG-kandidaten → LLM kiest → Ossie compileert → LLM antwoordt
# --------------------------------------------------------------------------
def kies_uit_embedding(index: RagIndex, vraag: str, pogingen=2):
    """Stap 1+2: embeddingleven kandidaten, LLM laat kiezen (strikt JSON).

    De keuze wordt gevalideerd tegen het Ossie-model: het LLM mag alleen
    referenties teruggeven die écht in het model bestaan. Anders: één retry
    met foutmelding, daarna een expliciete fout — zo voorkomt Ossie de
    hallucinatie, ook als het model zelf twijfelt.
    """
    kandidaten = index.zoek(vraag)
    instructie = (index.model.ai_context or {}).get("instructions", "")
    lijst = "\n".join(f"- {ref}  [{soort}]  {tekst}" for _, ref, soort, tekst in kandidaten)
    geldige_metrics = {r for r, _, _ in index.model.alle_metrics()}
    geldige_dims = set(index.model.alle_dimensies())
    basis = (
        f"Jij queryt een semantisch Ossie-model. {instructie}\n\n"
        f"Kandidaten (alleen hieruit kiezen!):\n{lijst}\n\n"
        f"Vraag: {vraag}\n\n"
        '"metric" MOET een ref met tag [metric] zijn, "dimensie" een ref met '
        'tag [dimensie] of null. Geen enkele metrische kandidaat passend? '
        'zet dan "metric": null.\n'
        'Antwoord ALLEEN met JSON: {"metric": "<ref>", "dimensie": "<ref of null>", '
        '"toelichting": "<korte uitleg in het Nederlands>"}'
    )
    feedback = ""
    for _ in range(pogingen):
        antwoord = chat([{"role": "user", "content": basis + feedback}])
        m = re.search(r"\{.*\}", antwoord, flags=re.S)
        if not m:
            feedback = f"\n\nFOUT: je gaf geen JSON. Jouw antwoord: {antwoord[:120]}"
            continue
        keuze = json.loads(m.group(0))
        dim = keuze.get("dimensie")
        if dim in ("null", "None", ""):
            dim = None
        metric = keuze.get("metric")
        if metric in ("null", "None", ""):
            metric = None
        metric_ok = metric is None or metric in geldige_metrics
        dim_ok = dim is None or dim in geldige_dims
        if metric_ok and dim_ok:
            keuze["metric"], keuze["dimensie"] = metric, dim
            return keuze, kandidaten
        feedback = (f"\n\nFOUT: {keuze.get('metric')!r} / {dim!r} bestaan niet in het model "
                    f"(dimensies zijn geen metrics!). Geldige metrics: {sorted(geldige_metrics)}. "
                    f"Niets passend? kies dan \"metric\": null.")
    raise ValueError("LLM bleef een onbekende metric kiezen — probeer je vraag te herschrijven.")


def formuleer_antwoord(vraag: str, sql: str, kolommen, rijen) -> str:
    """Stap 5: zet het queryresultaat om naar een natuurlijktaalantwoord."""
    tabel = "\n".join(" | ".join(str(c) for c in r) for r in rijen[:12])
    antwoord = chat([
        {"role": "system", "content": "Je bent data-analist bij bloemenwebshop Knol & Bloei. "
                                      "Beantwoord kort en concreet in het Nederlands, met cijfers."},
        {"role": "user", "content": f"Vraag: {vraag}\nSQL: {sql}\nResultaat:\n"
                                    f"{' | '.join(kolommen)}\n{tabel}"},
    ], temperature=0.3)
    return antwoord


# --------------------------------------------------------------------------
# UI (CustomTkinter / "Tinker Q")
# --------------------------------------------------------------------------
class AiDemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Apache Ossie × AI — agent met embeddings + LLM (Knol & Bloei)")
        self.geometry("1050x720")
        ctk.set_appearance_mode("dark")

        self.model = OssieModel(DEFAULT_MODEL)
        self.index = RagIndex(DB_PATH, self.model)
        self.bezig = False

        kop = ctk.CTkFrame(self, corner_radius=0, fg_color="#16324a")
        kop.pack(fill="x")
        ctk.CTkLabel(kop, text="🤖  Ossie + Qwen3 — vraag het maar",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)
        self.status = ctk.CTkLabel(kop, text="", text_color="#9fc9ec",
                                   font=ctk.CTkFont(size=12))
        self.status.pack(side="right", padx=16)

        bediening = ctk.CTkFrame(self)
        bediening.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(bediening, text="Stel een vraag in gewone taal — de agent zoekt "
                                     "met embeddings in rag.db, het LLM kiest uit het Ossie-model.",
                     font=ctk.CTkFont(size=11), text_color="#aaa").pack(anchor="w", padx=12, pady=(8, 2))

        rij = ctk.CTkFrame(bediening, fg_color="transparent")
        rij.pack(fill="x", padx=12, pady=6)
        self.txt_vraag = ctk.CTkEntry(rij, placeholder_text="Bijv. wat is de omzet per categorie?",
                                      height=38, font=ctk.CTkFont(size=14))
        self.txt_vraag.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.txt_vraag.bind("<Return>", lambda e: self._start())
        self.knop = ctk.CTkButton(rij, text="Vraag het aan de AI 🤖", width=180, height=38,
                                  command=self._start)
        self.knop.pack(side="left")

        ctk.CTkLabel(bediening, text="Voorbeeldvragen:",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=12)
        voorb = ctk.CTkFrame(bediening, fg_color="transparent")
        voorb.pack(fill="x", padx=8, pady=(2, 8))
        vragen = list(dict.fromkeys(
            list((self.model.ai_context or {}).get("examples", [])) + VOORBEELDVRAAG_DEFAULTS))
        for i, v in enumerate(vragen):
            ctk.CTkButton(voorb, text=v, fg_color="#2a4d68", hover_color="#3b8ed0",
                          anchor="w",
                          command=lambda t=v: (self.txt_vraag.delete(0, "end"),
                                               self.txt_vraag.insert(0, t),
                                               self._start())).grid(
                row=i // 2, column=i % 2, padx=4, pady=3, sticky="we")
        voorb.grid_columnconfigure((0, 1), weight=1)

        self.log = ctk.CTkTextbox(self, font=ctk.CTkFont("Menlo", 12))
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._toon("\n".join([
            "Klaar. De agent werkt in 4 stappen:",
            "  1. Je vraag wordt geëmbed (Qwen3-Embedding) en tegen rag.db gehouden",
            "  2. De beste kandidaten (ai_context uit het Ossie-model) gaan naar Qwen3-8B",
            "  3. Het LLM kiest metric + dimensie → Ossie compileert de SQL",
            "  4. SQLite voert uit; het LLM formuleert het antwoord",
            "",
            "Tip: klik op een voorbeeldvraag of typ je eigen vraag.",
        ]))

        threading.Thread(target=self._ensure_index, daemon=True).start()

    # ------------------------------------------------------------- helpers
    def _toon(self, txt):
        self.log.delete("1.0", "end")
        self.log.insert("1.0", txt)
        self.log.see("end")

    def _append(self, txt):
        self.log.insert("end", txt + "\n")
        self.log.see("end")

    def _stel_in(self, fn):
        self.after(0, fn)

    def _ensure_index(self):
        self._stel_in(lambda: self.status.configure(text="RAG-index controleren…"))
        try:
            n = self.index.bouw_indien_nodig()
            self._stel_in(lambda: self.status.configure(
                text=f"{CHAT_MODEL} · {EMBED_MODEL} · rag.db: {n} ankerpunten"))
        except Exception as exc:
            self._stel_in(lambda: self.status.configure(
                text=f"⚠️ index mislukt: {exc}"))

    # ------------------------------------------------------------- vraag--flow
    def _start(self):
        vraag = self.txt_vraag.get().strip()
        if not vraag or self.bezig:
            return
        self.bezig = True
        self.knop.configure(state="disabled", text="Denken… 🧠")
        threading.Thread(target=self._verwerk, args=(vraag,), daemon=True).start()

    def _klaar(self):
        self.bezig = False
        self.knop.configure(state="normal", text="Vraag het aan de AI 🤖")

    def _verwerk(self, vraag: str):
        try:
            self._stel_in(lambda: self._toon(f"Vraag: {vraag}\n"))
            self._stel_in(lambda: self._append("① Vraag embedden + zoeken in rag.db…"))
            keuze, kandidaten = kies_uit_embedding(self.index, vraag)
            regels = [f"   Top-kandidaten (cosine):"]
            for s, ref, soort, _ in kandidaten[:5]:
                markering = "→" if ref in (keuze.get("metric"), keuze.get("dimensie")) else " "
                regels.append(f"   {markering} {s:+.3f}  [{soort:8}] {ref}")
            self._stel_in(lambda: self._append("\n".join(regels)))

            metric = keuze.get("metric")
            dim = keuze.get("dimensie") or None
            if not metric:
                self._stel_in(lambda: self._append(
                    "\n⛔ Het LLM stelt vast dat dit model géén passende metric heeft.\n"
                    "   De agent weigert te gokken — precies het belang van Ossie:\n"
                    "   geen metric in het model = geen antwoord, dus geen hallucinatie.\n"
                    "   Voeg de metric toe aan het YAML-model en stel de vraag opnieuw."))
                return
            if dim in ("null", "None", ""):
                dim = None
            self._stel_in(lambda: self._append(
                f"\n② {CHAT_MODEL} koos: metric `{metric}`, dimensie `{dim}`\n"
                f"   «{keuze.get('toelichting', '')}»"))

            self._stel_in(lambda: self._append("③ SQL compileren uit het Ossie-model…"))
            sql = self.model.compileer(metric, dim)
            self._stel_in(lambda: self._append(
                "\n".join(f"   {ln}" for ln in sql.splitlines())))

            self._stel_in(lambda: self._append("\n④ Uitvoeren op SQLite (webshop.db)…"))
            kolommen, rijen = self.model.uitvoeren(DEFAULT_DB, sql)
            regels = ["   " + " | ".join(str(k) for k in kolommen)]
            for r in rijen[:10]:
                regels.append("   " + " | ".join(str(c) for c in r))
            self._stel_in(lambda: self._append("\n".join(regels)))

            self._stel_in(lambda: self._append(f"\n⑤ Antwoord formuleren via {CHAT_MODEL}…"))
            antwoord = formuleer_antwoord(vraag, sql, kolommen, rijen)
            self._stel_in(lambda: self._append(f"\n💬 {antwoord}"))
        except urllib.error.URLError as exc:
            self._stel_in(lambda: self._append(
                f"\n❌ LLM-server niet bereikbaar op {API} — draait oMLX?  ({exc})"))
        except (KeyError, ValueError) as exc:
            self._stel_in(lambda: self._append(f"\n❌ {exc}"))
        except Exception as exc:
            self._stel_in(lambda: self._append(f"\n❌ Onverwacht: {type(exc).__name__}: {exc}"))
        finally:
            self._stel_in(self._klaar)


def main():
    for pad, tip in ((DEFAULT_MODEL, None), (DEFAULT_DB,
        "uv run python scripts/genereer_data.py && uv run python scripts/bouw_database.py")):
        if not os.path.exists(pad):
            print(f"{pad} niet gevonden" + (f" — bouw hem eerst:\n  {tip}" if tip else ""))
            sys.exit(1)
    AiDemoApp().mainloop()


if __name__ == "__main__":
    main()
