#!/usr/bin/env python3
"""ossie_core.py — een minimale, zelfstandige "consumer" van Apache Ossie.

Doe wat een BI-tool of AI-agent met een Ossie-model zou doen:
  1. een .ossie.yaml-model inlezen   (Core Metadata Specification 0.2.0.dev0)
  2. het valideren tegen de kernregels van de specificatie
  3. metrics + dimensies compileren naar SQLite-SQL (name resolution volgens de spec)
  4. vragen-matchen via ai_context (synoniemen/voorbeelden) — "AI-ready context"

Dit bestand is bewust losgekoppeld van de UI, zodat CLI, tests en de
CustomTkinter-app exact dezelfde compiler logica delen: één model, vele tools.
"""
from __future__ import annotations

import os
import re
import sqlite3
from collections import deque

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL = os.path.join(ROOT, "models", "knol_en_bloei.ossie.yaml")
DEFAULT_DB = os.path.join(ROOT, "data", "webshop.db")

# --------------------------------------------------------------------------
# Woordsoorten die nooit naar een kolom hoeven te worden "ontleed"
# --------------------------------------------------------------------------
KEYWORDS = {
    "sum", "count", "avg", "min", "max", "distinct", "case", "when", "then",
    "else", "end", "and", "or", "not", "null", "as", "cast", "text", "integer",
    "real", "date", "source",
}
FUNCTIONS = {
    "substr", "substring", "round", "coalesce", "ifnull", "abs", "lower",
    "upper", "length", "strftime", "total",
}
# Vulstofdheid die nooit een synoniem-matching "mag" winnen (losstaat hij in
# geen enkele definitie; in een vraag hoort hij nergens bij)
STOPWORDS = {
    "de", "het", "een", "in", "van", "op", "aan", "is", "zijn", "of", "en",
    "dat", "dit", "er", "als", "maar", "ook", "nog", "voor", "met", "bij",
    "uit", "te", "bijna", "eens",
}

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _bron_tabel(source: str) -> str:
    """Los `database.schema.tabel` op naar de fysieke tabelnaam.

    SQLite kent geen schemas; de consumer gebruikt het laatste deel.
    (Name resolution: `source` verwijst naar de onderliggende tabel/view.)
    """
    return source.split(".")[-1].strip('"`')


class OssieModel:
    """In-memory weergave van één Ossie semantic model (één document = één model)."""

    def __init__(self, path: str):
        self.path = path
        with open(path, encoding="utf-8") as f:
            self.doc = yaml.safe_load(f)
        self.version = self.doc.get("version")
        self.name = self.doc.get("name", "?")
        self.description = self.doc.get("description", "")
        self.ai_context = self.doc.get("ai_context", "")
        self.datasets = {d["name"]: d for d in self.doc.get("datasets", [])}
        self.relationships = self.doc.get("relationships", []) or []
        self.model_metrics = {m["name"]: m for m in self.doc.get("metrics", []) or []}

    # ------------------------------------------------------------ lookup
    def dataset(self, naam):
        return self.datasets[naam]

    def field(self, dataset_naam, veld_naam):
        for veld in self.datasets[dataset_naam].get("fields", []) or []:
            if veld["name"] == veld_naam:
                return veld
        raise KeyError(f"veld {dataset_naam}.{veld_naam} niet gevonden")

    def find_metric(self, ref: str):
        """Zoek metric op referentie: 'omzet_per_klant' (model) of 'orderregels.omzet' (dataset)."""
        if "." in ref:
            ds, naam = ref.split(".", 1)
            for m in self.datasets.get(ds, {}).get("metrics", []) or []:
                if m["name"] == naam:
                    return "dataset", ds, m
        if ref in self.model_metrics:
            return "model", None, self.model_metrics[ref]
        for dnaam, ds in self.datasets.items():
            for m in ds.get("metrics", []) or []:
                if m["name"] == ref:
                    return "dataset", dnaam, m
        raise KeyError(f"metric {ref} niet gevonden")

    def alle_metrics(self):
        """Lijst van (referentie, metric, dataset_of_None) — gesorteerd op referentie."""
        refs = [(m["name"], m, None) for m in self.model_metrics.values()]
        for dnaam, ds in self.datasets.items():
            refs += [(f"{dnaam}.{m['name']}", m, dnaam) for m in ds.get("metrics", []) or []]
        return sorted(refs, key=lambda r: r[0])

    def alle_dimensies(self):
        """Lijst van 'dataset.veld' referenties, tijd-dimensies eerst."""
        uit = []
        for dnaam, ds in self.datasets.items():
            for veld in ds.get("fields", []) or []:
                dim = veld.get("dimension") or {}
                is_time = dim.get("is_time")
                if is_time is None:  # default volgens de spec: temporeel datatype
                    is_time = veld.get("datatype") in ("Date", "Time", "DateTime", "DateTimeTz")
                uit.append((not is_time, f"{dnaam}.{veld['name']}", veld))
        return [r[1] for r in sorted(uit)]

    # ------------------------------------------------- name resolution
    def veld_expr(self, dataset_naam, veld_naam, alias=None):
        """Compileer één veld naar SQL met kolomvoorzetsel van de dataset-alias.

        Identifiers in een veld-expressie verwijzen naar kolommen van de
        `source` van die dataset (spec § Name Resolution).
        """
        veld = self.field(dataset_naam, veld_naam)
        if alias is None:
            alias = dataset_naam
        expr = (veld.get("expression") or {}).get("sql", "")

        def vervang(m):
            ident = m.group(0)
            nxt = expr[m.end():m.end() + 1]
            if ident.lower() in FUNCTIONS or nxt == "(":
                return ident
            if ident.lower() in KEYWORDS:
                return ident
            return f"{alias}.{ident}"

        return "(" + _IDENT.sub(vervang, expr) + ")"

    def metric_expr(self, scope, dataset_naam, metric):
        """Compileer een metric-expressie; scope = 'dataset' of 'model'.

        Eén regex-pass over de hele expressie (geen her-verwerking van
        eerdere vervangingen), conform § Name Resolution:
        - dataset-scope:  `source.kolom` → `alias.kolom`;
                          kale namen → expressie van het eigen veld
        - model-scope:    `dataset.veld` → expandede, gekwalificeerde expressie
        """
        expr = (metric.get("expression") or {}).get("sql", "")

        def is_call(i, ident):
            nxt = expr[i + len(ident):i + len(ident) + 1]
            return ident.lower() in FUNCTIONS or nxt == "("

        if scope == "model":
            pat = re.compile(r"([A-Za-z_]\w*)\.([A-Za-z_]\w*)|([A-Za-z_]\w*)")

            def rep(m):
                if m.group(1):
                    ds, v = m.group(1), m.group(2)
                    if ds in self.datasets:
                        return self.veld_expr(ds, v)
                    return m.group(0)
                ident = m.group(3)
                return ident  # kale namen zijn in model-scope ongeldig; valideer meldt ze
            return pat.sub(rep, expr)

        alias = dataset_naam
        pat = re.compile(r"(?i)\bsource\.([A-Za-z_]\w*)|([A-Za-z_]\w*)")

        def rep(m):
            if m.group(1):
                return f"{alias}.{m.group(1)}"       # source.kolom
            ident = m.group(2)
            if ident.lower() in KEYWORDS or is_call(m.start(2), ident):
                return ident
            return self.veld_expr(alias, ident)      # eigen veld → expressie
        return pat.sub(rep, expr)

    # ------------------------------------------------------------ joins
    def _rel_graph(self):
        g = {dnaam: [] for dnaam in self.datasets}
        for rel in self.relationships:
            g[rel["from"]].append((rel["to"], rel))
            g[rel["to"]].append((rel["from"], rel))
        return g

    def pad(self, start, doel):
        """Kortstepad over relaties (BFS) → lijst van relationships."""
        if start == doel:
            return []
        g = self._rel_graph()
        vorig = {start: None}
        rij = deque([start])
        while rij:
            knoop = rij.popleft()
            for buur, rel in g.get(knoop, []):
                if buur not in vorig:
                    vorig[buur] = (knoop, rel)
                    if buur == doel:
                        pad, cur = [], buur
                        while vorig[cur] is not None:
                            prev, rel = vorig[cur]
                            pad.append(rel)
                            cur = prev
                        return list(reversed(pad))
                    rij.append(buur)
        raise ValueError(f"geen relatiepad tussen {start} en {doel}")

    # ------------------------------------------------------------ query
    def compileer(self, metric_ref, dim_ref=None, filters=(), top=25):
        """Bouw SQLite-SQL voor één metric (+ optioneel één dimensie + filters).

        Dit is exact wat elke Ossie-consumer (BI-tool, AI-agent) doet:
        veldnamen vervangen door hun expressies, joins via relationships.
        """
        scope, dnaam, metric = self.find_metric(metric_ref)
        benodigd = set()
        mexpr = self.metric_expr(scope, dnaam, metric)
        if scope == "model":
            for ds in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.[A-Za-z_][A-Za-z0-9_]*",
                                 (metric.get("expression") or {}).get("sql", "")):
                if ds in self.datasets:
                    benodigd.add(ds)
            anchor = sorted(benodigd)[0]
        else:
            anchor = dnaam
            benodigd.add(anchor)

        joins = []      # (tabel, alias, on)
        aliasen = {anchor}
        if dim_ref:
            dds, dv = dim_ref.split(".", 1)
            dim_expr = self.veld_expr(dds, dv)
            if dds not in aliasen:
                for rel in self.pad(anchor, dds):
                    a, b = rel["from"], rel["to"]
                    if a in aliasen and b not in aliasen:
                        van, tot = a, b
                    elif b in aliasen and a not in aliasen:
                        van, tot = b, a
                    else:
                        continue
                    on = " AND ".join(
                        f"{self.veld_expr(van, fc)} = {self.veld_expr(tot, tc)}"
                        for fc, tc in zip(rel["from_columns"], rel["to_columns"]))
                    joins.append((_bron_tabel(self.datasets[tot]["source"]), tot, on))
                    aliasen.add(tot)
                benodigd.add(dds)
        else:
            dim_expr = None

        # extra datasets uit de model-metric refs joennen
        for target in sorted(benodigd - aliasen):
            for rel in self.pad(anchor, target):
                a, b = rel["from"], rel["to"]
                if a in aliasen and b not in aliasen:
                    van, tot = a, b
                elif b in aliasen and a not in aliasen:
                    van, tot = b, a
                else:
                    continue
                on = " AND ".join(
                    f"{self.veld_expr(van, fc)} = {self.veld_expr(tot, tc)}"
                    for fc, tc in zip(rel["from_columns"], rel["to_columns"]))
                joins.append((_bron_tabel(self.datasets[tot]["source"]), tot, on))
                aliasen.add(tot)

        where = []
        for f in filters:
            fds, fv, operator, waarde = f
            where.append(f"{self.veld_expr(fds, fv)} {operator} {waarde}")

        sql = "SELECT "
        if dim_expr:
            sql += f"{dim_expr} AS \"dimensie\",\n       "
        sql += f"{mexpr} AS \"{metric['name']}\"\n"
        sql += f"FROM {_bron_tabel(self.datasets[anchor]['source'])} AS {anchor}"
        for tabel, alias, on in joins:
            sql += f"\nJOIN {tabel} AS {alias} ON {on}"
        if where:
            sql += "\nWHERE " + " AND ".join(where)
        if dim_expr:
            sql += f"\nGROUP BY 1\nORDER BY 2 DESC\nLIMIT {int(top)}"
        return sql

    def uitvoeren(self, db_path, sql):
        con = sqlite3.connect(db_path)
        try:
            cur = con.execute(sql)
            kolommen = [d[0] for d in cur.description]
            return kolommen, cur.fetchall()
        finally:
            con.close()

    # --------------------------------------------------------- AI-match
    def match_vraag(self, vraag: str):
        """Zeer eenvoudige 'agent': match een NL-vraag op metrics/dimensies via ai_context.

        Een echte AI-agent gebruikt een LLM; het punt van Ossie is dat de
        semantische ankerpunten (synoniemen, voorbeelden, instructies) uit
        ditzelfde model komen.
        """
        t = vraag.lower()
        words = set(re.findall(r"[a-zäëïöüéèê]+", t)) - STOPWORDS

        def score(woorden, naam, ctx):
            kandidaten = {naam.lower().replace("_", " "), naam.lower()}
            synoniemen = []
            if isinstance(ctx, dict):
                synoniemen = [s.lower() for s in ctx.get("synonyms", [])]
            elif isinstance(ctx, str):
                synoniemen = [s.strip().lower() for s in ctx.split(",")]
            punten = 0.0
            for k in kandidaten | set(synoniemen):
                if k and k in t:
                    punten = max(punten, 1.0 + len(k) / 100.0)
                else:
                    overlap = words & set(k.split())
                    if overlap:
                        punten = max(punten, 0.6 + len(overlap) / 100.0)
            return punten

        beste_metric, beste_metric_score, beste_metric_ctx = None, 0.0, None
        for ref, m, ds in self.alle_metrics():
            s = score(words, m["name"], m.get("ai_context", ""))
            if s > beste_metric_score:
                beste_metric, beste_metric_score, beste_metric_ctx = ref, s, m.get("ai_context")

        beste_dim, beste_dim_score, beste_dim_ctx = None, 0.0, None
        for ref in self.alle_dimensies():
            dds, dv = ref.split(".", 1)
            veld = self.field(dds, dv)
            s = score(words, dv, veld.get("ai_context", ""))
            if s > beste_dim_score:
                beste_dim, beste_dim_score, beste_dim_ctx = ref, s, veld.get("ai_context")

        if beste_metric_score < 0.5:
            return None, None, []
        if beste_dim_score < 0.5:
            beste_dim = None

        uitleg = []
        if beste_metric_ctx:
            uitleg.append(f"Metric `{beste_metric}` — ai_context.synonyms: {self._syn(beste_metric_ctx)}")
        if beste_dim:
            uitleg.append(f"Dimensie `{beste_dim}` — ai_context.synonyms: {self._syn(beste_dim_ctx)}")
        return beste_metric, beste_dim, uitleg

    @staticmethod
    def _syn(ctx):
        if isinstance(ctx, dict):
            return ", ".join(ctx.get("synonyms", [])[:5])
        return str(ctx)


# --------------------------------------------------------------------------
# Validatie tegen de kernregels van de Core Metadata Specification
# --------------------------------------------------------------------------
def valideer(model: OssieModel):
    """Geeft een lijst (niveau, bericht) —niveau ∈ {OK, FOUT, WARN}."""
    uit = []

    def ok(b):
        uit.append(("OK", b))

    def fout(b):
        uit.append(("FOUT", b))

    def warn(b):
        uit.append(("WARN", b))

    if model.doc.get("version"):
        ok(f"`version` aanwezig: {model.version}")
    else:
        fout("`version` ontbreekt (verplicht veld)")
    if model.doc.get("name"):
        ok(f"`name` aanwezig: {model.name}")
    else:
        fout("`name` ontbreekt (verplicht veld)")
    if model.datasets:
        ok(f"`datasets` niet-leeg ({len(model.datasets)} dataset(s))")
    else:
        fout("`datasets` ontbreekt of is leeg (verplicht, niet-leeg)")

    for dnaam, ds in model.datasets.items():
        if not ds.get("source"):
            fout(f"dataset {dnaam}: `source` ontbreekt (verplicht)")
        namen = [f["name"] for f in ds.get("fields", []) or []]
        mnamen = [m["name"] for m in ds.get("metrics", []) or []]
        dub = set(n for n in namen + mnamen if (namen + mnamen).count(n) > 1)
        if dub:
            fout(f"dataset {dnaam}: dubbele namen in velden/metrics: {sorted(dub)}")
        else:
            ok(f"dataset {dnaam}: {len(namen)} velden + {len(mnamen)} dataset-metrics, namen uniek")
        for pk in (ds.get("primary_key") or []) + [k for group in (ds.get("unique_keys") or []) for k in group]:
            if pk not in namen:
                fout(f"dataset {dnaam}: primary/unique key {pk} is geen gedeclareerd veld")
        # dataset-scoped metrics: alleen eigen velden of source.kolommen
        pat = re.compile(r"(?i)\bsource\.[A-Za-z_]\w*|([A-Za-z_]\w*)\.([A-Za-z_]\w*)|([A-Za-z_]\w*)")
        for m in ds.get("metrics", []) or []:
            expr = (m.get("expression") or {}).get("sql", "")
            for mq in pat.finditer(expr):
                if mq.group(0).lower().startswith("source."):
                    continue  # source.kolom = bronkolom, in dataset-scope gewoon toegestaan
                if mq.group(1):  # gekwalificeerde verwijzing → dat is model-scope
                    fout(f"metric {dnaam}.{m['name']}: `{mq.group(1)}.{mq.group(2)}` is gekwalificeerd; "
                         f"dataset-metrics mogen alleen eigen velden of source.kolom gebruiken")
                    continue
                ident = mq.group(3)
                nxt = expr[mq.end():mq.end() + 1]
                if ident.lower() in KEYWORDS or ident.lower() in FUNCTIONS or nxt == "(":
                    continue
                if ident not in namen:
                    fout(f"metric {dnaam}.{m['name']}: `{ident}` is geen veld van {dnaam} "
                         f"(bronkolommen moeten als source.kolom geschreven worden)")

    for rel in model.relationships:
        f, t = rel.get("from"), rel.get("to")
        if f not in model.datasets or t not in model.datasets:
            fout(f"relationship {rel.get('name')}: from/to onbekende dataset")
            continue
        if len(rel.get("from_columns", [])) != len(rel.get("to_columns", [])):
            fout(f"relationship {rel['name']}: from_columns en to_columns even lang")
        for kant, ds in (("from_columns", f), ("to_columns", t)):
            for veldref in rel.get(kant, []):
                try:
                    model.field(ds, veldref)
                except KeyError:
                    fout(f"relationship {rel['name']}: {kant} → {ds}.{veldref} is geen veld")
        ok(f"relationship {rel['name']}: {f} → {t} OK (vellden verwijzen naar gedeclareerde velden)")

    for mname, m in model.model_metrics.items():
        expr = (m.get("expression") or {}).get("sql", "")
        refs = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", expr)
        fout_ref = False
        for ds, v in refs:
            if ds not in model.datasets:
                fout(f"model-metric {mname}: onbekende dataset {ds}")
                fout_ref = True
            else:
                try:
                    model.field(ds, v)
                except KeyError:
                    fout(f"model-metric {mname}: {ds}.{v} is geen veld")
                    fout_ref = True
        if not refs and expr:
            fout(f"model-metric {mname}: model-scope expressies moeten dataset.veld gebruiken")
            fout_ref = True
        if not fout_ref:
            ok(f"model-metric {mname}: alle referenties zijn dataset.veld en bestaan")

    if model.doc.get("ai_context"):
        ok("ai_context aanwezig op model (goed voor AI-agents)")
    else:
        warn("geen ai_context op model-niveau")
    return uit
