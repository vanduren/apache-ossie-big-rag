# De relatie tussen Apache Ossie en een AI-model

**Vraag:** Wat is de relatie tussen Ossie en een AI-model?

Korte samenvatting van wat ik in dit project zie:

## Ossie ís geen AI-model — het is de context eromheen

**Apache Ossie** is een open standaard voor het *uitwisselen van semantische modellen*: datasets, velden, metrics, relaties. Een AI-model (LLM, agent) is de *consument* van die standaard. De relatie is dus: **Ossie levert de zakelijke betekenis, het AI-model levert het taalbegrip.**

Concreet, in drie richtingen:

**1. Ossie → AI: "AI-ready context" via `ai_context`**
Het Ossie-model (`models/knol_en_bloei.ossie.yaml`) bevat op model-, metric- en veldniveau `ai_context`-blokken met synoniemen, voorbeeldvragen en instructies. Een AI-agent gebruikt die om een vrije-tekstvraag ("hoeveel ging er van rozen weg?") te vertalen naar de juiste metric/dimensie (`omzet`, `product`) — en daarna via het model naar correcte SQL. Dat is precies wat [app/ossie_core.py](app/ossie_core.py) nabootst met een eenvoudige keyword-matcher in plaats van een LLM.

**2. AI → Ossie: natürtaal wordt de nieuwe query-taal**
Zonder Ossie moet een LLM uit de losse pols SQL schrijven tegen ruwe tabellen → veel kans op hallucinaties (verkeerde joins, foute definitie van "omzet"). Mét Ossie is de wereld beperkt tot gedefinieerde metrics en relatiepaden: het model kan alleen *kiezen* wat er al gedefinieerd is, niet zelf businesslogica verzinnen. Het semantisch laag fungeert als grondfeiten-laag (grounding).

**3. Één model, vele consumenten ("query anywhere")**
Ossie is vendor-neutraal: dezelfde YAML wordt geconsumeerd door een BI-tool, een CLI, een dashboard én een AI-agent. In deze demo bewijzen de GUI en [scripts/cli_vraag.py](scripts/cli_vraag.py) precies dat. Extra bonus: een AI-model kan ook *aan de andere kant* staan en zelf Ossie-modellen genereren of bijwerken — de standaard is YAML, dus lees- en schrijfbaar voor een LLM.

**Kernformule:** het AI-model begrijpt de vraag, het Ossie-model kent het antwoord — samen worden ze pas bruikbaar voor "vraag het maar" analytics.
