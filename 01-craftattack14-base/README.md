# 01 – Craft Attack 14: Base-Landschaften

Keine Häuser, sondern **sechs riesige, besondere Landschaften**. In jede ist die ganze Base eingebaut: Lager, Farmen, Wohnbereich, Werkstatt, Shop und Eingang.
Jede Landschaft ist Block für Block als 3D-Modell geplant und kann direkt in Minecraft geladen werden.

## Die sechs Landschaften

| Nr. | Landschaft | Idee | Größe (B × L × H) | Sichtbare Blöcke |
|---|---|---|---|---|
| 1 | [Das versteckte Tal](landschaften/01-verstecktes-tal/) | Rundum Felswände, rein kommt man nur durch einen Tunnel hinter einem Wasserfall. Innen liegen See, Felsbogen, Kirschwiese und Terrassen. | 300 × 599 × 175 | 537.375 |
| 2 | [Die Felsnadeln](landschaften/02-felsnadeln/) | 45 Felstürme bis 188 Blöcke hoch im Urwald. Die Base verteilt sich auf fünf Türme, verbunden durch Hängebrücken. Dazu ein gläserner Wasser-Aufzug und schwebende Felsen. | 347 × 525 × 228 | 632.462 |
| 3 | [Die Riesen-Doline](landschaften/03-riesen-doline/) | Ein 120 Blöcke breites, 78 Blöcke tiefes Loch im Dschungel. Ein Spiralweg führt hinab zu einem türkisen See mit Riesenbaum, unten liegt ein Raum unter Wasser. | 326 × 407 × 139 | 474.170 |
| 4 | [Die schwebenden Inseln](landschaften/04-schwebende-inseln/) | Fast 30 Inseln im Himmel. Auf der Hauptinsel steht ein riesiger Kirschbaum, dessen Wurzeln unten heraushängen. Ein Wasserfall stürzt ins Leere, ein Blasen-Aufzug führt hinauf. | 331 × 454 × 227 | 187.262 |
| 5 | [Die leuchtende Unterwelt](landschaften/05-leuchtende-unterwelt/) | Oben eine normale Wiese, darunter eine riesige Höhle mit Riesenpilzen, Leuchtbeeren, unterirdischem See und Amethyst-Geode. | 320 × 439 × 130 | 596.279 |
| 6 | [Die Vulkaninsel](landschaften/06-vulkaninsel/) | Vulkan mit Lavasee, Lavaströme, Dschungel, türkise Lagune, schwarzer Strand und ein Hafen mit Leuchtfeuer. | 323 × 473 × 160 | 346.753 |

In jedem Landschafts-Ordner liegen:
- `README.md`: genaue Beschreibung mit allen Orten (Koordinaten), Bau-Reihenfolge, Tipps und vollständiger Materialliste
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

## Selbst verändern

Alle Landschaften werden von Python-Skripten erzeugt (`generator/`). Man kann sie anpassen, zum Beispiel Größe, Lage der Räume oder Baumarten, und neu erzeugen:

```bash
cd generator
python3 build.py              # alle sechs Landschaften
python3 build.py tal vulkan   # nur einzelne
python3 verify.py             # prüft, ob .schem/.litematic korrekt lesbar sind
```

Benötigt wird nur Python 3 mit `numpy` und `Pillow`.

| Datei | Inhalt |
|---|---|
| `generator/mclib.py` | Bausteine: Blöcke, Gelände-Rauschen, Bäume, Felsnadeln, Inseln, Brücken, Export |
| `generator/tal.py` … `vulkan.py` | je eine Landschaft |
| `generator/build.py` | erzeugt Schematics, Viewer-Daten, Draufsichten und READMEs |
| `generator/verify.py` | liest die Schematics zurück und vergleicht sie Block für Block |
| `generator/preview.py` | Draufsicht- und Schnittbilder zum Prüfen |
