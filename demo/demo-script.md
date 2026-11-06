# Demo-script — Apache Ossie met Knol & Bloei

**Duur:** 12–15 minuten · **Publiek:** data-, BI- en softwareteams

## Klaarzetten

Voer vanuit de projectmap uit:

```bash
uv sync
uv run python scripts/cli_vraag.py --leg
uv run python app/webshop_demo.py
```

Laat de UI starten en houd de terminal beschikbaar. De CSV's en SQLite-database zijn al opgenomen. Herbouw ze alleen als dat nodig is met `uv run python scripts/genereer_data.py` en `uv run python scripts/bouw_database.py`.

## 1. Intro — waarom gedeelde semantiek? (1 min)

**Zeg:** “Als ik drie teams vraag naar omzet, kunnen drie definities terugkomen. Vandaag bekijken we hoe Apache Ossie semantische afspraken als uitwisselbaar model vastlegt.”

## 2. Lees het model (3 min)

Open `models/knol_en_bloei.ossie.yaml` of de modeltab in de demo.

- Wijs de datasets aan: bestellingen, orderregels, producten, klanten, verzendingen, beoordelingen en leveranciers.
- Laat `regel_bedrag` zien: aantal × prijs per stuk × (1 − korting).
- Vergelijk `omzet` met `bruto_omzet`.
- Wijs relationships aan, bijvoorbeeld orderregels → producten → leveranciers.
- Toon `ai_context` met synoniemen en voorbeeldvragen.
- Gebruik de knop voor modelvalidatie en benoem dat dit project een minimale consumer/validator heeft.

**Kernzin:** “De businessdefinitie staat in het model; de consumer leest haar.”

## 3. Volg een analyse (4–5 min)

Ga naar **Analyseer** en kies `orderregels.omzet` met `producten.categorie`.

1. Toon de gegroepeerde resultaten en grafiek.
2. Toon de gegenereerde SQL. Leg uit dat de relatie naar producten uit `relationships` komt.
3. Wissel naar `bruto_omzet` en wijs erop dat het verschil in betekenis expliciet als metric is gemodelleerd.
4. Probeer, indien beschikbaar, `gemiddelde_orderwaarde` per stad of `brutomarge` per leveranciersland om meer-hop-relaties te tonen.

**Vraag aan publiek:** “Welke definitie zou bij jullie organisatie eerst afgestemd moeten worden?”

## 4. Zelfde model, andere ingang (2–3 min)

In een terminal, vanuit de projectmap:

```bash
uv run python scripts/cli_vraag.py "wat is de omzet per categorie"
uv run python scripts/cli_vraag.py "gemiddelde orderwaarde per stad"
```

Toon dat de CLI hetzelfde model en dezelfde querylogica gebruikt. De UI en CLI zijn twee consumers van dezelfde definities.

## 5. Vraag in gewone taal (2 min)

Ga naar **Vraag via AI-context** en voer “hoeveel verkochte stuks per maand?” in. Wijs op de herkende metric/dimensie en de herkomst uit `ai_context`.

**Zeg expliciet:** “Dit is een regelgebaseerde matcher, geen LLM. Het voorbeeld laat zien hoe metadata een taalinterface kan sturen.”

## 6. Afsluiting (1 min)

Vat samen: het model documenteert datasets, velden, metrics en relaties; consumers kunnen die definities gebruiken om analyses consistent uit te voeren. Deze demo implementeert een beperkte subset en is bedoeld om het principe tastbaar te maken. Voor productie: verifieer compatibiliteit met de actuele officiële specificatie en tooling.

**Optionele verdieping:** open [mini-cursus](mini-cursus.md) en laat deelnemers de oefening doen.
