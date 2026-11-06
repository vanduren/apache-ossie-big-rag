# Samenvatting — Apache Ossie (incubating) demo met Knol & Bloei

## Wat is Apache Ossie?

**Apache Ossie (incubating)** — voorheen *Open Semantic Interchange (OSI)* — is
een open, vendor-neutrale **specificatie voor semantische modellen**: één
JSON/YAML-standaard waarin je *datasets* (feit- en dimensietabellen), *velden*,
*relaties* en *metrics* (omzet, AOV, …) **één keer** definieert, zodat BI-tools,
analytics-platformen én **AI-agents** allemaal vanuit dezelfde definities werken.
Slogan: *"Write Once, Query Anywhere."*

- 📜 Specificatie: <https://github.com/apache/ossie/blob/main/core-spec/spec.md> (versie 0.2.0.dev0)
- 🏠 Projectpagina: <https://ossie.apache.org>
- 🔄 Referentie-converters (dbt, Snowflake, GoodData, …): <https://github.com/apache/ossie-converters>
- 🐍 Python SDK (Pydantic) leeft in de repo (`python/`), maar staat nog niet op PyPI —
  daarom bevat deze demo een eigen, zelfstandige "consumer" (`app/ossie_core.py`).

Probleem dat het oplost: **semantische fragmentatie** — dezelfde KPI ("omzet")
die in elke tool anders gedefinieerd is, wat metric drift, arbeidsintensieve
handmatige vertaling en hallucinerende AI oplevert.

## De use case: bloemenwebshop "Knol & Bloei"

Een middelgrote bloemenwebshop met vier tabellen in **SQLite**:
`klanten`, `producten`, `bestellingen`, `orderregels`. Drie "tools" — een
desktop-dashboard (CustomTkinter), een commandoregel en een AI-agent — moeten
elk hetzelfde antwoord geven op "wat is de omzet per categorie?".

In plaats van drie keer een eigen definitie te schrijven, definieert
Knol & Bloei **één Ossie-model** (`models/knol_en_bloei.ossie.yaml`):

- **datasets** met velden (incl. computed fields zoals `regel_bedrag`);
- **dataset-metrics** zoals `omzet = SUM(regel_bedrag)`;
- **model-metrics** die over datasets spreiden:
  `gemiddelde_orderwaarde = SUM(orderregels.regel_bedrag) / COUNT(DISTINCT bestellingen.bestelling_id)`;
- **relationships** als joins;
- **ai_context** met synoniemen ("revenue", "verkopen") en voorbeeldvragen,
  zodat een AI-agent de juiste metric kiest.

## Wat er is gebouwd

| Onderdeel | Pad |
|---|---|
| Ossie-semantisch model (demo van de core-spec) | `models/knol_en_bloei.ossie.yaml` |
| Voorbeeld-databestanden (CSV) | `data/*.csv` (40 klanten, 22 producten, 320 bestellingen, 665 orderregels) |
| SQLite-database | `data/webshop.db` (bouwscript: `scripts/bouw_database.py`) |
| Ossie-"consumer": loader, validatie, SQL-compiler, AI-match | `app/ossie_core.py` |
| **User interface (CustomTkinter / Tk)** | `app/webshop_demo.py` |
| CLI voor dezelfde vragen | `scripts/cli_vraag.py` |
| Use case-beschrijving | `docs/use-case.md` |
| Demo-script voor publiek | `docs/demo-script.md` |

De consumer compileert metric + dimensie **automatisch** naar SQLite-SQL:
veldnamen worden door hun expressies vervangen en joins worden via
`relationships` gevonden (zelfs meer-hop-paden zoals
`orderregels → bestellingen → klanten`). Dit is precies de taak die de
Ossie-spec aan een "consumer" toedicht (§ *Name Resolution* en *Metric Scoping*).

## Hoe te gebruiken (kern)

1. **Model schrijven** — data-architect/domeinexpert definieert één `.ossie.yaml`.
2. **Valideren** — `cli_vraag.py --leg` of de UIcontroleren de kernregels
   (verplichte velden, unieke namen, geldige veldreferenties, …).
3. **Consumeren** — elke tool leest hetzelfde model en compileert er queries
   tegen zijn eigen engine (hier: SQLite) mee. Niets definiëert "omzet" opnieuw.
4. **Uitbreiden** — nieuwe tool? Sluit aan op het model (of converteer via
   ossie-converters). AI?-feed `ai_context` mee als semantische anker.

## Demo in één zin

Aan het publiek laten zien dat één YAML-bestand drie interfaces voedt: je typt
*"wat is de omzet per categorie?"*, ziet hoe het model de vraag herkend via
`ai_context`, de gegenereerde SQL oneindig vaak herbruikt wordt en als grafiek
verschijnt — zonder dat er één query met de hand is geschreven.
