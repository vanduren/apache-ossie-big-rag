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
DROP TABLE IF EXISTS beoordelingen;
DROP TABLE IF EXISTS verzendingen;
DROP TABLE IF EXISTS orderregels;
DROP TABLE IF EXISTS bestellingen;
DROP TABLE IF EXISTS producten;
DROP TABLE IF EXISTS leveranciers;
DROP TABLE IF EXISTS klanten;

CREATE TABLE klanten (
    klant_id  INTEGER PRIMARY KEY,
    naam      TEXT NOT NULL,
    stad      TEXT NOT NULL,
    segment   TEXT NOT NULL
);

CREATE TABLE leveranciers (
    leverancier_id  INTEGER PRIMARY KEY,
    naam            TEXT NOT NULL,
    land            TEXT NOT NULL,
    levertijd_dagen INTEGER NOT NULL
);

CREATE TABLE producten (
    product_id     INTEGER PRIMARY KEY,
    naam           TEXT NOT NULL,
    categorie      TEXT NOT NULL,
    prijs          REAL NOT NULL,
    inkoopprijs    REAL NOT NULL,
    leverancier_id INTEGER NOT NULL REFERENCES leveranciers(leverancier_id)
);

CREATE TABLE bestellingen (
    bestelling_id INTEGER PRIMARY KEY,
    klant_id      INTEGER NOT NULL REFERENCES klanten(klant_id),
    besteldatum   TEXT NOT NULL,          -- ISO-datum YYYY-MM-DD
    bezorgd       INTEGER NOT NULL,
    bestelbron    TEXT NOT NULL           -- website / mobiele app / e-mail
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

CREATE TABLE verzendingen (
    verzending_id  INTEGER PRIMARY KEY,
    bestelling_id  INTEGER NOT NULL UNIQUE REFERENCES bestellingen(bestelling_id),
    bezorger       TEXT NOT NULL,
    verzendkosten  REAL NOT NULL,
    verzend_datum  TEXT NOT NULL,         -- ISO-datum YYYY-MM-DD
    levertijd_dagen INTEGER NOT NULL
);

CREATE TABLE beoordelingen (
    beoordeling_id INTEGER PRIMARY KEY,
    klant_id       INTEGER NOT NULL REFERENCES klanten(klant_id),
    product_id     INTEGER NOT NULL REFERENCES producten(product_id),
    sterren        INTEGER NOT NULL,      -- 1..5
    beoordeeld_op  TEXT NOT NULL          -- ISO-datum YYYY-MM-DD
);

CREATE INDEX idx_bestellingen_klant ON bestellingen(klant_id);
CREATE INDEX idx_regels_product ON orderregels(product_id);
CREATE INDEX idx_regels_bestelling ON orderregels(bestelling_id);
CREATE INDEX idx_producten_leverancier ON producten(leverancier_id);
CREATE INDEX idx_verzendingen_bestelling ON verzendingen(bestelling_id);
CREATE INDEX idx_beoordelingen_product ON beoordelingen(product_id);
CREATE INDEX idx_beoordelingen_klant ON beoordelingen(klant_id);
"""

LADEN = [
    ("klanten.csv", "klanten", "INSERT INTO klanten VALUES (?,?,?,?)",
     lambda r: (r[0], r[1], r[2], r[3])),
    ("leveranciers.csv", "leveranciers", "INSERT INTO leveranciers VALUES (?,?,?,?)",
     lambda r: (r[0], r[1], r[2], int(r[3]))),
    ("producten.csv", "producten", "INSERT INTO producten VALUES (?,?,?,?,?,?)",
     lambda r: (r[0], r[1], r[2], float(r[3]), float(r[4]), r[5])),
    ("bestellingen.csv", "bestellingen", "INSERT INTO bestellingen VALUES (?,?,?,?,?)",
     lambda r: (r[0], r[1], r[2], int(r[3]), r[4])),
    ("orderregels.csv", "orderregels", "INSERT INTO orderregels VALUES (?,?,?,?,?,?)",
     lambda r: (r[0], r[1], r[2], int(r[3]), float(r[4]), float(r[5]))),
    ("verzendingen.csv", "verzendingen", "INSERT INTO verzendingen VALUES (?,?,?,?,?,?)",
     lambda r: (r[0], r[1], r[2], float(r[3]), r[4], int(r[5]))),
    ("beoordelingen.csv", "beoordelingen", "INSERT INTO beoordelingen VALUES (?,?,?,?,?)",
     lambda r: (r[0], r[1], r[2], int(r[3]), r[4])),
]


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    for csvnaam, tabel, insert, cast in LADEN:
        with open(os.path.join(DATA, csvnaam), encoding="utf-8") as f:
            rows = [cast(r) for r in list(csv.reader(f))[1:]]
            con.executemany(insert, rows)
            print(f"  {tabel}: {len(rows)} rijen geladen")
    con.commit()
    con.close()
    print(f"SQLite-database gebouwd: {DB}")


if __name__ == "__main__":
    main()
