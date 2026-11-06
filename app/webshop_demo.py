#!/usr/bin/env python3
"""Knol & Bloei — interactieve demo van Apache Ossie (incubating).

CustomTkinter-interface bovenop het Ossie-model `models/knol_en_bloei.ossie.yaml`
met als database SQLite (data/webshop.db). Deze UI is een willekeurige
"consumer": hij kent de tabellen niet, alleen het Ossie-model.

Starten:  uv run python app/webshop_demo.py
"""
import os
import sys
import tkinter.ttk as ttk
import tkinter as tk

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ossie_core import OssieModel, valideer, DEFAULT_MODEL, DEFAULT_DB  # noqa: E402

KLEUR_GRAFIEK = "#3b8ed0"
KLEUR_GRAFIEK2 = "#6ee28a"


def fmt_getal(x):
    if isinstance(x, float):
        return f"€ {x:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")
    return str(x)


class BarChart(ctk.CTkCanvas):
    """Eenvoudige staafdiagram op een canvas (geen extra dependencies)."""

    def __init__(self, master, **kw):
        super().__init__(master, bg="#1f1f1f", highlightthickness=0, **kw)
        self.bind("<Configure>", lambda e: self.draw(self._data, self._metricnaam))
        self._data, self._metricnaam = [], ""

    def draw(self, data, metricnaam):
        self._data, self._metricnaam = data, metricnaam
        self.delete("all")
        if not data:
            return
        W = self.winfo_width() or 700
        H = self.winfo_height() or 260
        marge_l, marge_b, marge_o = 90, 8, 46
        plot_b = H - marge_o
        plot_h = plot_b - marge_b
        maxwaarde = max(abs(w) for _, w in data) or 1.0
        n = len(data)
        beschikbare = W - marge_l - 16
        balk = max(8, min(64, int(beschikbare / max(n, 1) * 0.72)))
        stap = max(balk + 6, int(beschikbare / max(n, 1)))
        for i, (label, waarde) in enumerate(data):
            h = max(2, int(plot_h * abs(waarde) / maxwaarde))
            x = marge_l + 8 + i * stap
            self.create_rectangle(x, plot_b - h, x + balk, plot_b,
                                  fill=KLEUR_GRAFIEK if i % 2 == 0 else KLEUR_GRAFIEK2,
                                  outline="")
            self.create_text(x + balk / 2, plot_b - h - 9, fill="#ddd",
                             font=("Helvetica", 9),
                             text=f"{waarde:,.0f}".replace(",", "."))
            lab = str(label)
            if len(lab) > 11:
                lab = lab[:10] + "…"
            self.create_text(x + balk / 2, plot_b + 10, fill="#bbb", width=balk + 14,
                             anchor="n", font=("Helvetica", 9), text=lab)
        self.create_rectangle(marge_l, marge_b, marge_l + 1, plot_b, fill="#555", outline="")
        self.create_rectangle(marge_l, plot_b, W - 8, plot_b + 1, fill="#555", outline="")
        self.create_text(marge_l - 6, marge_b + 4, fill="#999", anchor="ne",
                         font=("Helvetica", 9), text=metricnaam)


class DemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Apache Ossie demo — bloemenwebshop 'Knol & Bloei'")
        self.geometry("1180x760")
        ctk.set_appearance_mode("dark")

        self.modelpad = DEFAULT_MODEL
        self.dbpad = DEFAULT_DB
        self.model = None

        # ---------------------------------------------------------- kop
        kop = ctk.CTkFrame(self, corner_radius=0, fg_color="#16324a")
        kop.pack(fill="x")
        ctk.CTkLabel(kop, text="🌷  Knol & Bloei × Apache Ossie (incubating)",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)
        self.status = ctk.CTkLabel(kop, text="", text_color="#9fc9ec",
                                   font=ctk.CTkFont(size=12))
        self.status.pack(side="right", padx=16)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=8)
        self.tab_analyse = self.tabs.add("🔍 Analyseer")
        self.tab_vraag = self.tabs.add("🤖 Vraag via AI-context")
        self.tab_model = self.tabs.add("📄 Het Ossie-model")

        self._bouw_model_tab()
        self._bouw_analyse_tab()
        self._bouw_vraag_tab()
        self._herlaad_model()

    # ============================================================ MODEL
    def _bouw_model_tab(self):
        knoppen = ctk.CTkFrame(self.tab_model, fg_color="transparent")
        knoppen.pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(knoppen, text="Valideer model tegen de spec",
                      command=self._valideer).pack(side="left", padx=4)
        ctk.CTkButton(knoppen, text="Herlaad YAML", fg_color="#444",
                      command=self._herlaad_model).pack(side="left", padx=4)
        self.model_pad_lbl = ctk.CTkLabel(knoppen, text=DEFAULT_MODEL,
                                          text_color="#888", font=ctk.CTkFont(size=11))
        self.model_pad_lbl.pack(side="left", padx=12)

        splits = ctk.CTkFrame(self.tab_model, fg_color="transparent")
        splits.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        splits.grid_columnconfigure(0, weight=1)
        splits.grid_columnconfigure(1, weight=1)
        splits.grid_rowconfigure(0, weight=1)
        self.model_samenvatting = ctk.CTkTextbox(splits, font=ctk.CTkFont("Menlo", 12))
        self.model_samenvatting.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.model_yaml = ctk.CTkTextbox(splits, font=ctk.CTkFont("Menlo", 11))
        self.model_yaml.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

    def _herlaad_model(self):
        self.model = OssieModel(self.modelpad)
        metingen = sum(len(d.get("metrics") or []) for d in self.model.datasets.values())
        import sqlite3
        con = sqlite3.connect(self.dbpad)
        n_orders = con.execute("SELECT COUNT(*) FROM bestellingen").fetchone()[0]
        n_regels = con.execute("SELECT COUNT(*) FROM orderregels").fetchone()[0]
        con.close()
        self.status.configure(
            text=f"model '{self.model.name}' · {len(self.model.datasets)} datasets · "
                 f"{metingen} metrics · {len(self.model.relationships)} relaties · "
                 f"SQLite: {n_orders} bestellingen / {n_regels} regels")
        with open(self.modelpad, encoding="utf-8") as f:
            self.model_yaml.delete("1.0", "end")
            self.model_yaml.insert("1.0", f.read())
        self._toon_model_samenvatting()
        # dropdowns vullen
        self.cmb_metric.configure(values=[r for r, _, _ in self.model.alle_metrics()])
        self.cmb_dim.configure(values=["(geen — totaal)"] + self.model.alle_dimensies())
        self.cmb_metric.set("orderregels.omzet")
        self.cmb_dim.set("producten.categorie")
        self.txt_vraag.configure(placeholder_text="Bijv. " + "; ".join(
            (self.model.ai_context or {}).get("examples", ["omzet per categorie"])[:2]))

    def _toon_model_samenvatting(self, validatie=None):
        m = self.model
        regels = [f"Ossie-model: {m.name}   (spec v{m.version})\n{m.description}\n"]
        for dnaam, ds in m.datasets.items():
            regels.append(f"▸ dataset {dnaam}      [source: {ds['source']}]")
            for v in ds.get("fields") or []:
                dim = "⏰" if ((v.get("dimension") or {}).get("is_time")
                               or v.get("datatype") in ("Date", "Time", "DateTime", "DateTimeTz")) else "  "
                regels.append(f"    {dim} veld  {v['name']:<18} = {v['expression']['sql']}")
            for x in ds.get("metrics") or []:
                regels.append(f"    ∑  metric {x['name']:<18} = {x['expression']['sql']}")
            regels.append("")
        for r in m.relationships:
            regels.append(f"⟷ relatie {r['name']}: {r['from']} → {r['to']} "
                          f"({', '.join(r['from_columns'])} = {', '.join(r['to_columns'])})")
        regels.append("")
        for n, x in m.model_metrics.items():
            regels.append(f"∑  model-metric {n} = {x['expression']['sql']}")
        if validatie is not None:
            regels.append("\n=== VALIDATIE ===")
            for niveau, bericht in validatie:
                icoon = {"OK": "✓", "FOUT": "✗", "WARN": "!"}[niveau]
                regels.append(f"{icoon} {bericht}")
        self.model_samenvatting.delete("1.0", "end")
        self.model_samenvatting.insert("1.0", "\n".join(regels))

    def _valideer(self):
        self._toon_model_samenvatting(valideer(self.model))

    # ========================================================== ANALYSE
    def _bouw_analyse_tab(self):
        bediening = ctk.CTkFrame(self.tab_analyse)
        bediening.pack(fill="x", padx=8, pady=8)
        rows = ctk.CTkFrame(bediening, fg_color="transparent")
        rows.pack(fill="x", padx=8, pady=6)

        def lab(txt, x):
            ctk.CTkLabel(rows, text=txt, font=ctk.CTkFont(size=11, weight="bold")).grid(
                row=0, column=x, sticky="w", padx=(10, 2))

        lab("Metric (uit het Ossie-model)", 0)
        lab("Dimensie (groep op)", 1)
        lab("Top N", 2)
        self.cmb_metric = ctk.CTkOptionMenu(rows, width=230, values=[])
        self.cmb_metric.grid(row=1, column=0, padx=(10, 10))
        self.cmb_dim = ctk.CTkOptionMenu(rows, width=230, values=[])
        self.cmb_dim.grid(row=1, column=1, padx=10)
        self.cmb_top = ctk.CTkOptionMenu(rows, width=70, values=["5", "10", "12", "25"])
        self.cmb_top.set("12")
        self.cmb_top.grid(row=1, column=2, padx=10)
        self.sw_bezonegd = ctk.CTkSwitch(rows, text="alleen bezorgde bestellingen",
                                         font=ctk.CTkFont(size=11))
        self.sw_bezonegd.grid(row=1, column=3, padx=18)
        ctk.CTkButton(rows, text="▶ Genereer SQL & draai op SQLite",
                      command=self._run_query).grid(row=1, column=4, padx=10)
        rows.grid_columnconfigure((0, 1, 2, 3), weight=1)

        kw = ctk.CTkFrame(self.tab_analyse, corner_radius=8)
        kw.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        kw.grid_columnconfigure(0, weight=3)
        kw.grid_columnconfigure(1, weight=2)
        kw.grid_rowconfigure(0, weight=1)
        kw.grid_rowconfigure(1, weight=2)

        self.chart = BarChart(kw, width=440, height=250)
        self.chart.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(4, 8), pady=8)

        self.sql_box = ctk.CTkTextbox(kw, font=ctk.CTkFont("Menlo", 11))
        self.sql_box.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=(8, 4))
        self._toon_sql("Kies een metric en dimensie en druk op ▶ — de SQL wordt "
                       "uit het Ossie-model gecompileerd, er staat geen query in deze app.")

        tblframe = ctk.CTkFrame(kw, fg_color="transparent")
        tblframe.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(4, 8))
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#262626", fieldbackground="#262626",
                        foreground="#e6e6e6", rowheight=24, font=("Menlo", 11))
        style.configure("Treeview.Heading", background="#16324a", foreground="white",
                        font=("Menlo", 11, "bold"))
        self.tree = ttk.Treeview(tblframe, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tblframe, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

    def _toon_sql(self, sql):
        self.sql_box.delete("1.0", "end")
        self.sql_box.insert("1.0", sql)

    def _run_query(self):
        metric = self.cmb_metric.get()
        dim = None if self.cmb_dim.get().startswith("(") else self.cmb_dim.get()
        top = int(self.cmb_top.get())
        filters = ()
        if self.sw_bezonegd.get():
            filters = (("bestellingen", "bezorgd", "=", 1),)
        try:
            sql = self.model.compileer(metric, dim, filters=filters, top=top)
        except Exception as exc:
            self._toon_sql(f"❌ {exc}")
            return
        self._toon_sql(sql)
        kolommen, rijen = self.model.uitvoeren(self.dbpad, sql)
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=kolommen)
        for k in kolommen:
            self.tree.heading(k, text=k)
            self.tree.column(k, width=220 if kolommen.index(k) == 0 else 150,
                             anchor="w" if kolommen.index(k) == 0 else "e")
        except_data = []
        for r in rijen:
            self.tree.insert("", "end", values=[fmt_getal(c) for c in r])
            except_data.append((r[0], r[-1]))
        self.chart.draw(except_data if dim else [], metric.split(".")[-1])

    # ============================================================= VRAAG
    def _bouw_vraag_tab(self):
        frame = ctk.CTkFrame(self.tab_vraag)
        frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(frame, text="Stel een vraag in gewone taal — net zoals een BI-gebruiker of AI-agent dat zou doen.",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(frame,
                     text="De demo matcht je vraag op metrics/dimensies via `ai_context` (synoniemen & voorbeelden) uit het Ossie-model.\n"
                          "Een echte AI-agent gebruikt een LLM — maar leest dezelfde ai_context. Zo voorkomt Ossie hallucinaties door consistente definities.",
                     font=ctk.CTkFont(size=11), text_color="#aaa", justify="left").pack(anchor="w", padx=12)
        rij = ctk.CTkFrame(frame, fg_color="transparent")
        rij.pack(fill="x", padx=12, pady=8)
        self.txt_vraag = ctk.CTkEntry(rij, placeholder_text="Bijv. wat is de omzet per categorie?", height=36)
        self.txt_vraag.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.txt_vraag.bind("<Return>", lambda e: self._ask())
        ctk.CTkButton(rij, text="Zoek in model 🤖", width=150, command=self._ask).pack(side="left")
        self.voorbeeld_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=64)
        self.voorbeeld_scroll.pack(fill="x", padx=8, pady=(0, 8))

        self.vraag_result = ctk.CTkTextbox(self.tab_vraag, font=ctk.CTkFont("Menlo", 12))
        self.vraag_result.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.vraag_result.insert("1.0",
            "Voorbeeldvragen (klik op een knopje hierboven):\n"
            "  • wat is de omzet per categorie?\n"
            "  • hoeveel verkochte stuks per maand?\n"
            "  • gemiddelde orderwaarde per stad\n"
            "  • omzet per klant per segment\n"
            "  • gemiddelde korting per categorie\n")

    def _vul_voorbeelden(self):
        for w in self.voorbeeld_scroll.winfo_children():
            w.destroy()
        vragen = list((self.model.ai_context or {}).get("examples", []))
        vragen += ["wat is de omzet per categorie", "verkochte stuks per maand",
                   "gemiddelde korting per categorie", "wat is de omzet_per_klant"]
        for i, v in enumerate(dict.fromkeys(vragen)):
            ctk.CTkButton(self.voorbeeld_scroll, text=v, width=220,
                          fg_color="#2a4d68", hover_color="#3b8ed0",
                          command=lambda t=v: (self.txt_vraag.delete(0, "end"),
                                               self.txt_vraag.insert(0, t),
                                               self._ask())).grid(
                row=i // 4, column=i % 4, padx=4, pady=4, sticky="w")

    def _ask(self):
        vraag = self.txt_vraag.get().strip()
        if not vraag:
            return
        metric, dim, uitleg = self.model.match_vraag(vraag)
        self.vraag_result.delete("1.0", "end")
        if not metric:
            self.vraag_result.insert("1.0",
                f"❓ '{vraag}' — geen metric gevonden in het model.\n\n"
                "Tips: een AI-agent kan alleen antwoorden waar `ai_context`\n"
                "en metrics voor bestaan. Dit is precies waarom Ossie-modellen\n"
                "met goede ai_context zo belangrijk zijn voor betrouwbare AI.")
            return
        regels = [f"Vraag: {vraag}", "", "Herkend via ai_context uit het Ossie-model:"]
        for u in uitleg:
            regels.append(f"  • {u}")
        try:
            sql = self.model.compileer(metric, dim)
            kolommen, rijen = self.model.uitvoeren(self.dbpad, sql)
        except Exception as exc:
            self.vraag_result.insert("1.0", f"❌ {exc}")
            return
        regels += ["", "Gecompileerde SQL:", *[f"    {ln}" for ln in sql.splitlines()], "", "Antwoord:"]
        for r in rijen[:12]:
            regels.append("    " + "   ".join(fmt_getal(c) for c in r))
        regels += ["", "→ open het tabblad 'Analyseer' om dit als grafiek te zien."]
        self.vraag_result.insert("1.0", "\n".join(regels))
        # zet dezelfde selectie in de analyse-tab
        self.cmb_metric.set(metric)
        self.cmb_dim.set(dim if dim else "(geen — totaal)")
        self._run_query()


def main():
    if not os.path.exists(DEFAULT_DB):
        print("webshop.db niet gevonden — bouw hem eerst:\n"
              "  uv run python scripts/genereer_data.py && uv run python scripts/bouw_database.py")
        sys.exit(1)
    app = DemoApp()
    app._vul_voorbeelden()
    app.mainloop()


if __name__ == "__main__":
    main()
