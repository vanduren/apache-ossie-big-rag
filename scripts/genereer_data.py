#!/usr/bin/env python3
"""Genereert deterministic voorbeeld-CSV's voor de webshop "Knol & Bloei".

Run:  uv run python scripts/genereer_data.py
De CSV's in data/ zijn de voorbeeldbestanden; bouw_database.py maakt er SQLite van.

Entiteiten: klanten, leveranciers, producten, bestellingen, orderregels,
verzendingen en beoordelingen — met grotere opvoeringen dan de oorspronkelijke
demo (zaad 42 blijft de bron van alle herleidbaarheid).
"""
import csv
import os
import random
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

random.seed(42)  # deterministic: dezelfde demo elke run

AANTAL_KLANTEN = 150
AANTAL_BESTELLINGEN = 1800
AANTAL_BEOORDELINGEN = 1100

STEDEN = ["Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Eindhoven",
          "Groningen", "Maastricht", "Leiden", "Haarlem", "Arnhem",
          "Amersfoort", "Breda", "Nijmegen", "Zwolle", "Almere", "Leuwarden"]
VOORNAMEN = ["Jan", "Anna", "Pieter", "Sanne", "Willem", "Lisa", "Dirk",
             "Femke", "Bram", "Noor", "Kees", "Julia", "Sjoerd", "Renske",
             "Thijs", "Lieke", "Aad", "Maud", "Guus", "Eva",
             "Daan", "Lotte", "Mila", "Luuk", "Floor", "Ruben", "Sem",
             "Tess", "Guusje", "Fleur", "Jesse", "Sasker"]
ACHTERNAMEN = ["de Vries", "Jansen", "van Dijk", "Bakker", "Visser", "Smit",
               "Meijer", "de Boer", "Mulder", "de Groot", "Bos", "Vos",
               "Peters", "Hendriks", "van Leeuwen", "Dekker", "Brouwer",
               "de Wit", "Dijkstra", "Vermeer", "Kuiper", "Hofman", "Post",
               "Driessen", "Kok", "Peeters", "Crombach", "Willems", "Roos",
               "Zandbergen"]

# (leverancier_id, naam, land, levertijd in dagen)
LEVERANCIERS = [
    (1, "Bolhub B.V.", "Nederland", 2),
    (2, "Kwekerij 't Gooi", "Nederland", 3),
    (3, "Zadenhuis de Akker", "Nederland", 2),
    (4, "Flower Direct", "Kenia", 6),
    (5, "Andes Bloemen Export", "Colombia", 7),
    (6, "Valle Verde Flores", "Ecuador", 8),
    (7, "Groen Groothandel Limburg", "Nederland", 3),
    (8, "Nordic Garden Supply", "Denemarken", 5),
    (9, "Deko & Vaas Import", "Duitsland", 4),
    (10, "Terra Pots Cerâmica", "Portugal", 5),
]

# per categorie de in aanmerking komende leveranciers (leverancier_id's)
CATEGORIE_LEVERANCIERS = {
    "bollen": [1, 2],
    "zaden": [3],
    "snijbloemen": [2, 4, 5, 6, 7],
    "kamerplanten": [7, 8],
    "abonnementen": [2],
    "accessoires": [9, 10],
}

PRODUCTEN = [
    # (naam, categorie, prijs)
    ("Tulp 'Paul Scherer' (25 bollen)", "bollen", 7.50),
    ("Narcis 'Baby Jean' (25 bollen)", "bollen", 6.25),
    ("Hyacint 'Pink Pearl' (3 stuks)", "bollen", 8.95),
    ("Krokus-mix (50 bollen)", "bollen", 9.95),
    ("Narcis 'Replete' (25 bollen)", "bollen", 6.95),
    ("Iris 'Hollandia' (10 bollen)", "bollen", 7.95),
    ("Allium 'Purple Sensation' (15 bollen)", "bollen", 11.50),
    ("Dahlia 'Café au Lait' (5 knollen)", "bollen", 13.95),
    ("Lelie 'Stargazer' (10 bollen)", "bollen", 10.50),
    ("Gladiool 'Prins Claus' (10 bollen)", "bollen", 8.75),
    ("Wildebollenmix (40 bollen)", "bollen", 12.50),
    ("Zonnebloem 'Giant Russian' (zaden)", "zaden", 3.50),
    ("Zoete erwt 'Spencer' (zaden)", "zaden", 2.95),
    ("Grasmix weidebloemen (1 kg)", "zaden", 12.50),
    ("Lavendel 'Hidcote' (zaden)", "zaden", 3.25),
    ("Phacelia groenbemester (500 g)", "zaden", 6.50),
    ("Bloemenmix 'Vlinderhof' (zaden)", "zaden", 4.95),
    ("Korenbloem (zaden)", "zaden", 2.75),
    ("Kruidenmix potten (zaden)", "zaden", 3.15),
    ("Rode miet & klaproos (zaden)", "zaden", 2.95),
    ("Rozen 'Avalanche' (10 stengels)", "snijbloemen", 14.95),
    ("Tulpenboeket gemengd (15 stengels)", "snijbloemen", 11.50),
    ("Zonnebloemboeket (5 stengels)", "snijbloemen", 9.75),
    ("Gerbera 'Mini Mix' (10 stengels)", "snijbloemen", 8.50),
    ("Lelies 'Orient' (5 stengels)", "snijbloemen", 13.25),
    ("Ranunkel (10 stengels)", "snijbloemen", 10.95),
    ("Anjer 'Sociable' (10 stengels)", "snijbloemen", 7.95),
    ("Freesia gemengd (10 stengels)", "snijbloemen", 8.25),
    ("Lisianthus 'Rosanne' (7 stengels)", "snijbloemen", 11.95),
    ("Eucalyptus 'Baby Blue' (5 stengels)", "snijbloemen", 6.95),
    ("Pioenroos 'Coral Charm' (7 stengels)", "snijbloemen", 16.50),
    ("Droogbloemen 'Dune' boeket (7 stuks)", "snijbloemen", 12.75),
    ("Orchidee Phalaenopsis (1 pot)", "kamerplanten", 24.95),
    ("Monstera Deliciosa (M-pot)", "kamerplanten", 29.95),
    ("Sansevieria (M-pot)", "kamerplanten", 19.95),
    ("Vetplanten assortiment (3 stuks)", "kamerplanten", 12.95),
    ("Arecapalm (M-pot)", "kamerplanten", 27.50),
    ("Philodendron 'Brasil' (M-pot)", "kamerplanten", 21.95),
    ("Lepelleplant (M-pot)", "kamerplanten", 23.50),
    ("Aloë vera (S-pot)", "kamerplanten", 9.95),
    ("Geldboom Pachira (M-pot)", "kamerplanten", 25.50),
    ("Hangende vetplant (hangmand)", "kamerplanten", 14.50),
    ("Kalenderjaarabonnement bloemenpakket", "abonnementen", 49.95),
    ("Proefabonnement wekelijks", "abonnementen", 27.50),
    ("Maandabonnement bloemen (4 bezorgingen)", "abonnementen", 42.50),
    ("Seizoensabonnement 10 weken", "abonnementen", 99.95),
    ("Zakelijkabonnement kantoor (wekelijks)", "abonnementen", 64.95),
    ("Vaas 'Delfts Blauw' (30 cm)", "accessoires", 17.95),
    ("Snoeischaar professioneel", "accessoires", 22.50),
    ("Bloempot terracotta (set van 3)", "accessoires", 15.95),
    ("Kompost 20 liter", "accessoires", 8.95),
    ("Vloeibare bloemenvoeding (500 ml)", "accessoires", 6.95),
    ("Tuinset 3-delig RVS", "accessoires", 19.95),
    ("Plantenspuit 'Mist' (300 ml)", "accessoires", 9.75),
    ("Bindraad & bloementape set", "accessoires", 7.50),
    ("Geurkaars 'Passiebloesem'", "accessoires", 13.50),
    ("Cadeaubon Knol & Bloei (naar keuze)", "accessoires", 25.00),
]

BEZORGERS = ["PostNL", "DHL", "Budbee", "Eigen bezorgdienst"]
BEZORG_DEELGEWICHTEN = [40, 25, 20, 15]
BESTELBRONNEN = ["website", "mobiele app", "e-mail"]
BESTELBRON_DEELGEWICHTEN = [62, 28, 10]


def genereer_klanten():
    klanten, namen = [], set()
    for i in range(1, AANTAL_KLANTEN + 1):
        while True:
            naam = f"{random.choice(VOORNAMEN)} {random.choice(ACHTERNAMEN)}"
            if naam not in namen:
                namen.add(naam)
                break
        stad = random.choice(STEDEN)
        segment = "zakelijk" if random.random() < 0.25 else "particulier"
        klanten.append((i, naam, stad, segment))
    return klanten


KLANTEN = genereer_klanten()


def genereer_producten():
    producten = []
    for naam, cat, prijs in PRODUCTEN:
        inkoop = round(prijs * random.uniform(0.42, 0.66), 2)
        leverancier = random.choice(CATEGORIE_LEVERANCIERS[cat])
        producten.append((naam, cat, prijs, inkoop, leverancier))
    return producten


PRODUCTRIJEN = genereer_producten()


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

    # leveranciers.csv
    schrijf("leveranciers.csv",
            ["leverancier_id", "naam", "land", "levertijd_dagen"], LEVERANCIERS)

    # producten.csv (nu met inkoopprijs en leverancier)
    schrijf("producten.csv",
            ["product_id", "naam", "categorie", "prijs", "inkoopprijs", "leverancier_id"],
            [(i, n, c, f"{p:.2f}", f"{ink:.2f}", lev)
             for i, (n, c, p, ink, lev) in enumerate(PRODUCTRIJEN, 1)])

    # bestellingen.csv + orderregels.csv (1 juni 2025 t/m oktober 2026)
    start, einde = date(2025, 6, 1), date(2026, 10, 31)
    dagen = (einde - start).days
    bestellingen, regels, verzendingen = [], [], []
    ingekocht = {}  # (klant_id, product_id) → eerste aankoopdatum
    bestel_id = verzend_id = 0
    for _ in range(AANTAL_BESTELLINGEN):
        bestel_id += 1
        d = start + timedelta(days=random.randint(0, dagen))
        # seizoenspiek: bolletijd (okt-dec) en voorjaar (mrt-mei) drukker
        if d.month in (3, 4, 5, 10, 11, 12) and random.random() < 0.35:
            maand = random.choice([3, 4, 10, 11])
            dag = min(d.day, [31, 30, 31, 30][[3, 4, 10, 11].index(maand)])
            d = d.replace(month=maand, day=dag)
        klant = random.choice(KLANTEN)
        bezorgd = 1 if random.random() < 0.93 else 0
        bron = random.choices(BESTELBRONNEN, weights=BESTELBRON_DEELGEWICHTEN)[0]
        bestellingen.append((bestel_id, klant[0], d.isoformat(), bezorgd, bron))
        for regel_nr in range(1, random.randint(1, 4) + 1):
            p = random.randint(1, len(PRODUCTRIJEN))
            prijs = PRODUCTRIJEN[p - 1][2]
            aantal = random.choices([1, 2, 3, 4, 5, 10], weights=[50, 25, 12, 6, 4, 3])[0]
            korting = random.choice([0.0, 0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20])
            regels.append((bestel_id, regel_nr, p, aantal, f"{prijs:.2f}", f"{korting:.2f}"))
            sleutel = (klant[0], p)
            if sleutel not in ingekocht or d < ingekocht[sleutel]:
                ingekocht[sleutel] = d
        if bezorgd:
            verzend_id += 1
            bezorger = random.choices(BEZORGERS, weights=BEZORG_DEELGEWICHTEN)[0]
            kosten = random.choice([0.0, 4.95, 4.95, 4.95, 6.95, 9.95])
            levertijd = random.choices([1, 2, 3, 4, 5], weights=[10, 35, 30, 17, 8])[0]
            verzendingen.append((verzend_id, bestel_id, bezorger, f"{kosten:.2f}",
                                 (d + timedelta(days=levertijd)).isoformat(), levertijd))

    schrijf("bestellingen.csv",
            ["bestelling_id", "klant_id", "besteldatum", "bezorgd", "bestelbron"], bestellingen)
    schrijf("orderregels.csv",
            ["bestelling_id", "regel_nr", "product_id", "aantal", "prijs_per_stuk", "korting"], regels)
    schrijf("verzendingen.csv",
            ["verzending_id", "bestelling_id", "bezorger", "verzendkosten",
             "verzend_datum", "levertijd_dagen"], verzendingen)

    # beoordelingen.csv — klanten reviewen alleen wat ze écht kochten
    paren = sorted(ingekocht)
    reviews = random.sample(paren, min(AANTAL_BEOORDELINGEN, len(paren)))
    beoordelingen = []
    for i, (klant_id, product_id) in enumerate(reviews, 1):
        sterren = random.choices([1, 2, 3, 4, 5], weights=[3, 5, 12, 34, 46])[0]
        datum = ingekocht[(klant_id, product_id)] + timedelta(days=random.randint(1, 45))
        beoordelingen.append((i, klant_id, product_id, sterren, datum.isoformat()))
    schrijf("beoordelingen.csv",
            ["beoordeling_id", "klant_id", "product_id", "sterren", "beoordeeld_op"], beoordelingen)

    print("Klaar. Bouw nu de SQLite-database met:  uv run python scripts/bouw_database.py")


if __name__ == "__main__":
    main()
