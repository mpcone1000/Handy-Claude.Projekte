"""Erzeugt alle Landschaften: Schematics (.litematic/.schem), Viewer-Daten, Vorschaubilder, Infos.

Aufruf:  python3 build.py [name ...]      (ohne Namen: alle)
"""
import importlib
import json
import os
import sys
import time

import numpy as np

import preview
from mclib import BLOCKS, beautify, export_litematic, export_palette_json, export_schem, export_viewer, material_list

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANDS = ["tal", "felsnadeln", "doline", "inseln", "unterwelt", "vulkan", "kombi_tuerkistal", "kombi_himmelsloch",
         "kombi_kaskaden"]


def crop(w, info, margin=1):
    """Schneidet leere Ränder ab und verschiebt alle Koordinaten in info entsprechend."""
    nz = w.b != 0
    ys = np.nonzero(nz.any(axis=(1, 2)))[0]
    zs = np.nonzero(nz.any(axis=(0, 2)))[0]
    xs = np.nonzero(nz.any(axis=(0, 1)))[0]
    y0, y1 = ys[0], min(w.H, ys[-1] + 1 + 6)
    z0, z1 = max(0, zs[0] - margin), min(w.D, zs[-1] + 1 + margin)
    x0, x1 = max(0, xs[0] - margin), min(w.W, xs[-1] + 1 + margin)
    w.b = np.ascontiguousarray(w.b[y0:y1, z0:z1, x0:x1])
    w.H, w.D, w.W = w.b.shape
    w.Z, w.X = np.meshgrid(np.arange(w.D, dtype=float), np.arange(w.W, dtype=float), indexing="ij")

    def sh(p):
        return (p[0] - x0, p[1] - y0, p[2] - z0)
    for z in info["zones"]:
        z["pos"] = sh(z["pos"])
    info["camera"] = dict(target=sh(info["camera"]["target"]), pos=sh(info["camera"]["pos"]))
    for k in ("ground_y", "water_level"):
        if info.get(k) is not None:
            info[k] = info[k] - y0
    if info.get("clip") is not None:
        info["clip"] = info["clip"] - y0
    info["paste_y"] = info["paste_y"] + y0


TYP_DE = dict(eingang="Eingang", wohnen="Wohnen", lager="Lager", farm="Farm", werkstatt="Werkstatt", shop="Shop",
              highlight="Highlight")


def fill_placeholders(w, info):
    """Ersetzt {paste_y}, {welt_max}, {water_world} in allen Texten durch echte Weltkoordinaten."""
    nz = (w.b != 0).any(axis=(1, 2))
    vals = dict(paste_y=info["paste_y"], welt_max=info["paste_y"] + int(np.nonzero(nz)[0][-1]),
                water_world=(info["paste_y"] + info["water_level"]) if info.get("water_level") is not None else "")

    def f(t):
        for k, v in vals.items():
            t = t.replace("{" + k + "}", str(v))
        return t
    info["story"] = [f(t) for t in info["story"]]
    info["tipps"] = [f(t) for t in info["tipps"]]
    info["phasen"] = [(f(a), f(b)) for a, b in info["phasen"]]
    info["paste_note"] = f(info.get("paste_note", ""))
    for z in info["zones"]:
        z["text"] = f(z["text"])


def write_readme(path, w, info, mats):
    from mclib import BLOCKS
    de = {b["key"]: b["de"] for b in BLOCKS}
    L = []
    L.append(f"# {info['nr']:02d} – {info['title']}\n")
    L.append(f"**{info['tagline']}**\n")
    L.append("![Draufsicht](draufsicht.png)\n")
    L.extend(t + "\n" for t in info["story"])
    L.append("## Eckdaten\n")
    L.append("| | |\n|---|---|")
    L.append(f"| Größe (B × L × H) | {w.W} × {w.D} × {w.H} Blöcke |")
    L.append(f"| Sichtbare Blöcke | {mats['sichtbar']:,} (≈ {mats['sichtbar'] // 1728:,} Shulker-Kisten) |".replace(",", "."))
    L.append(f"| Einfügehöhe | Unterkante der Schematic auf **Y {info['paste_y']}** |")
    L.append(f"| Hinweis | {info['paste_note']} |\n")
    L.append("## Orte in der Landschaft\n")
    L.append("Positionen sind Koordinaten innerhalb der Schematic (X, Y, Z ab der unteren Ecke).\n")
    L.append("| Nr. | Ort | Art | Position | Beschreibung |\n|---|---|---|---|---|")
    for i, z in enumerate(info["zones"]):
        x, y, zz = (int(v) for v in z["pos"])
        art = TYP_DE[z["typ"]] + (" (im Fels)" if z.get("innen") else "")
        L.append(f"| {i + 1} | {z['name']} | {art} | {x} / {y} / {zz} | {z['text']} |")
    L.append("\n## Bau-Reihenfolge\n")
    for i, (a, b) in enumerate(info["phasen"]):
        L.append(f"{i + 1}. **{a}**: {b}")
    L.append("\n## Tipps\n")
    L.extend(f"- {t}" for t in info["tipps"])
    L.append("\n## Materialliste (sichtbare Blöcke)\n")
    L.append("Gezählt sind nur Blöcke, die man sieht. Das Innere von Bergen und Inseln kann aus beliebigem "
             "Material sein.\n")
    L.append("| Block | Anzahl | Stacks | Shulker |\n|---|---:|---:|---:|")
    for k, v in sorted(mats["bloecke"].items(), key=lambda kv: -kv[1]["sichtbar"]):
        n = v["sichtbar"]
        L.append(f"| {de[k]} | {n:,} | {-(-n // 64):,} | {n / 1728:.1f} |".replace(",", "."))
    L.append("\n## Dateien\n")
    L.append(f"- `{info['slug']}.litematic`: für die Mod **Litematica**. Die Landschaft erscheint als "
             "Geisterblöcke in der Welt, und du baust sie Block für Block nach.")
    L.append(f"- `{info['slug']}.schem`: für **WorldEdit**. Mit `//paste -a` einfügen, damit Luft nichts überschreibt.")
    L.append("- `draufsicht.png`: Draufsicht als Bild.")
    L.append("\nDie 3D-Ansicht mit allen Orten gibt es im Viewer (`../../viewer/index.html`).")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def build(modname, previews_only=False):
    t0 = time.time()
    mod = importlib.import_module(modname)
    w, info = mod.generate()
    crop(w, info)
    beautify(w, seed=info["nr"], green_ledges=info.get("green_ledges", True))
    fill_placeholders(w, info)
    slug = info["slug"]
    nr = info["nr"]
    t1 = time.time()
    folder = os.path.join(ROOT, "landschaften", f"{nr:02d}-{slug}")
    vdir = os.path.join(ROOT, "viewer", "data")
    os.makedirs(folder, exist_ok=True)
    os.makedirs(vdir, exist_ok=True)
    preview.topdown(w, os.path.join(folder, "draufsicht.png"), scale=1)
    if previews_only:
        scratch = os.environ.get("PREVIEW_DIR", "/tmp")
        preview.topdown(w, os.path.join(scratch, f"{slug}_top.png"), scale=2)
        print(f"{modname}: generiert in {t1 - t0:.1f}s (nur Vorschau)")
        return w, info
    mats = material_list(w)
    nbytes = export_viewer(w, os.path.join(vdir, f"{slug}.txt"))
    export_schem(w, os.path.join(folder, f"{slug}.schem"), info["title"])
    export_litematic(w, os.path.join(folder, f"{slug}.litematic"), info["title"], info["tagline"])
    meta = dict(info)
    meta["size"] = [w.W, w.H, w.D]
    meta["materials"] = mats
    meta["zones"] = [dict(z, pos=[int(v) for v in z["pos"]]) for z in info["zones"]]
    meta["bin_bytes"] = nbytes
    write_readme(os.path.join(folder, "README.md"), w, info, mats)
    with open(os.path.join(vdir, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=lambda o: o.tolist())
    print(f"{modname}: generiert {t1 - t0:.1f}s, export {time.time() - t1:.1f}s, viewer {nbytes / 1e6:.2f} MB, "
          f"sichtbare Blöcke {mats['sichtbar']:,}")
    return w, info


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    po = "--preview" in sys.argv
    export_palette_json(os.path.join(ROOT, "viewer", "data", "palette.json")) if not po else None
    for name in args or LANDS:
        build(name, previews_only=po)
