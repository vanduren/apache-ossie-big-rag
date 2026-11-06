#!/usr/bin/env python3
"""CLI-demo: draag een Ossie-vraag over via het semantische model.

Voorbeelden:
    uv run python scripts/cli_vraag.py "omzet"
    uv run python scripts/cli_vraag.py "wat is de omzet per categorie"
    uv run python scripts/cli_vraag.py "verkochte stuks per maand"
    uv run python scripts/cli_vraag.py "gemiddelde orderwaarde per stad"
    uv run python scripts/cli_vraag.py --leg uit              # model + validatie
    uv run python scripts/cli_vraag.py --sql --vraag "omzet per product"

Of zonder AI-match, met expliciete referenties:
    uv run python scripts/cli_vraag.py --metric orderregels.omzet --dimensie producten.categorie
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from ossie_core import OssieModel, valideer, DEFAULT_MODEL, DEFAULT_DB  # noqa: E402


def toon(kolommen, rijen):
    breed = [len(k) for k in kolommen]
    text = [[f"{r[i]:.2f}" if isinstance(r[i], float) else str(r[i]) for i in range(len(r))] for r in rijen]
    for row in text:
        for i, c in enumerate(row):
            breed[i] = max(breed[i], len(c))
    print("  " + "  ".join(k.ljust(breed[i]) for i, k in enumerate(kolommen)))
    print("  " + "  ".join("-" * b for b in breed))
    for row in text:
        print("  " + "  ".join(c.rjust(breed[i]) if i else c for i, c in enumerate(row)))


def toon_model(model):
    print(f"\n=== Ossie-model: {model.name} (versie {model.version}) ===")
    print(model.description)
    for dnaam, ds in model.datasets.items():
        print(f"\n  dataset {dnaam}  [source: {ds['source']}]")
        print(f"    velden : {', '.join(f['name'] for f in ds.get('fields') or [])}")
        print(f"    metrics: {', '.join(m['name'] for m in ds.get('metrics') or [])}")
    print(f"\n  relaties : {', '.join(r['name'] for r in model.relationships)}")
    print(f"  model-metrics: {', '.join(model.model_metrics) or '(geen)'}")
    print("\n  === validatie tegen de kernregels van de spec ===")
    for niveau, bericht in valideer(model):
        icoon = {"OK": "✓", "FOUT": "✗", "WARN": "!"}[niveau]
        print(f"    {icoon} [{niveau}] {bericht}")


def main():
    ap = argparse.ArgumentParser(description="Apache Ossie CLI-demo (Knol & Bloei)")
    ap.add_argument("vraag", nargs="?", help="vraag in gewone taal, bijv. 'omzet per categorie'")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--metric", help="expliciete metric-referentie, bijv. orderregels.omzet")
    ap.add_argument("--dimensie", help="expliciete dimensie, bijv. producten.categorie")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--sql", action="store_true", help="toon de gecompileerde SQL")
    ap.add_argument("--alleen-sql", action="store_true")
    ap.add_argument("--leg", action="store_true", help="toon model + validatie")
    args = ap.parse_args()

    model = OssieModel(args.model)
    if args.leg:
        toon_model(model)
        return

    if args.metric:
        metric, dim, uitleg = args.metric, args.dimensie, []
    else:
        if not args.vraag:
            ap.error("geef een vraag, of --metric/--dimensie, of --leg")
        metric, dim, uitleg = model.match_vraag(args.vraag)
        if not metric:
            print(f"Kon in '{args.vraag}' geen metric herkennen. Probeer bijv.:")
            for ref, m, _ in model.alle_metrics():
                print(f"  - {ref}: {m.get('description', '')}")
            sys.exit(1)

    if not args.alleen_sql:
        toon_model(model)
        print(f"\n=== Vraag: {args.vraag or (metric + (' per ' + dim if dim else ''))} ===")
        for regel in uitleg:
            print(f"  (herkend via ai_context) {regel}")

    sql = model.compileer(metric, dim, top=args.top)
    print("\n--- gecompileerde SQL (door de Ossie-consumer, niet handmatig geschreven) ---")
    print(sql)
    if args.alleen_sql:
        return

    kolommen, rijen = model.uitvoeren(args.db, sql)
    print("\n--- resultaat uit SQLite (data/webshop.db) ---")
    toon(kolommen, rijen)


if __name__ == "__main__":
    main()
