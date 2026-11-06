# prompts.md — originele opdracht

> Dit bestand bevat de letterlijke prompt waarmee deze demo is gebouwd,
> followed by de date and a short note on execution.

## De prompt

> bekijk online de documentatie / informatie rondom apache ossie. Maak een
> eenvoudige use case. Voorzie de case van voorbeeldbestanden, indien mogelijk
> bijvoorbeeld data bestanden. Beschrijf hoe apache ossie dan gebruikt kan of
> moet worden. Geef een duidelijke beschrijving van een demo die kan worden
> gedemonstreerd aaan een publiek. Maak dus ook een user interface, bijvoorbeeld
> met behulp van python Tinker Q. Op deze computer is python en uv geinstalleerd.
> Als database systeem gebruik het liefst SQLite. Schrijf deze prompt naar een
> bestand met de naam prompts.md. Maak ook een samenvatting.md en een readme.md.
> Als je klaar bent, doe dan een git init en een commit.

## Uitvoering (november 2026)

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
