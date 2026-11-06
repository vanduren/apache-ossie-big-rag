#!/usr/bin/env python3
"""Bouwt de SQLite-database data/webshop.db uit de CSV-bestanden in data/.

Run:  uv run python scripts/bouw_database.py
"""
import csv
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DB = os.path.join(DATA, "webshop.db")

SCHEMA = """
DROP TABLE IF EXISTS klanten;
DROP TABLE IF EXISTS producten;
DROP TABLE IF EXISTS bestellingen;
DROP TABLE IF EXISTS orderregels;

CREATE TABLE klanten (
    klant_id  INTEGER PRIMARY KEY,
    naam      TEXT NOT NULL,
    stad      TEXT NOT NULL,
    segment   TEXT NOT NULL
);

CREATE TABLE producten (
    product_id INTEGER PRIMARY KEY,
    naam       TEXT NOT NULL,
    categorie  TEXT NOT NULL,
    prijs      REAL NOT NULL
);

CREATE TABLE bestellingen (
    bestelling_id INTEGER PRIMARY KEY,
    klant_id      INTEGER NOT NULL REFERENCES klanten(klant_id),
    besteldatum   TEXT NOT NULL,          -- ISO-datum YYYY-MM-DD
    bezorgd       INTEGER NOT NULL
);

CREATE TABLE orderregels (
    bestelling_id  INTEGER NOT NULL REFERENCES bestellingen(bestelling_id),
    regel_nr       INTEGER NOT NULL,
    product_id     INTEGER NOT NULL REFERENCES producten(product_id),
    aantal         INTEGER NOT NULL,
    prijs_per_stuk REAL NOT NULL,
    korting        REAL NOT NULL,
    PRIMARY KEY (bestelling_id, regel_nr)
);

CREATE INDEX idx_bestellingen_klant ON bestellingen(klant_id);
CREATE INDEX idx_regels_product ON orderregels(product_id);
CREATE INDEX idx_regels_bestelling ON orderregels(bestelling_id);
"""

LADEN = [
    ("klanten.csv", "klanten", "INSERT INTO klanten VALUES (?,?,?,?)"),
    ("producten.csv", "producten", "INSERT INTO producten VALUES (?,?,?,?)"),
    ("bestellingen.csv", "bestellingen", "INSERT INTO bestellingen VALUES (?,?,?,?)"),
    ("orderregels.csv", "orderregels", "INSERT INTO orderregels VALUES (?,?,?,?,?,?)"),
]


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    for csvnaam, tabel, insert in LADEN:
        with open(os.path.join(DATA, csvnaam), encoding="utf-8") as f:
            rows = list(csv.reader(f))[1:]
            if tabel in ("producten",):
                rows = [(r[0], r[1], r[2], float(r[3])) for r in rows]
            elif tabel == "bestellingen":
                rows = [(r[0], r[1], r[2], int(r[3])) for r in rows]
            elif tabel == "orderregels":
                rows = [(r[0], r[1], r[2], int(r[3]), float(r[4]), float(r[5])) for r in rows]
            con.executemany(insert, rows)
            print(f"  {tabel}: {len(rows)} rijen geladen")
    con.commit()
    con.close()
    print(f"SQLite-database gebouwd: {DB}")


if __name__ == "__main__":
    main()
