#!/usr/bin/env python3
"""Genereert deterministic voorbeeld-CSV's voor de webshop "Knol & Bloei".

Run:  uv run python scripts/genereer_data.py
De CSV's in data/ zijn de voorbeeldbestanden; bouw_database.py maakt er SQLite van.
"""
import csv
import random
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

random.seed(42)  # deterministic: dezelfde demo elke run

STEDEN = ["Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Eindhoven",
          "Groningen", "Maastricht", "Leiden", "Haarlem", "Arnhem"]
VOORNAMEN = ["Jan", "Anna", "Pieter", "Sanne", "Willem", "Lisa", "Dirk",
             "Femke", "Bram", "Noor", "Kees", "Julia", "Sjoerd", "Renske",
             "Thijs", "Lieke", "Aad", "Maud", "Guus", "Eva"]
ACHTERNAMEN = ["de Vries", "Jansen", "van Dijk", "Bakker", "Visser", "Smit",
               "Meijer", "de Boer", "Mulder", "de Groot", "Bos", "Vos",
               "Peters", "Hendriks", "van Leeuwen", "Dekker", "Brouwer",
               "de Wit", "Dijkstra", "Vermeer"]

PRODUCTEN = [
    # (naam, categorie, prijs)
    ("Tulp 'Paul Scherer' (25 bollen)", "bollen", 7.50),
    ("Narcis 'Baby Jean' (25 bollen)", "bollen", 6.25),
    ("Hyacint 'Pink Pearl' (3 stuks)", "bollen", 8.95),
    ("Krokus-mix (50 bollen)", "bollen", 9.95),
    ("Zonnebloem 'Giant Russian' (zaden)", "zaden", 3.50),
    ("Zoete erwt 'Spencer' (zaden)", "zaden", 2.95),
    ("Grasmix weidebloemen (1 kg)", "zaden", 12.50),
    ("Rozen 'Avalanche' (10 stengels)", "snijbloemen", 14.95),
    ("Tulpenboeket gemengd (15 stengels)", "snijbloemen", 11.50),
    ("Zonnebloemboeket (5 stengels)", "snijbloemen", 9.75),
    ("Gerbera 'Mini Mix' (10 stengels)", "snijbloemen", 8.50),
    ("Lelies 'Orient' (5 stengels)", "snijbloemen", 13.25),
    ("Orchidee Phalaenopsis (1 pot)", "kamerplanten", 24.95),
    ("Monstera Deliciosa (M-pot)", "kamerplanten", 29.95),
    ("Sansevieria (M-pot)", "kamerplanten", 19.95),
    ("Vetplanten assortiment (3 stuks)", "kamerplanten", 12.95),
    ("Kalenderjaarloos bloemenpakket", "abonnementen", 49.95),
    ("Proefabonnement wekelijks", "abonnementen", 27.50),
    ("Vaas 'Delfts Blauw' (30 cm)", "accessoires", 17.95),
    ("Snoeischaar professioneel", "accessoires", 22.50),
    ("Bloempot terracotta (set van 3)", "accessoires", 15.95),
    ("Kompost 20 liter", "accessoires", 8.95),
]

KLANTEN = []
for i in range(1, 41):
    naam = f"{random.choice(VOORNAMEN)} {random.choice(ACHTERNAMEN)}"
    stad = random.choice(STEDEN)
    segment = "zakelijk" if random.random() < 0.25 else "particulier"
    KLANTEN.append((i, naam, stad, segment))


def schrijf(naam, koppen, rijen):
    pad = os.path.join(DATA, naam)
    with open(pad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(koppen)
        w.writerows(rijen)
    print(f"  {pad}  ({len(rijen)} rijen)")


def main():
    # klanten.csv
    schrijf("klanten.csv",
            ["klant_id", "naam", "stad", "segment"], KLANTEN)

    # producten.csv
    schrijf("producten.csv",
            ["product_id", "naam", "categorie", "prijs"],
            [(i, n, c, f"{p:.2f}") for i, (n, c, p) in enumerate(PRODUCTEN, 1)])

    # bestellingen.csv + orderregels.csv (1 juni 2025 t/m oktober 2026)
    start, einde = date(2025, 6, 1), date(2026, 10, 31)
    dagen = (einde - start).days
    bestellingen, regels = [], []
    bestel_id = 0
    for _ in range(320):
        bestel_id += 1
        d = start + timedelta(days=random.randint(0, dagen))
        # seizoenspiek: bolletijd (okt-dec) en voorjaar (mrt-mei) drukker
        if d.month in (3, 4, 5, 10, 11, 12) and random.random() < 0.35:
            d = d.replace(month=random.choice([3, 4, 10, 11]))
        klant = random.choice(KLANTEN)
        bezorgd = 1 if random.random() < 0.93 else 0
        bestellingen.append((bestel_id, klant[0], d.isoformat(), bezorgd))
        for regel_nr in range(1, random.randint(1, 3) + 1):
            p = random.randint(1, len(PRODUCTEN))
            prijs = PRODUCTEN[p - 1][2]
            aantal = random.choices([1, 2, 3, 4, 5, 10], weights=[50, 25, 12, 6, 4, 3])[0]
            korting = random.choice([0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20])
            regels.append((bestel_id, regel_nr, p, aantal, f"{prijs:.2f}", f"{korting:.2f}"))

    schrijf("bestellingen.csv",
            ["bestelling_id", "klant_id", "besteldatum", "bezorgd"], bestellingen)
    schrijf("orderregels.csv",
            ["bestelling_id", "regel_nr", "product_id", "aantal", "prijs_per_stuk", "korting"], regels)

    print("Klaar. Bouw nu de SQLite-database met:  uv run python scripts/bouw_database.py")


if __name__ == "__main__":
    main()
