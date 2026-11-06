# prompts.md — originele opdrachten

> Dit bestand bevat de letterlijke prompts waarmee deze demo is gebouwd en
> uitgebreid, telkens gevolgd door de datum en een korte notitie van uitvoering.

## Prompt 1 — de oorspronkelijke demo

> bekijk online de documentatie / informatie rondom apache ossie. Maak een
> eenvoudige use case. Voorzie de case van voorbeeldbestanden, indien mogelijk
> bijvoorbeeld data bestanden. Beschrijf hoe apache ossie dan gebruikt kan of
> moet worden. Geef een duidelijke beschrijving van een demo die kan worden
> gedemonstreerd aaan een publiek. Maak dus ook een user interface, bijvoorbeeld
> met behulp van python Tinker Q. Op deze computer is python en uv geinstalleerd.
> Als database systeem gebruik het liefst SQLite. Schrijf deze prompt naar een
> bestand met de naam prompts.md. Maak ook een samenvatting.md en een readme.md.
> Als je klaar bent, doe dan een git init en een commit.

### Uitvoering (november 2026)

- Online gedocumenteerd via ossie.apache.org en github.com/apache/ossie
  (Core Metadata Specification, versie 0.2.0.dev0).
- Use case: bloemenwebshop **Knol & Bloei** (zie `docs/use-case.md`).
- Voorbeeldbestanden: CSV's in `data/` + SQLite-database `data/webshop.db`.
- Semantisch model: `models/knol_en_bloei.ossie.yaml`.
- User interface: CustomTkinter ("Tinker Q"-stijl, tkinter-gebaseerd) —
  `app/webshop_demo.py`; daarnaast een CLI (`scripts/cli_vraag.py`).
- Database: SQLite, zoals verzocht.
- Tooling: `uv` (acties: `uv sync`, `uv run …`).
- Documentatie: `readme.md`, `samenvatting.md`, `docs/use-case.md`,
  `docs/demo-script.md`.
- Afgesloten met `git init` + `git commit`.

## Prompt 2 — datapuitbreiding

> voeg data toe (meer entiteiten en relaties) en vergroot de kwantiteit.
> Update de scripts waar nodig (bijvoorbeeld voorbeelvragen) en werk prompts.md
> bij en commit.

### Uitvoering (november 2026)

- **Nieuwe entiteiten** (CSV + SQLite-tabel + Ossie-dataset): `leveranciers`
  (10 kwekers/exporteurs in 6 landen), `verzendingen` (één per bezorgde
  bestelling: bezorger, kosten, levertijd) en `beoordelingen` (1–5 sterren,
  alleen op écht gekochte producten).
- **Meer relaties**: `producten → leveranciers`, `bestellingen → verzendingen`,
  `beoordelingen → klanten` en `beoordelingen → producten` — samen 7 relaties,
  goed voor drie-hop-paden zoals `orderregels → producten → leveranciers`.
- **Kwantiteit × 5 à × 6** (zaad 42 blijft deterministisch): 150 klanten,
  57 producten, 1.800 bestellingen, 4.451 orderregels, plus de drie nieuwe
  tabellen; `producten` kregen `inkoopprijs` en `leverancier_id`,
  `bestellingen` een `bestelbron` (kanaal).
- **Nieuwe metrics** in het model: `brutomarge`, `margepercentage` en
  `verzendkosten_per_order` (model-scope, cross-dataset) en
  dataset-metrics voor bezorging (`gemiddelde_levertijd`, verzendkosten) en
  klanttevredenheid (`gemiddelde_sterren`, `aantal_beoordelingen`).
- **Scripts en UI**: voorbeeldvragen in `scripts/cli_vraag.py`,
  `app/webshop_demo.py` en `app/ai_demo.py` uitgebreid met marge-, bezorg- en
  reviewvragen; de UI-statusbalk toont nu alle zeven tabellen;
  `scripts/genereer_data.py` en `scripts/bouw_database.py` maken en laden de
  nieuwe tabellen.
- **Documentatie**: `readme.md`, `samenvatting.md`, `docs/use-case.md` en
  `docs/demo-script.md` meegenomen; afgesloten met een commit.
