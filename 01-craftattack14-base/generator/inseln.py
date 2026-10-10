"""Landschaft 4: Die schwebenden Inseln.

Ein Archipel aus über 20 schwebenden Inseln. Auf der Hauptinsel wächst ein riesiger Kirschbaum, dessen
Wurzeln unten aus dem Fels hängen. Jede größere Insel hat eine Aufgabe.
"""
import numpy as np

from mclib import (B, OCCLUDES, World, bridge, bush, carve_room, fbm2, float_island, leaf_blob, paint_path,
                   scatter_points, smooth_polyline, smoothstep, tree_big, tree_cherry, tree_round, tree_spruce,
                   vine_curtain)

W, H, D = 380, 236, 500
SLUG = "schwebende-inseln"
PASTE_Y = 90           # Unterkante der Schematic auf Y 90 → Boden der Welt liegt 27 Blöcke darunter, Spitze bleibt unter Y 320


def raise_hill(w, cx, cz, r, hgt, seed=0):
    top = w.column_top()
    X, Z = w.X, w.Z
    d = np.hypot(X - cx, Z - cz) / r + fbm2(X, Z, 10, 2, seed) * 0.12
    k = np.clip(1 - d, 0, 1)
    add = (smoothstep(0, 1, k) * hgt).astype(int)
    zz, xx = np.nonzero((add > 0) & (top > 0))
    for z, x in zip(zz, xx):
        t = top[z, x]
        if w.b[t, z, x] not in (B("grass"), B("dirt")):
            continue
        a = add[z, x]
        w.b[t:t + a, z, x] = B("stone")
        w.b[max(t, t + a - 3):t + a, z, x] = B("dirt")
        w.b[t + a, z, x] = B("grass")


def fall_off(w, x0, x1, z0, z1, y_top):
    """Wasserfall ins Leere: Wasser fällt senkrecht bis zur Unterkante der Schematic."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(int(y_top), -1, -1):
                b = w.b[y, z, x]
                if b == 0:
                    w.b[y, z, x] = B("water")
                elif OCCLUDES[b] and y < y_top - 1:
                    break


def generate():
    w = World(W, H, D, seed=44)
    rng = w.rng
    isl = {}

    def island(name, cx, cy, cz, rx, rz, depth, seed):
        float_island(w, cx, cy, cz, rx, rz, depth, seed=seed)
        isl[name] = dict(x=cx, y=cy, z=cz, rx=rx, rz=rz, depth=depth)

    island("haupt", 190, 150, 250, 72, 86, 96, 1)
    island("farm", 318, 136, 128, 34, 30, 42, 2)
    island("lager", 64, 160, 150, 30, 34, 48, 3)
    island("shop", 196, 124, 440, 34, 28, 36, 4)
    island("werk", 326, 166, 340, 26, 28, 40, 5)
    island("zauber", 58, 184, 340, 17, 15, 26, 6)
    island("aussicht", 236, 206, 64, 11, 11, 22, 7)

    # Deko-Inseln, Sprungpfad zur Aussichtsinsel
    step = [(214, 160, 158), (222, 170, 130), (230, 181, 106), (236, 192, 86)]
    for i, (x, y, z) in enumerate(step):
        float_island(w, x, y, z, 6, 6, 8, seed=50 + i)
    deco = []
    for i in range(18):
        for _ in range(60):
            x, z = rng.uniform(25, W - 25), rng.uniform(25, D - 25)
            r = rng.uniform(5, 14)
            ok = all(np.hypot(x - v["x"], z - v["z"]) > max(v["rx"], v["rz"]) + r + 10 for v in isl.values())
            ok = ok and all(np.hypot(x - a, z - c) > r + b + 8 for a, c, b in deco)
            if ok:
                y = rng.uniform(70, 200)
                float_island(w, x, y, z, r, r * rng.uniform(0.7, 1.2), r * rng.uniform(1.2, 2.2), seed=80 + i)
                deco.append((x, z, r))
                break

    # ---------------- Hauptinsel ----------------
    m = isl["haupt"]
    raise_hill(w, 176, 200, 34, 20, seed=3)
    raise_hill(w, 236, 300, 22, 9, seed=4)
    top = w.column_top()
    # See mit Abfluss über die Kante
    lx, lz, lr = 214, 262, 15
    X, Z = w.X, w.Z
    lake = np.hypot(X - lx, Z - lz) + fbm2(X, Z, 7, 2, 9) * 2 < lr
    chan = (np.abs(Z - lz) < 2.5) & (X > lx) & (X < m["x"] + m["rx"] + 6)
    zz, xx = np.nonzero(lake | chan)
    wl = int(np.median(top[lake]))
    for z, x in zip(zz, xx):
        t = top[z, x]
        if t <= 0:
            continue
        depth = 5 if lake[z, x] else 2
        w.b[wl - depth + 1:t + 1, z, x] = 0
        w.b[wl - depth, z, x] = B("sand") if lake[z, x] else B("gravel")
        w.b[wl - depth + 1:wl + 1, z, x] = B("water")
    edge_x = int(m["x"] + m["rx"])
    for x in range(lx, W):
        if w.b[wl, lz, x] == 0 and not OCCLUDES[w.b[wl - 1, lz, x]]:
            edge_x = x
            break
    fall_off(w, edge_x, edge_x + 1, lz - 2, lz + 2, wl)

    # Weltenbaum (Kirsche) mit Wurzeln, die unten aus der Insel hängen
    tx, tz = 172, 262
    ty = int(w.column_top()[tz, tx]) + 1
    tree_big(w, tx, ty, tz, h=58, trunk_r=4.6, log="cherry_log", leaf="cherry_leaves", crown=27, branches=10,
             leaf2="flowering_azalea_leaves")
    bot = m["y"] - m["depth"]
    for k in range(9):
        a = k / 9 * 2 * np.pi + rng.uniform(-0.2, 0.2)
        ex = tx + np.cos(a) * rng.uniform(10, 26)
        ez = tz + np.sin(a) * rng.uniform(10, 26)
        ey = bot + rng.uniform(-28, 10)
        w.line((tx, ty - 3, tz), (ex, ey, ez), B("cherry_log"), r=1.1 if k % 2 else 0.7)
        for j in range(int(rng.integers(6, 16))):
            w.set(ex, ey - 1 - j, ez, B("hanging_roots"), only_air=True)

    # Wohnbereich im Hügel mit Glasfront zum Baum
    hx, hz = 176, 200
    hy = int(w.column_top()[hz + 20, hx]) + 1
    carve_room(w, hx - 13, hy, hz - 14, hx + 13, hy + 9, hz + 6, floor="spruce_planks", light="lantern",
               round_=True)
    w.box(hx - 10, hy, hz + 6, hx + 10, hy + 7, hz + 22, 0)
    zf = hz + 7
    for z in range(hz + 6, hz + 24):
        if OCCLUDES[w.b[hy + 8, z, hx]] or OCCLUDES[w.b[hy + 4, z, hx - 9]]:
            zf = z
    w.box(hx - 10, hy, hz + 6, hx + 10, hy + 7, zf, 0)
    w.box(hx - 10, hy, zf, hx + 10, hy + 7, zf, B("glass"))
    w.box(hx - 1, hy, zf, hx + 1, hy + 3, zf, 0)
    w.box(hx - 10, hy - 1, hz + 6, hx + 10, hy - 1, zf + 4, B("spruce_planks"))
    w.box(hx - 13, hy, hz - 14, hx - 13, hy + 3, hz + 4, B("bookshelf"))
    wohn = (hx, hy + 1, hz - 2)

    # Garten und Wege auf der Hauptinsel
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    grass = gb == B("grass")
    near_main = np.hypot((X - m["x"]) / m["rx"], (Z - m["z"]) / m["rz"]) < 0.9
    for z, x in scatter_points(w, grass & near_main & (np.hypot(X - tx, Z - tz) > 24), 22, 14):
        tree_cherry(w, x, top[z, x] + 1, z) if rng.random() < 0.5 else tree_round(
            w, x, top[z, x] + 1, z, log="birch_log", leaf="birch_leaves")
    for z, x in scatter_points(w, grass & near_main, 90, 5):
        bush(w, x, top[z, x] + 1, z, leaf="flowering_azalea_leaves" if rng.random() < 0.6 else "azalea_leaves")

    # ---------------- Farminsel ----------------
    f = isl["farm"]
    top = w.column_top()
    for z in range(f["z"] - 18, f["z"] + 18):
        for x in range(f["x"] - 22, f["x"] + 22):
            t = top[z, x]
            if t > 0 and w.b[t, z, x] == B("grass"):
                if (x - f["x"]) % 9 == 0:
                    w.b[t, z, x] = B("water")
                elif z < f["z"] + 4:
                    w.b[t, z, x] = B("farmland")
                    w.set(x, t + 1, z, B("wheat"))
    for (x0, z0) in ((f["x"] - 20, f["z"] + 7), (f["x"] + 2, f["z"] + 7)):
        for x in range(x0, x0 + 17):
            for z in (z0, z0 + 10):
                w.set(x, top[z, x] + 1, z, B("spruce_fence"), only_air=True)
        for z in range(z0, z0 + 11):
            for x in (x0, x0 + 16):
                w.set(x, top[z, x] + 1, z, B("spruce_fence"), only_air=True)
        w.set(x0 + 8, top[z0 + 5, x0 + 8] + 1, z0 + 5, B("hay"))
    farm = (f["x"], int(top[f["z"], f["x"]]) + 1, f["z"])

    # ---------------- Lagerinsel (innen hohl) ----------------
    g = isl["lager"]
    ly = g["y"] - 16
    carve_room(w, g["x"] - 16, ly, g["z"] - 18, g["x"] + 16, ly + 11, g["z"] + 18, floor="spruce_planks",
               light="lantern")
    for x in range(g["x"] - 14, g["x"] + 15, 3):
        w.box(x, ly, g["z"] - 12, x, ly + 2, g["z"] + 12, B("barrel"))
    w.box(g["x"] - 1, ly, g["z"] + 17, g["x"] + 1, g["y"] + 3, g["z"] + 19, 0)
    for k in range(0, g["y"] + 2 - ly):
        w.set(g["x"], ly + k, g["z"] + 20, B("stripped_spruce_log"))
    lager = (g["x"], ly + 1, g["z"])

    # ---------------- Shopinsel ----------------
    s = isl["shop"]
    top = w.column_top()
    sy = int(top[s["z"], s["x"]]) + 1
    w.box(s["x"] - 18, sy - 1, s["z"] - 14, s["x"] + 18, sy - 1, s["z"] + 14, B("stone_bricks"))
    w.box(s["x"] - 18, sy, s["z"] - 14, s["x"] + 18, sy + 14, s["z"] + 14, 0, replace=[B("grass"), B("dirt"),
                                                                                      B("stone"), B("andesite")])
    for x in range(s["x"] - 15, s["x"] + 16, 6):
        for z in (s["z"] - 8, s["z"] + 8):
            w.box(x, sy, z, x + 2, sy, z, B("barrel"))
            w.set(x + 1, sy + 1, z, B("lantern"))
    # Blasen-Aufzug vom Boden zur Shopinsel
    ex, ez = s["x"] + 22, s["z"]
    w.set(ex, 0, ez, B("soul_sand"))
    for y in range(1, sy + 2):
        w.set(ex, y, ez, B("water"))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            w.set(ex + dx, y, ez + dz, B("glass"))
    w.set(ex - 1, sy, ez, 0)
    w.set(ex - 1, sy + 1, ez, 0)
    shop = (s["x"], sy, s["z"])

    # ---------------- Werkstatt ----------------
    k = isl["werk"]
    ky = k["y"] - 6
    carve_room(w, k["x"] - 12, ky, k["z"] - 10, k["x"] + 8, ky + 7, k["z"] + 10, floor="stone_bricks",
               light="lantern")
    w.box(k["x"] + 8, ky, k["z"] - 6, k["x"] + 30, ky + 6, k["z"] + 6, 0)
    w.box(k["x"] + 8, ky - 1, k["z"] - 6, k["x"] + 30, ky - 1, k["z"] + 6, B("stone_bricks"))
    for i, blk in enumerate(["crafting_table", "smithing_table", "anvil", "blast_furnace", "blast_furnace", "barrel"]):
        w.set(k["x"] - 10, ky, k["z"] - 7 + i * 3, B(blk))
    werk = (k["x"] - 2, ky + 1, k["z"])

    # ---------------- Verzauberungsinsel ----------------
    v = isl["zauber"]
    top = w.column_top()
    vy = int(top[v["z"], v["x"]]) + 1
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        if np.cos(a) < -0.85:
            continue
        w.set(v["x"] + 4 * np.cos(a), vy, v["z"] + 4 * np.sin(a), B("bookshelf"))
        w.set(v["x"] + 4 * np.cos(a), vy + 1, v["z"] + 4 * np.sin(a), B("bookshelf"))
    w.set(v["x"], vy, v["z"], B("lantern"))
    tree_cherry(w, v["x"] + 7, int(top[v["z"] + 5, v["x"] + 7]) + 1, v["z"] + 5)
    zauber = (v["x"], vy, v["z"])

    # ---------------- Aussichtsinsel ----------------
    a_ = isl["aussicht"]
    top = w.column_top()
    ay = int(top[a_["z"], a_["x"]]) + 1
    w.box(a_["x"] - 4, ay, a_["z"] - 4, a_["x"] + 4, ay, a_["z"] + 4, B("spruce_planks"))
    w.box(a_["x"] - 4, ay + 1, a_["z"] - 4, a_["x"] + 4, ay + 8, a_["z"] + 4, 0)
    for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        w.set(a_["x"] + dx, ay + 1, a_["z"] + dz, B("spruce_fence"))
        w.set(a_["x"] + dx, ay + 2, a_["z"] + dz, B("lantern"))

    # ---------------- Brücken ----------------
    def edge(name, toward, y=None):
        c = isl[name]
        d = np.array([toward[0] - c["x"], toward[1] - c["z"]], float)
        d /= np.linalg.norm(d)
        topm = w.column_top()
        last = None
        for r in np.arange(0, 120, 0.5):
            x, z = int(c["x"] + d[0] * r), int(c["z"] + d[1] * r)
            if not (0 <= x < W and 0 <= z < D) or topm[z, x] < 0 or abs(topm[z, x] - c["y"]) > 30:
                break
            last = (x, int(topm[z, x]), z)
        return last

    def link(a, b, sag):
        pa = edge(a, (isl[b]["x"], isl[b]["z"]))
        pb = edge(b, (isl[a]["x"], isl[a]["z"]))
        if pa and pb:
            bridge(w, (pa[0], pa[1] + 1, pa[2]), (pb[0], pb[1] + 1, pb[2]), sag=sag)
    link("haupt", "farm", 6)
    link("haupt", "lager", 7)
    link("haupt", "shop", 6)
    link("haupt", "werk", 6)
    link("lager", "zauber", 8)

    # ---------------- Hängende Ketten und Lianen ----------------
    for name, c in isl.items():
        for _ in range(3 if c["rx"] > 25 else 1):
            ang = rng.uniform(0, 2 * np.pi)
            x = c["x"] + np.cos(ang) * c["rx"] * 0.5
            z = c["z"] + np.sin(ang) * c["rz"] * 0.5
            # unterste feste Stelle der Spalte suchen
            col = OCCLUDES[w.b[:, int(z), int(x)]]
            if not col.any():
                continue
            yb = int(np.argmax(col))
            for y in range(yb - 1, max(0, yb - int(rng.integers(12, 34))), -1):
                w.set(x, y, z, B("chain"), only_air=True)
            w.set(x, y - 1, z, B("lantern"), only_air=True)
        for _ in range(int(c["rx"] / 4)):
            ang = rng.uniform(0, 2 * np.pi)
            vine_curtain(w, c["x"], c["z"], c["y"] - 1, rng.uniform(6, 22), ang, leaf="azalea_leaves", width=2)

    # Kleine Bäume auf den Deko-Inseln
    top = w.column_top()
    for x, z, r in deco:
        x, z = int(x), int(z)
        if top[z, x] > 0 and w.b[top[z, x], z, x] == B("grass"):
            if r > 8:
                tree_round(w, x, top[z, x] + 1, z, log="oak_log", leaf="azalea_leaves" if r % 2 > 1 else "oak_leaves")
            else:
                bush(w, x, top[z, x] + 1, z, leaf="flowering_azalea_leaves")
    for (x, y, z) in step:
        bush(w, x, int(w.column_top()[z, x]) + 1, z, leaf="flowering_azalea_leaves", r=1.5)

    zones = [
        dict(name="Blasen-Aufzug", typ="eingang", pos=(ex, 4, ez),
             text="Ein gläserner Wasser-Aufzug mit Seelensand am Boden bringt dich in Sekunden vom Erdboden "
                  "zur Shopinsel. Mit Elytren landest du auch direkt auf dem Marktplatz."),
        dict(name="Shopinsel", typ="shop", pos=shop,
             text="Ein Marktplatz aus Steinziegeln mit acht Ständen. Er ist die Ankunftsinsel für Besucher und "
                  "über eine Hängebrücke mit der Hauptinsel verbunden."),
        dict(name="Weltenbaum", typ="highlight", pos=(tx, ty + 30, tz),
             text="Ein 58 Blöcke hoher Kirschbaum mit über 50 Blöcke breiter Krone. Seine Wurzeln wachsen durch die "
                  "Insel und hängen unten frei in der Luft."),
        dict(name="Wohnbereich im Hügel", typ="wohnen", innen=True, pos=wohn, cut=7,
             text="Eine gewölbte Halle im Hügel der Hauptinsel. Die Glasfront schaut direkt auf den Weltenbaum "
                  "und den See."),
        dict(name="See mit Wasserfall ins Leere", typ="highlight", pos=(lx, wl + 1, lz),
             text="Ein kleiner See auf der Hauptinsel. Sein Abfluss stürzt über die Inselkante in die Tiefe."),
        dict(name="Farminsel", typ="farm", pos=farm,
             text="Weizenfelder mit Wasserrinnen und zwei eingezäunte Weiden für Tiere."),
        dict(name="Lagerinsel", typ="lager", innen=True, pos=lager, cut=8,
             text="Die ganze Insel ist innen hohl. In der 32 × 36 Blöcke großen Halle stehen Regalreihen aus "
                  "Fässern. Eine Treppe führt von oben hinein."),
        dict(name="Werkstatt unter dem Überhang", typ="werkstatt", innen=True, pos=werk, cut=7,
             text=f"In die Werkstattinsel gehauen, mit einer offenen Terrasse. Darunter geht es {PASTE_Y + ky - 63} "
                  "Blöcke tief bis zum Boden."),
        dict(name="Verzauberungsinsel", typ="werkstatt", pos=zauber,
             text="Die zweithöchste Insel, mit einem Ring aus Bücherregalen und einem Kirschbaum. Eine Brücke "
                  "führt zur Lagerinsel."),
        dict(name="Sprungpfad und Aussichtsinsel", typ="highlight", pos=(a_["x"], ay, a_["z"]),
             text="Vier Mini-Inseln bilden einen Sprungpfad hinauf zur höchsten Insel. Oben ist eine Plattform "
                  "mit Laternen."),
    ]
    info = dict(
        slug=SLUG, nr=4, title="Die schwebenden Inseln",
        tagline="Über 20 Inseln im Himmel. In der Mitte steht ein riesiger Kirschbaum.",
        story=[
            "Hoch über dem Boden schweben über 20 Inseln. Die Hauptinsel ist 145 × 170 Blöcke groß, die "
            "kleinsten sind nur ein paar Blöcke breit.",
            "Auf der Hauptinsel wächst ein riesiger Kirschbaum. Seine Wurzeln hängen unten aus dem Fels. Ein See "
            "läuft über die Kante und stürzt als Wasserfall in die Tiefe.",
            "Jede große Insel hat eine Aufgabe: Wohnen, Farmen, Lager, Werkstatt, Shop, Verzaubern. "
            "Hängebrücken verbinden sie, Ketten und Lianen hängen unter ihnen.",
        ],
        ground_y=63 - PASTE_Y, water_level=None, paste_y=PASTE_Y,
        paste_note="Dann schweben die Inseln hoch über dem Boden (Y 63). Den Blasen-Aufzug bis zum Boden verlängern.",
        water_color="#3d8ad8", sky_color="#b4d4ee",
        surround=dict(kind="grass", y=63 - PASTE_Y, color="#6f9e4a", full=True),
        camera=dict(target=(190, 118, 260), pos=(440, 220, 590)),
        clip=None,
        zones=zones,
        phasen=[
            ("Gerüst", "Die Mittelpunkte der Inseln mit Säulen aus Gerüst oder Wolle in der richtigen Höhe "
                       "markieren."),
            ("Hauptinsel", "Zuerst die flache Oberseite bauen, dann die kegelförmige Unterseite Schicht für "
                           "Schicht nach unten. So hat man immer eine Fläche zum Stehen."),
            ("Weltenbaum", "Stamm, Äste und Krone, dann die Wurzeln, die durch die Insel nach unten wachsen."),
            ("Weitere Inseln", "Shop-, Farm-, Lager-, Werkstatt- und Verzauberungsinsel bauen und mit Brücken "
                               "verbinden."),
            ("Aufzug", "Den Blasen-Aufzug vom Boden bis zur Shopinsel bauen: Seelensand unten, Wassersäule, "
                       "Glas außen herum."),
            ("Details", "Deko-Inseln, Ketten, Lianen, Wasserfälle und Gerüst wieder abbauen."),
        ],
        tipps=[
            "Die Schematic so einfügen, dass ihre Unterkante auf Y {paste_y} liegt. Die höchste Insel reicht dann "
            "bis Y {welt_max}. Den Aufzug unten bis zum Boden verlängern.",
            "Der Wasserfall fällt in Minecraft bis zum Boden. Unten ein Becken bauen, sonst fließt das Wasser "
            "breit auseinander.",
            "Unterseiten aus Stein, Andesit und Tuff in Schichten bauen. Hängende Wurzeln und Ketten verstärken "
            "den Schwebe-Effekt.",
        ],
    )
    return w, info
