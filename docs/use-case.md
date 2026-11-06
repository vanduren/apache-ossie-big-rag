# Use case — bloemenwebshop "Knol & Bloei"

## Het probleem

Knol & Bloei is een bloemen- en bollenwebshop. Over een paar jaar is er een SQLite-database aan verkoopdata: `klanten`,
`producten`, `bestellingen` en
`orderregels`. Drie partijen willen antwoorden op dezelfde of gelijkende vragen:

1. **Het dashboard-team** bouwt een internal app (deze demo: CustomTkinter).
2. **De data-analist** werkt op de commandoregel (deze demo: `cli_vraag.py`).
3. **Een AI-assistent** moet in natuurlijke taal vragen kunnen beantwoorden.

Zonder standaard gebeurt precies wat Ossie wil voorkomen: het dashboard definieert
"omzet" als *bedrag vóór btw op factuurniveau*, de analist als *aantal × prijs
per stuk* en de AI leert iets derde. Resultaat: drie antwoorden op één vraag —
metric drift, gedoe en wantrouwen. (En bij de demo hieronder zie je het
verschil tussen `bruto_omzet` en `omzet`: precies de valkuil.)

## De Oplossing: één Ossie-model

In Apache Ossie schrijf je de semantiek **één keer**, in een vendor-neutraal
YAML-document (`models/knol_en_bloei.ossie.yaml`), volgens de *Core Metadata
Specification* (v0.2.0.dev0):

| Ossie-bouwsteen | In deze demo |
|---|---|
| **Semantic Model** | `knol_en_bloei` — één document = één model |
| **Datasets** | `orderregels` (fact), `bestellingen`, `producten`, `klanten` (dimensies) |
| **Fields** | o.a. computed: `regel_bedrag = aantal * prijs_per_stuk * (1 - korting)` — één definitie, overal identiek |
| **Metrics (dataset-scope)** | `orderregels.omzet`, `bruto_omzet`, `verkochte_stukken`, `gemiddelde_korting` |
| **Metrics (model-scope)** | `omzet_per_klant`, `gemiddelde_orderwaarde` — tellen `dataset.veld` over meerdere datasets |
| **Relationships** | `orderregels → bestellingen → klanten`, `orderregels → producten` |
| **Time-dimensions** | `besteldatum`, `bestel_maand` (`dimension.is_time: true`) |
| **ai_context** | instructies, synoniemen ("revenue", "verkopen", "AOV") en voorbeeldvragen |
| **custom_extensions** | vendor-metadata (hier: SQLite-pad), door Ossie gedragen maar niet geïnterpreteerd |

Twee spec-details die in de demo zichtbaar zijn:

- **Name resolution**: een veld-expressie verwijst naar kolommen van de eigen
  `source`; een dataset-metric verwijst met korte naam naar eigen velden
  (`SUM(regel_bedrag)`); een model-metric gebruikt `dataset.veld`.
  De consumer vertelt dit om naar fysieke kolommen.
- **Metric scoping**: een cross-dataset metric *moet* in de model-root; de
  validatie in `app/ossie_core.py` markeert een dataset-metric met
  `customers.id`-referenties als fout.

## Hoe Ossie hier gebruikt wordt (stap voor stap)

### 1. Gegeven: fysieke tabel in SQLite

```
orderregels(bestelling_id, regel_nr, product_id, aantal, prijs_per_stuk, korting)
```

### 2. Model: beschrijf de semantiek, schrijf géén SQL

```yaml
datasets:
  - name: orderregels
    source: webshop.orderregels
    fields:
      - name: regel_bedrag
        expression: { sql: aantal * prijs_per_stuk * (1 - korting) }
    metrics:
      - name: omzet
        expression: { sql: SUM(regel_bedrag) }
        ai_context: { synonyms: ["revenue", "verkopen"] }
relationships:
  - name: regels_naar_producten
    from: orderregels
    to: producten
    from_columns: [product_id]
    to_columns: [product_id]
```

### 3. Consumer: elke tool compileert queries uit het model

Deze demo's "consumer" (`app/ossie_core.py`) doet wat elke BI-tool of agent
met een Ossie-model zou doen:

1. lees het model en los `dataset.veld`-referenties op (name resolution);
2. vind de nodige joins via `relationships` (ook 2-hop: orden→klanten);
3. vervang elke veldnaam door zijn expressie;
4. genereer `SELECT … GROUP BY … ORDER BY …` en voer uit op SQLite.

Voor `"omzet per categorie"` produceert hij:

```sql
SELECT (producten.categorie) AS "dimensie",
       SUM((orderregels.aantal * orderregels.prijs_per_stuk
            * (1 - orderregels.korting))) AS "omzet"
FROM orderregels AS orderregels
JOIN producten AS producten ON (orderregels.product_id) = (producten.product_id)
GROUP BY 1 ORDER BY 2 DESC LIMIT 25
```

…zonder dat die SQL ergens in de code staat. Verander de `korting`-formule in
het YAML en alle drie de "tools" (en elke echte Ossie-tool die het model leest)
veranderen tegelijk mee: **write once, query anywhere**.

### 4. AI-laag: `ai_context` als semantische anker

De UI/CLI matchen een vrije tekstvraag op metrics en dimensies via de
`synonyms` en `examples` uit het model. Dit is een bewuste vereenvoudiging van
een echte LLM-agent — het Ossie-principe blijft hetzelfde: de agent kiest uit
*gepaste, gevalideerde* definities in plaats van zelf een query te verzinnen.

## Waarom "moet" het zo?

- Het model **verplicht** eenduidigheid: metricnamen delen één namespace per
  dataset, key- en relatieverwijzingen *moeten* naar gedeclareerde velden,
  model-metrics *moeten* gekwalificeerd — de validatie in deze demo nagaat dit.
- Wie het model overtreedt, krijgt in álle tools tegelijk fout — dat is precies
  de governor-functie die "no more metric drift" waar moet maken.
- Vendor-specifieke wensen (dialecten, warehouse-namen) kunnen in `dialects` en
  `custom_extensions` zonder de kern te vervuilen.
