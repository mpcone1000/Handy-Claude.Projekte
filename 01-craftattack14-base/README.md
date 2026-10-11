# 01 – Craft Attack 14: Base-Landschaften

Keine Häuser, sondern **riesige, besondere Landschaften**: sechs Grundideen und drei Kombinationen. In jede ist die ganze Base eingebaut: Lager, Farmen, Wohnbereich, Werkstatt, Shop und Eingang.
Jede Landschaft ist Block für Block als 3D-Modell geplant und kann direkt in Minecraft geladen werden.

## Die sechs Landschaften

| Nr. | Landschaft | Idee | Größe (B × L × H) | Sichtbare Blöcke |
|---|---|---|---|---|
| 1 | [Das versteckte Tal](landschaften/01-verstecktes-tal/) | Rundum Felswände, rein kommt man nur durch einen Tunnel hinter einem Wasserfall. Innen liegen See, Felsbogen, Kirschwiese und Terrassen. | 297 × 599 × 175 | 537.730 |
| 2 | [Die Felsnadeln](landschaften/02-felsnadeln/) | 45 Felstürme bis 188 Blöcke hoch im Urwald. Die Base verteilt sich auf fünf Türme, verbunden durch Hängebrücken. Dazu ein gläserner Wasser-Aufzug und schwebende Felsen. | 343 × 522 × 232 | 630.156 |
| 3 | [Die Riesen-Doline](landschaften/03-riesen-doline/) | Ein 120 Blöcke breites, 78 Blöcke tiefes Loch im Dschungel. Ein Spiralweg führt hinab zu einem türkisen See mit Riesenbaum, unten liegt ein Raum unter Wasser. | 326 × 407 × 139 | 474.751 |
| 4 | [Die schwebenden Inseln](landschaften/04-schwebende-inseln/) | Fast 30 Inseln im Himmel. Auf der Hauptinsel steht ein riesiger Kirschbaum, dessen Wurzeln unten heraushängen. Ein Wasserfall stürzt ins Leere, ein Blasen-Aufzug führt hinauf. | 332 × 454 × 227 | 186.862 |
| 5 | [Die leuchtende Unterwelt](landschaften/05-leuchtende-unterwelt/) | Oben eine normale Wiese, darunter eine riesige Höhle mit Riesenpilzen, Leuchtbeeren, unterirdischem See und Amethyst-Geode. | 320 × 439 × 130 | 595.442 |
| 6 | [Die Vulkaninsel](landschaften/06-vulkaninsel/) | Vulkan mit Lavasee, Lavaströme, Dschungel, türkise Lagune, schwarzer Strand und ein Hafen mit Leuchtfeuer. | 323 × 473 × 160 | 345.010 |

### Kombinationen mit türkisem See

| Nr. | Landschaft | Kombiniert | Idee | Größe (B × L × H) | Sichtbare Blöcke |
|---|---|---|---|---|---|
| 7 | [Das Türkis-Tal](landschaften/07-tuerkis-tal/) | Tal + See + Inseln | Bergring mit geheimem Tunnel. Der Talboden ist ein türkiser See mit Wohninsel, Farminsel, Felsturm-Lager und Palmeninseln. Darüber schweben vier Inseln, eine mit Wasserfall, und ein Blasen-Aufzug führt hinauf. | 322 × 539 × 162 | 508.338 |
| 8 | [Das Himmelsloch](landschaften/08-himmelsloch/) | Doline + Inseln + See | Riesenloch im Dschungel. In der Glocke schweben vier Inseln mit Kirschbaum über einem flachen türkisen See, verbunden über Hängebrücken mit dem Spiralweg an der Wand. | 339 × 423 × 145 | 483.274 |
| 9 | [Das Kaskaden-Tal](landschaften/09-kaskaden-tal/) | Tal + See + Doline | Fünf türkise Seen in Stufen in einer Waldschlucht, zwanzig Kaskaden über Sinterdämme, Holzstege im Zickzack. Der Wohnbereich liegt hinter einem großen Wasserfall, am Ende stürzt alles in ein Riesenloch. | 320 × 580 × 139 | 524.000 |

In jedem Landschafts-Ordner liegen:
- `README.md`: genaue Beschreibung mit allen Orten (Koordinaten), Bau-Reihenfolge, Tipps und vollständiger Materialliste (ohne Deko wie Gras, Blumen, Ranken und Seerosen)
- `*.litematic`: für die Mod **Litematica**. Die Landschaft wird als Geisterblöcke in die Welt projiziert, und du baust sie Block für Block nach.
- `*.schem`: für **WorldEdit** (mit `//paste -a` einfügen, damit Luft nichts überschreibt)
- `draufsicht.png`: Draufsicht als Bild

## 3D-Viewer

**Online ansehen:** https://claude.ai/artifact/8tPwBeG1DqBeGZPsFD8EQr

In `viewer/index.html` kannst du jede Landschaft in 3D drehen und zoomen, auch auf dem Handy. Der Viewer kann:
- alle Orte der Base als nummerierte Punkte anzeigen; antippen fliegt hin und erklärt den Ort
- die Landschaft mit dem **Schnitt-Regler** von oben abschneiden, um in Höhlen und Räume im Fels zu schauen
- auf **Nacht** umschalten, dann leuchten Laternen, Lava, Pilzlichter und Leuchtbeeren
- einen **Rundflug** zeigen

Die Grafik zeigt Minecraft-artige Block-Texturen, weiche Schatten und Licht wie mit Smooth Lighting, Sonnenschatten, Wolken und bewegtes Wasser.

## Selbst verändern

Alle Landschaften werden von Python-Skripten erzeugt (`generator/`). Man kann sie anpassen, zum Beispiel Größe, Lage der Räume oder Baumarten, und neu erzeugen:

```bash
cd generator
python3 build.py              # alle neun Landschaften
python3 build.py tal vulkan   # nur einzelne
python3 verify.py             # prüft, ob .schem/.litematic korrekt lesbar sind
```

Benötigt wird nur Python 3 mit `numpy` und `Pillow`.

| Datei | Inhalt |
|---|---|
| `generator/mclib.py` | Bausteine: Blöcke, Gelände-Rauschen, Bäume, Felsnadeln, Inseln, Brücken, Export |
| `generator/tal.py` … `vulkan.py` | die sechs Grundideen |
| `generator/kombi_*.py` | die drei Kombinationen |
| `generator/build.py` | erzeugt Schematics, Viewer-Daten, Draufsichten und READMEs |
| `generator/verify.py` | liest die Schematics zurück und vergleicht sie Block für Block |
| `generator/preview.py` | Draufsicht- und Schnittbilder zum Prüfen |
