# Demo-script — "Eén model, drie tools" (~12 minuten)

> publiek: technisch publiek met data/BI-achtergrond.
> Voorbereiding: terminal links, demo-UI rechts, beide maximaal leesbaar (groot lettertype).

## Voorbereiding (vóór het publiek)

```bash
cd apache-ossie
uv sync
uv run python scripts/genereer_data.py      # alleen de eerste keer (CSV's staan er al)
uv run python scripts/bouw_database.py      # ... idem, webshop.db staat er al
uv run python app/webshop_demo.py           # UI laten starten
```

## Akte 0 — het probleem (1 min)

*"Hoeveel bedroeg de omzet in 2026?"* Vraag dat aan het dashboard, aan de
analist en aan een chatbot — en je krijgt drie antwoorden. Iedere tool heeft
zijn eigen definitie van 'omzet'. Dat is het probleem dat
**Apache Ossie (incubating)** oplost: één open standaard voor semantische
definities. write once, query anywhere.

## Akte 1 — het model (3 min, UI-tabblad **📄 Het Ossie-model**)

1. Wijs op `models/knol_en_bloei.ossie.yaml` (rechtspaneel = echte YAML).
2. Loop de onderdelen van de core-spec langs:
   - **datasets** — fact (`orderregels`) plus feitten voor bezorging
     (`verzendingen`) en klanttevredenheid (`beoordelingen`), en de dimensies
     `bestellingen`, `producten`, `leveranciers` en `klanten`, elk met een
     `source` naar de fysieke SQLite-tabel;
   - **fields** — let op `regel_bedrag = aantal * prijs_per_stuk * (1 - korting)`:
     *dit* is de enige plaats waar "netto-omzet per regel" bestaat;
   - **metrics** — dataset-scope (`omzet`) en model-scope
     (`gemiddelde_orderwaarde`, verwijst over datasets naar `bestellingen.bestelling_id`);
   - **relationships** — de enige toegestane joinroutes;
   - **ai_context** — synoniemen en voorbeeldvragen voor AI-tools.
3. Klik **"Valideer model tegen de spec"**: alle kernregels groen.
   *(Optioneel: open het YAML, maak ergens een typo in een metric-referentie,
   herlaad en valideer — de demo laat dan direct een rode fout zien.)*

> Kernboodschap: dit bestand ís de 'single source of truth'-laag. Geen tool mag
> 'omzet' opnieuw uitvinden.

## Akte 2 — de machine draait zelf (4 min, tabblad **🔍 Analyseer**)

1. Laat zien dat de UI **geen SQL kent**: geen query's in de code, alleen
   dropdowns die uit het model zijn opgebouwd.
2. Kies `orderregels.omzet` × `producten.categorie` → **▶**.
   Wijs op het midden: de *gecompileerde SQL* — veldnamen zijn door hun
   expressies vervangen, de join komt uit `relationships`. Rechts: grafiek.
3. **Tovertrick 1 (consistentie):** wissel naar `orderregels.bruto_omzet`.
   Zelfde dimensie, ander getal — "bruto vs. netto" is nu één expliciete
   metric-keuze in plaats van een stil verschil tussen twee tools.
4. **Tovertrick 2 (model-scope):** kies `gemiddelde_orderwaarde` × `klanten.stad`.
   De query sprent nu twee hops: `orderregels → bestellingen → klanten` —
   alle joins netjes uit het model gehaald.
5. **Tovertrick 3 (inhoud groeit mee):** kies `brutomarge` × `leveranciers.land`.
   De compiler vindt vanzelf het drietal joins `orderregels → producten →
   leveranciers` en trekt per land de inkoopprijs van de verkoopprijs af —
   in een nieuw dataset dat er bij de eerste demo-versie nog niet eens was.
   Bonus: `gemiddelde_levertijd` × `verzendingen.bezorger` of
   `gemiddelde_sterren` × `producten.categorie` — dezelfde machine, nieuwe vragen.
6. Zet de switch **"alleen bezorgde bestellingen"** aan — dezelfde pipeline,
   nu met `WHERE bestellingen.bezorgd = 1`.

## Akte 3 — de AI-vraag (3 min, tabblad **🤖 Vraag via AI-context**)

1. Typ: *"hoeveel verkochte stuks per maand?"* → **Zoek in model 🤖**.
   Het systeem laat zien wát het herkend heeft en wáárom: de match kwam via
   `ai_context.synonyms` van metric en dimensie. Antwoord + SQL verschijnen;
   de Analyseer-tab staat op dezelfde selectie (grafiek up-to-date).
2. Typ iets geks: *"wat kost een tulp in Frankrijk?"* → geen match.
   Boodschap: een agent kiest alleen uit goedgekeurde definities — geen
   verzinnen, dus geen hallucinaties.
3. Klik een paar voorbeeldknoppen door ("omzet per categorie", "gemiddelde
   orderwaarde per stad", "wat is de brutomarge per leverancier", "gemiddelde
   levertijd per bezorger").

## Akte 4 — "query anywhere" live (2 min, terminal)

```bash
# dezelfde vraag, andere tool, zelfde antwoord:
uv run python scripts/cli_vraag.py "wat is de omzet per categorie"

# toon alleen de gegenereerde SQL (die de UI zonet bouwde):
uv run python scripts/cli_vraag.py --metric orderregels.omzet \
    --dimensie producten.categorie --alleen-sql
```

Vergelijk het getal met de UI: **identiek**. Stel je voor dat dit YAML morgen
ook naar dbt, Snowflake, Power BI of een LLM-agent geconverteerd wordt —
daarvoor bestaan de officiële *ossie-converters*.

## Afsluiting (1 min)

- Eén vendor-neutraal YAML-model: **single source of semantic truth**.
- Drie consumenten (UI, CLI, 'AI') — nul duplicated business logic.
- AI krijgt betrouwbare ankerpunten (`ai_context`) → geen verzonnen cijfers.
- Dit project toont de kern van de spec in het klein; in het echt doe je het
  met TPC-DS-formaat modellen en Snowflake/Power BI achter dezelfde YAML.
- Links: ossie.apache.org · github.com/apache/ossie

## Veelvoorkomende vragen (Q&A-voorbeelden)

- **"Vervangt dit dbt/LookML?"** Nee — het úitwisselen ervan; Ossie is het
  interchange-formaat, converters (apache/ossie-converters) koppelen aan bestaande tools.
- **"Waarom staat de SQL-compiler in de demo en niet in een library?"** De officiële
  Python SDK (Pydantic, map `python/` in de repo) staat nog niet op PyPI; deze demo
  imiteert bewust wat elke consumer moet doen (name resolution + scoping).
- **"Schaalt dit?"** Het model is klein (mens-leesbaar); de queries draaien tegen
  een miljardenrijen-feitentabel net zo goed — de SQL-dialecten en
  `custom_extensions` zijn daarvoor bedoeld.
