# Apache Ossie (incubating) — demo: bloemenwebshop "Knol & Bloei"

Een complete, werkende demo van [Apache Ossie (incubating)](https://ossie.apache.org)
— de open standaard voor **uitwisseling van semantische modellen** (voorheen
*Open Semantic Interchange*) — met:

- 📄 een **Ossie-semantisch model** volgens de Core Metadata Specification (v0.2.0.dev0);
- 🗄️ **SQLite** als database, met voorbeeld-CSV-bestanden als databron;
- 🖥️ een **user interface** in Python CustomTkinter (tkinter/gebaseerd, "Tinker Q"-stijl);
- ⌨️ een **CLI** die exact dezelfde vragen beantwoordt — bewijs van "query anywhere";
- 🤖 een AI-context-laag: vrije-tekstvragen worden via `ai_context` naar
  metrics/dimensies gematcht.

| Document | Inhoud |
|---|---|
| [`samenvatting.md`](samenvatting.md) | Wat is Apache Ossie + wat deze demo toont |
| [`docs/use-case.md`](docs/use-case.md) | De use case en hoe Ossie gebruikt *moet* worden |
| [`docs/demo-script.md`](docs/demo-script.md) | Stap-voor-stap demo voor een publiek (~12 min) |
| [`prompts.md`](prompts.md) | De originele opdracht voor dit project |

## Projectstructuur

```
apache-ossie/
├── models/
│   └── knol_en_bloei.ossie.yaml   ← hét Ossie-model (datasets, metrics, relaties, ai_context)
├── data/
│   ├── klanten.csv                ← voorbeeldbestanden (bron)
│   ├── producten.csv
│   ├── bestellingen.csv
│   ├── orderregels.csv
│   └── webshop.db                 ← SQLite-database (gegenereerd, meegeleverd)
├── app/
│   ├── ossie_core.py              ← Ossie-"consumer": loader, validatie, SQL-compiler, AI-match
│   └── webshop_demo.py            ← CustomTkinter-interface
├── scripts/
│   ├── genereer_data.py           ← hermaakt de CSV's (deterministisch, seed=42)
│   ├── bouw_database.py           ← CSV → data/webshop.db
│   └── cli_vraag.py               ← dezelfde vragen via de commandoregel
└── docs/                          ← use case + demo-script
```

## Snel starten

Vereist: [`uv`](https://docs.astral.sh/uv/) (deze computer heeft die) en Python (uv regelt zelf een geschikte versie).

```bash
cd apache-ossie
uv sync                                   # installeert pyyaml + customtkinter

# alleen de eerste keer (data en db staan er al, maar kunnen herbouwd worden):
uv run python scripts/genereer_data.py
uv run python scripts/bouw_database.py

# de interface starten:
uv run python app/webshop_demo.py
```

Commandoregel-versie (zelfde model, zelfde compiler, andere tool):

```bash
uv run python scripts/cli_vraag.py --leg                          # model + validatie
uv run python scripts/cli_vraag.py "wat is de omzet per categorie"
uv run python scripts/cli_vraag.py "gemiddelde orderwaarde per stad"
uv run python scripts/cli_vraag.py "hoeveel verkochte stuks per maand"
```

## Wat de interface laat zien

**Tabblad 🔍 Analyseer** — kies een *metric* en *dimensie* uit de dropdowns
(deze worden uit het Ossie-model zelf opgebouwd). Druk op ▶ en de tool
compileert ter plekke SQLite-SQL: veldnamen worden door hun expressies uit het
model vervangen, joins worden via `relationships` gezocht (meer-hop, bv.
`orderregels → bestellingen → klanten`). Het gegenereerde SQL, de resultaattabel
en een staafdiagram verschijnen naast elkaar. Er staat géén handmatige
query in de applicatie.

**Tabblad 🤖 Vraag via AI-context** — typ een vraag in gewone taal. De demo
matcht 'm op `ai_context.synonyms`/`examples` uit het model (een kleine
vervoudiging van wat een echte LLM-agent doet) en toont welke definitie is
gekozen en waarom — precies de mechanismen waarmee Ossie AI-hallucinaties door
consistentie tegengaat.

**Tabblad 📄 Het Ossie-model** — het echte YAML naast een leesbare samenvatting,
met een knop die het model valideert tegen de kernregels van de specificatie
(verplichte velden, naam-namespaces, geldige veldreferenties, scoping van
metrics).

## Wat Apache Ossie is (tl;dr)

> Apache Ossie is een industry-wide specificatie die gestandaardiseerd
> **semantische metadata** (datasets, velden, relaties, metrics) uitwisselt
> tussen analytics-, BI- en AI-platformen — vendor-neutraal, YAML/JSON,
> Apache 2.0. Eén definitie van "omzet"; elke tool en elke AI-agent leest
> dezelfde waarheid.

- Kern-spec: <https://github.com/apache/ossie/blob/main/core-spec/spec.md>
- Voorbeeldmodellen (o.a. TPC-DS): <https://github.com/apache/ossie/tree/main/examples>
- Converters naar/uit dbt, Snowflake, GoodData, Salesforce, …: <https://github.com/apache/ossie-converters>

## Toelichting op deze implementatie

- De officiële **Python SDK** (Pydantic) leeft in de repo (`python/`) maar staat
  nog niet op PyPI; `app/ossie_core.py` is daarom een zelfstandige, minimale
  consumer die de relevante onderdelen van de spec navolgt: name resolution,
  metric-scoping en relatiegebaseerde joins.
- `source: webshop.orderregels` gebruikt de notatie `database.schema.tabel`
  zoals de spec voorschrijft; deze SQLite-consumer neemt het laatste deel als
  tabelnaam (SQLite kent geen schema's).
- Het model gebruikt alleen portable SQL in het veld `expression.sql`, zodat de
  gegenereerde queries ook op andere engines (PostgreSQL, DuckDB) werken.
- Het AI-matcher is bewust een eenvoudige regelmatige matcher (geen LLM): het punt van de
  demo is dat de semantische ankerpunten uit het Ossie-model komen, niet welk
  model de vraag interpreteert.

## Herhaalbaar voorbeeld

Deterministische gegenereerde data (seed 42): **40 klanten**, **22 producten**
(5 categorieën), **320 bestellingen** en **665 orderregels** over
juni 2025 – oktober 2026, met seizoenspieken in het voor- en najaar.
Herbouw altijd identiek: `uv run python scripts/genereer_data.py`.
