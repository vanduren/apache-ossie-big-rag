"""Build a small, dependency-free Office Open XML PowerPoint."""
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "apache-ossie-knol-en-bloei.pptx"
W, H = 12192000, 6858000  # 13.333 x 7.5 in, EMU

slides = [
    ("Apache Ossie", "Eén semantisch model, meerdere toepassingen\n\nDe bloemenwebshop Knol & Bloei\nSQLite · YAML-model · Python UI · CLI", "ossie-stroom.svg"),
    ("Het probleem: metric drift", "Verschillende tools kunnen hetzelfde begrip anders definiëren.\n\nEen gedeelde modeldefinitie maakt afspraken zichtbaar.", "metric-drift.svg"),
    ("Wat is Apache Ossie?", "• Open specificatie voor uitwisseling van semantische metadata\n• Beschrijft datasets, velden, metrics en relaties\n• Helpt verschillende consumers dezelfde begrippen te gebruiken\n• Dit projectmodel staat in models/knol_en_bloei.ossie.yaml", None),
    ("De bouwstenen van het model", "Voorbeeld: regelbedrag na korting, opgeteld tot netto-omzet.", "model-bouwstenen.svg"),
    ("De projectdemo", "• Zeven datasets voor verkoop, klanten, producten, leveranciers, verzendingen en reviews\n• SQLite bevat de webshopdata; CSV's zijn de voorbeeldbronnen\n• Een Python-consumer leest het YAML-model en genereert SQL\n• De desktopinterface en CLI gebruiken dezelfde querylogica", None),
    ("Van vraag naar antwoord", "Voorbeeldvraag: omzet per productcategorie.", "query-pad.svg"),
    ("Wat gebeurt er bij een analyse?", "• Kies orderregels.omzet en producten.categorie\n• De consumer vertaalt velden en relationships naar SQL\n• De demo toont query, resultaten en grafiek\n\nNetto-omzet = aantal × prijs per stuk × (1 − korting)", None),
    ("Een vraag in gewone taal", "• ai_context bevat synoniemen en voorbeeldvragen\n• De demo koppelt herkende termen aan modeldefinities\n• Dit is een regelgebaseerde matcher, geen LLM\n• Semantische metadata kan een taalinterface sturen", None),
    ("Demo in drie stappen", "1. Bekijk het model: datasets, velden, metrics en relaties\n2. Analyseer omzet per categorie; vergelijk bruto en netto\n3. Stel dezelfde vraag via de CLI en de vraagtab\n\nOpstarten: uv sync\nuv run python app/webshop_demo.py", None),
    ("Wat laat deze demo zien?", "• Eén model kan definities leveren aan meerdere consumers\n• Metrics en relaties maken aannames bespreekbaar\n• De meegeleverde consumer implementeert een leerzame subset\n• Toets productiegebruik aan de actuele officiële specificatie\n\nOefening: demo/mini-cursus.md", None),
]


def xml_text(text, x, y, w, h, size, color="173B32", bold=False):
    paras = []
    for line in text.split("\n"):
        b = '<a:rPr lang="nl-NL" sz="%d" b="%s"><a:solidFill><a:srgbClr val="%s"/></a:solidFill><a:latin typeface="Aptos"/></a:rPr>' % (size, "1" if bold else "0", color)
        paras.append('<a:p><a:pPr algn="l"/><a:r>%s<a:t xml:space="preserve">%s</a:t></a:r><a:endParaRPr lang="nl-NL" sz="%d"/></a:p>' % (b, escape(line), size))
    return '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Text"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>%s</p:txBody></p:sp>' % (x, y, w, h, "".join(paras))


def slide_xml(title, body, image=None):
    pic = ""
    if image:
        pic = '<p:pic><p:nvPicPr><p:cNvPr id="3" name="Diagram"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="6400000" y="1700000"/><a:ext cx="5400000" cy="3000000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
        body_w = 5800000
    else:
        body_w = 10800000
    shapes = xml_text(title, 620000, 330000, 11000000, 700000, 3000, bold=True)
    shapes += xml_text(body, 700000, 1500000, body_w, 4600000, 2100, "2D3733")
    shapes += pic
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="F5F2EA"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
            '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>' + shapes + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def main():
    n = len(slides)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        types = ['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>', '<Default Extension="xml" ContentType="application/xml"/>', '<Default Extension="svg" ContentType="image/svg+xml"/>', '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>', '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>', '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>']
        for i in range(1, n + 1):
            types.append('<Override PartName="/ppt/slides/slide%d.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' % i)
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">%s</Types>' % ''.join(types))
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        ids = ''.join('<p:sldId id="%d" r:id="rId%d"/>' % (255 + i, i) for i in range(1, n + 1))
        z.writestr('ppt/presentation.xml', '<?xml version="1.0" encoding="UTF-8"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId%d"/></p:sldMasterIdLst><p:sldIdLst>%s</p:sldIdLst><p:sldSz cx="%d" cy="%d" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>' % (n + 1, ids, W, H))
        rels = ''.join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide%d.xml"/>' % (i, i) for i in range(1, n + 1))
        rels += '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>' % (n + 1)
        z.writestr('ppt/_rels/presentation.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s</Relationships>' % rels)
        for i, (title, body, image) in enumerate(slides, 1):
            z.writestr('ppt/slides/slide%d.xml' % i, slide_xml(title, body, image))
            relationships = '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            if image:
                media_name = 'diagram-' + image
                relationships += '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/%s"/>' % media_name
                z.write(ROOT / 'afbeeldingen' / image, 'ppt/media/' + media_name)
            z.writestr('ppt/slides/_rels/slide%d.xml.rels' % i, '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s</Relationships>' % relationships)
        z.writestr('ppt/slideLayouts/slideLayout1.xml', '<?xml version="1.0" encoding="UTF-8"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
        z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>')
        z.writestr('ppt/slideMasters/slideMaster1.xml', '<?xml version="1.0" encoding="UTF-8"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld name="Master"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>')
        z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>')
    print(OUT)


if __name__ == '__main__':
    main()
