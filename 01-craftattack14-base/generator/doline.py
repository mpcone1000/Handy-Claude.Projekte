"""Landschaft 3: Die Riesen-Doline.

Ein Dschungel-Plateau mit einem gigantischen Einsturzloch: oben 120 Blöcke breit, darunter glockenförmig
erweitert, 78 Blöcke tief, unten ein türkiser See mit einer Insel und einem Riesenbaum.
"""
import numpy as np

from mclib import (B, OCCLUDES, World, bridge, bush, carve_room, fbm2, fbm3, leaf_blob, paint_path, polyline_dist,
                   retexture, scatter_points, smooth_polyline, smoothstep, tree_big, tree_jungle, tree_round)

W, H, D = 340, 140, 430
PLAT = 104          # Plateau-Oberfläche
WATER = 26          # Seespiegel
BOT = 6
SLUG = "riesen-doline"
CX, CZ = 170, 232


def wall_point(w, cx, cz, y, ang, rmax=140, rmin=40):
    """Von der Lochmitte nach außen bis zur Wand; gibt die letzte Position vor dem Fels zurück.
    Erst ab rmin suchen, damit Insel und Riesenbaum in der Mitte nicht stören."""
    c, s = np.cos(ang), np.sin(ang)
    prev = None
    for r in np.arange(rmin, rmax, 0.5):
        x, z = int(round(cx + c * r)), int(round(cz + s * r))
        if not w.inside(x, y, z):
            return None
        if OCCLUDES[w.b[y, z, x]]:
            return (prev[0], prev[1], r) if prev else None
        prev = (x, z)
    return None


def fall_column(w, x0, x1, z0, z1, y_top):
    """Frei fallender Wasserfall: Wasser senkrecht nach unten, bis etwas im Weg ist."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(int(y_top), 0, -1):
                b = w.b[y, z, x]
                if b == 0:
                    w.b[y, z, x] = B("water")
                elif b == B("water") and y < y_top - 2:
                    break
                elif OCCLUDES[b] and y < y_top - 2:
                    break


def generate():
    w = World(W, H, D, seed=33)
    X, Z = w.X, w.Z
    rng = w.rng

    # ---------------- Plateau ----------------
    wx = X + fbm2(X, Z, 60, 3, 1) * 16
    wz = Z + fbm2(X, Z, 60, 3, 2) * 16
    e = np.hypot((wx - CX) / 160, (wz - 215) / 200)
    foot = e < 1
    h = PLAT + fbm2(X, Z, 50, 4, 3) * 3 + np.maximum(0, fbm2(X, Z, 80, 3, 4)) * 9
    h = PLAT + (h - PLAT) * (1 - smoothstep(0.8, 1.0, e))
    rivers = [smooth_polyline([(170, 2), (160, 50), (176, 100), (170, 150)], 10),
              smooth_polyline([(330, 230), (290, 222), (250, 238)], 10),
              smooth_polyline([(18, 300), (60, 290), (95, 272)], 10)]
    rd = np.min([polyline_dist(X, Z, p) for p in rivers], axis=0)
    h = np.where(rd < 7, np.minimum(h, PLAT - 3 + smoothstep(3, 7, rd) * (h - PLAT + 3)), h)
    surf = np.full(h.shape, B("grass"), np.uint8)
    r = rng.random(h.shape)
    surf[(fbm2(X, Z, 12, 2, 5) > 0.35) & (r < 0.12)] = B("podzol")
    surf[rd < 4] = B("gravel")
    rock = w.strata(["stone", "calcite", "stone", "andesite", "stone", "diorite", "stone", "tuff", "andesite"], band=3, seed=8,
                    warp=9)
    w.fill_heightmap(np.where(foot, h, -1), surf, "dirt", 3, rock_fn=rock, bottom=np.full(h.shape, float(BOT)))
    w.flood(PLAT - 1, region=(rd < 3.6) & foot)

    # ---------------- Das Loch (Glockenform) ----------------
    def carve_hole(cx, cz, r_top, bulge, depth_bulge, seed, water_r=None):
        R = r_top + bulge + 12
        bb = w._bbox(cx - R, BOT, cz - R, cx + R, H - 1, cz + R)
        x0, y0, z0, x1, y1, z1 = bb
        Y, Zg, Xg = np.meshgrid(np.arange(y0, y1, dtype=float), np.arange(z0, z1, dtype=float),
                                np.arange(x0, x1, dtype=float), indexing="ij")
        th = np.arctan2(Zg - cz, Xg - cx)
        dist = np.hypot(Xg - cx, Zg - cz)
        t = PLAT + 2 - Y
        rr = r_top + bulge * smoothstep(0, depth_bulge, t) - bulge * 0.25 * smoothstep(55, 78, t)
        n = fbm3(np.cos(th) * 3 + seed, Y / 14.0, np.sin(th) * 3 - seed, 1.0, 3, seed)
        rr = rr * (1 + 0.1 * n) + fbm3(Xg, Y, Zg, 9, 2, seed + 1) * 2.5
        below = Y < WATER
        bowl = np.sqrt(np.clip(1 - ((WATER - Y) / (WATER - BOT - 1)) ** 2, 0, 1))
        rr = np.where(below, rr * bowl, rr)
        hole = dist < rr
        sub = w.b[y0:y1, z0:z1, x0:x1]
        sub[hole] = 0
        sub[hole & (Y <= WATER)] = B("water")
        return rr

    carve_hole(CX, CZ, 58, 26, 26, 1)
    carve_hole(98, 78, 21, 9, 14, 5)
    # Unterirdischer Fluss zwischen den beiden Löchern
    for t in np.linspace(0, 1, 160):
        px = 98 + (CX - 98) * t + np.sin(t * 6) * 6
        pz = 78 + (CZ - 78) * t
        w.ellipsoid(px, WATER + 2, pz, 5, 6, 5, 0, noise=0.2, seed=int(t * 50))
        w.ellipsoid(px, WATER - 2, pz, 5, 3, 5, B("water"), replace=[0, B("stone"), B("calcite"), B("andesite"),
                                                                       B("diorite"), B("tuff"), B("dirt")])
    # Oberlichter in der überhängenden Decke
    for k, a in enumerate((0.6, 2.2, 3.7, 5.1)):
        rx = CX + np.cos(a) * 73
        rz = CZ + np.sin(a) * 73
        w.cylinder(rx, rz, PLAT - 26, PLAT + 12, 3.5 + k % 2, 0)

    # Seeboden, Insel, Wandfarben
    lake = (w.b == B("water"))
    for y in range(BOT, WATER):
        layer = w.b[y]
        below_water = (layer != 0) & (layer != B("water")) & (w.b[y + 1] == B("water"))
        layer[below_water & (rng.random(layer.shape) < 0.5)] = B("sand")
        layer[below_water & (rng.random(layer.shape) < 0.25)] = B("clay")
    isl = np.hypot(X - (CX + 8), Z - (CZ + 12))
    for y in range(BOT, WATER + 4):
        rad = 15 - max(0, y - WATER) * 2.5 + max(0, WATER - y) * 0.9
        m = isl < rad * (1 + 0.1 * fbm2(X, Z, 6, 2, 9))
        w.b[y][m] = np.where(y >= WATER + 1, B("grass") if y == WATER + 3 else B("dirt"), B("stone"))
    top = w.column_top()

    retexture(w, 0, BOT, 0, W, PLAT, D, ["stone"], [("andesite", 0.14), ("cobblestone", 0.04), ("diorite", 0.06)])
    retexture(w, 0, BOT, 0, W, PLAT, D, ["calcite"], [("stone", 0.3), ("diorite", 0.25)])
    # Moos und Tropfsteine an den unteren Wänden
    retexture(w, 0, WATER, 0, W, WATER + 30, D, ["stone", "andesite", "diorite", "calcite"],
              [("moss", 0.18), ("mossy_cobblestone", 0.08), ("dripstone_block", 0.06)])

    # ---------------- Grün an der Wand: Lianen, Wurzeln, Tropfsteine ----------------
    for a in np.linspace(0, 2 * np.pi, 120, endpoint=False):
        a += rng.uniform(-0.03, 0.03)
        p = wall_point(w, CX, CZ, PLAT - 1, a)
        if not p:
            continue
        L = rng.uniform(10, 55)
        leaf = "jungle_leaves" if rng.random() < 0.5 else ("azalea_leaves" if rng.random() < 0.7 else "cave_vines")
        x, z = p[0], p[1]
        for y in range(PLAT, int(PLAT - L), -1):
            if w.get(x, y, z) != 0:
                continue
            w.set(x, y, z, B(leaf))
    # Decke der Glocke: hängende Wurzeln und Tropfsteinzapfen
    for _ in range(260):
        a = rng.uniform(0, 2 * np.pi)
        rr = rng.uniform(60, 82)
        x, z = int(CX + np.cos(a) * rr), int(CZ + np.sin(a) * rr)
        for y in range(PLAT - 4, WATER, -1):
            if w.get(x, y, z) == 0 and OCCLUDES[w.get(x, y + 1, z)]:
                if rng.random() < 0.55:
                    for k in range(int(rng.integers(2, 7))):
                        w.set(x, y - k, z, B("hanging_roots"), only_air=True)
                else:
                    L = int(rng.integers(3, 10))
                    for k in range(L):
                        rad = (1 - k / L) * 1.6
                        w.cylinder(x, z, y - k, y - k, rad, B("dripstone_block"), only_air=True)
                break

    # ---------------- Wasserfälle über den Rand ----------------
    fall_column(w, 167, 172, 168, 172, PLAT)
    fall_column(w, 246, 249, 236, 240, PLAT)
    fall_column(w, 94, 97, 270, 274, PLAT)
    for (x0, x1, z0, z1) in ((166, 173, 150, 175), (242, 252, 233, 243), (92, 99, 266, 277)):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if w.b[PLAT - 1, z, x] == 0 and OCCLUDES[w.b[PLAT - 2, z, x]]:
                    w.b[PLAT - 1, z, x] = B("water")

    # ---------------- Riesenbaum auf der Insel ----------------
    tree_big(w, CX + 8, WATER + 4, CZ + 12, h=50, trunk_r=3.2, log="jungle_log", leaf="jungle_leaves", crown=16,
             branches=8, leaf2="azalea_leaves")
    for k in range(10):
        a = rng.uniform(0, 2 * np.pi)
        bush(w, CX + 8 + np.cos(a) * 10, WATER + 4, CZ + 12 + np.sin(a) * 10, leaf="flowering_azalea_leaves")

    # ---------------- Spiralweg an der Wand ----------------
    a0, turns = -0.4, 1.35
    nst = 900
    y_hi, y_lo = PLAT, WATER + 2
    room_spots = {}
    for i in range(nst):
        t = i / nst
        a = a0 + t * turns * 2 * np.pi
        y = int(round(y_hi - (y_hi - y_lo) * t))
        p = wall_point(w, CX, CZ, y + 2, a)
        if not p:
            continue
        rwall = p[2]
        c, s = np.cos(a), np.sin(a)
        for rr in np.arange(rwall - 3.5, rwall + 2.5, 0.5):
            x, z = CX + c * rr, CZ + s * rr
            w.set(x, y, z, B("spruce_planks"))
            for k in range(1, 5):
                if w.get(x, y + k, z) not in (B("water"),):
                    w.set(x, y + k, z, 0)
        x, z = CX + c * (rwall - 4), CZ + s * (rwall - 4)
        w.set(x, y + 1, z, B("spruce_fence"), only_air=True)
        if i % 30 == 0:
            w.set(x, y + 2, z, B("lantern"), only_air=True)
        if i % 70 == 0:
            for k in range(1, 30):
                if w.get(x, y - k, z) == 0:
                    w.set(x, y - k, z, B("chain"))
                else:
                    break
        room_spots[i] = (a, y, rwall)

    def room_at(i, depth, width, height, floor="spruce_planks"):
        a, y, rwall = room_spots[min(room_spots, key=lambda k: abs(k - i))]
        c, s = np.cos(a), np.sin(a)
        mid = rwall + 2 + depth / 2
        cx, cz = CX + c * mid, CZ + s * mid
        # Raum entlang der Wandrichtung ausrichten (achsparallele Box um den Mittelpunkt)
        hw = width / 2
        carve_room(w, cx - hw, y + 1, cz - hw, cx + hw, y + height, cz + hw, floor=floor, light="lantern")
        for rr in np.arange(rwall - 1, rwall + 3, 0.5):
            for o in (-1, 0, 1):
                xx, zz = CX + c * rr - s * o, CZ + s * rr + c * o
                for k in range(1, 5):
                    w.set(xx, y + k, zz, 0)
        return (int(cx), y + 1, int(cz))

    wohn = room_at(120, 18, 20, 9)
    werk = room_at(330, 14, 16, 7, floor="stone_bricks")
    lager = room_at(520, 24, 26, 10)
    farm = room_at(700, 26, 30, 14, floor="stone_bricks")

    # Glasbalkone vor dem Wohnbereich
    a, y, rwall = room_spots[120]
    for rr in np.arange(rwall - 9, rwall - 3, 0.5):
        for o in np.arange(-5, 5.5, 0.5):
            xx, zz = CX + np.cos(a) * rr - np.sin(a) * o, CZ + np.sin(a) * rr + np.cos(a) * o
            w.set(xx, y, zz, B("spruce_planks"), only_air=True)

    # Unterwasser-Raum mit Glaswand zum See
    a_uw = a0 + turns * 2 * np.pi
    uw_y = WATER - 12
    p = wall_point(w, CX, CZ, uw_y + 4, a_uw, rmin=30)
    uw = None
    if p:
        c, s = np.cos(a_uw), np.sin(a_uw)
        mid = p[2] + 9
        cx, cz = CX + c * mid, CZ + s * mid
        carve_room(w, cx - 8, uw_y, cz - 8, cx + 8, uw_y + 8, cz + 8, floor="dark_prismarine", light="sea_lantern",
                   round_=False)
        for o in np.arange(-6, 6.5, 0.5):
            for k in range(0, 8):
                for rr in np.arange(p[2] - 2, p[2] + 6, 0.5):
                    xx, zz = CX + c * rr - s * o, CZ + s * rr + c * o
                    b = w.get(xx, uw_y + k, zz)
                    if b == B("water"):
                        continue
                    near_w = any(w.get(xx + dx, uw_y + k, zz + dz) == B("water")
                                 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    w.set(xx, uw_y + k, zz, B("glass") if near_w else 0)
        # Treppenschacht vom Spiralende nach unten
        _, ye, rwe = room_spots[max(room_spots)]
        for k in range(0, (WATER + 2) - uw_y + 1):
            xx, zz = CX + c * (p[2] + 3), CZ + s * (p[2] + 3)
            w.box(xx - 1, uw_y + k, zz - 1, xx + 1, uw_y + k + 3, zz + 1, 0)
            w.set(xx, uw_y + k - 1, zz, B("spruce_planks"))
        uw = (int(cx), uw_y, int(cz))

    # ---------------- Aussichtsplattform mit Glasboden + Shop am Rand ----------------
    pa = np.pi * 0.5
    p = wall_point(w, CX, CZ, PLAT + 1, pa)
    rim_r = p[2] if p else 60
    px0 = CX - 6
    pz_rim = int(CZ + rim_r)
    w.box(px0, PLAT, pz_rim - 20, px0 + 12, PLAT, pz_rim + 2, B("glass"))
    w.box(px0, PLAT, pz_rim - 20, px0, PLAT, pz_rim + 2, B("spruce_planks"))
    w.box(px0 + 12, PLAT, pz_rim - 20, px0 + 12, PLAT, pz_rim + 2, B("spruce_planks"))
    w.box(px0, PLAT, pz_rim - 20, px0 + 12, PLAT, pz_rim - 20, B("spruce_planks"))
    for x in range(px0, px0 + 13):
        w.set(x, PLAT + 1, pz_rim - 20, B("spruce_fence"))
    for z in range(pz_rim - 20, pz_rim + 3):
        w.set(px0, PLAT + 1, z, B("spruce_fence"))
        w.set(px0 + 12, PLAT + 1, z, B("spruce_fence"))
    shop_z = pz_rim + 8
    w.box(CX - 16, PLAT + 1, shop_z, CX + 16, PLAT + 1, shop_z + 14, B("stone_bricks"))
    w.box(CX - 16, PLAT + 2, shop_z, CX + 16, PLAT + 16, shop_z + 14, 0)
    for x in range(CX - 14, CX + 15, 6):
        w.box(x, PLAT + 2, shop_z + 3, x + 2, PLAT + 2, shop_z + 3, B("barrel"))
        w.set(x + 1, PLAT + 3, shop_z + 3, B("lantern"))

    # ---------------- Dschungel ----------------
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    ground = np.isin(gb, [B("grass"), B("podzol")]) & (top > PLAT - 6) & foot & (np.hypot(X - CX, Z - CZ) > 74)
    for zz, xx in scatter_points(w, ground, 150, 12):
        tree_jungle(w, xx, top[zz, xx] + 1, zz)
    for zz, xx in scatter_points(w, ground, 260, 7):
        tree_round(w, xx, top[zz, xx] + 1, zz, log="jungle_log", leaf="jungle_leaves", r=rng.uniform(2.4, 3.4))
    for zz, xx in scatter_points(w, ground, 900, 3):
        bush(w, xx, top[zz, xx] + 1, zz, leaf="azalea_leaves" if rng.random() < 0.5 else "jungle_leaves")
    paint_path(w, smooth_polyline([(CX, shop_z + 14), (CX + 10, shop_z + 40), (CX + 30, 410)], 8), width=1.6,
               lanterns=12, allowed=("grass", "podzol", "dirt"))

    spiral_top = room_spots[0]
    sx = int(CX + np.cos(spiral_top[0]) * spiral_top[2])
    sz = int(CZ + np.sin(spiral_top[0]) * spiral_top[2])
    zones = [
        dict(name="Einstieg zum Spiralweg", typ="eingang", pos=(sx, PLAT + 1, sz),
             text="Am Rand des Lochs beginnt ein 6 Blöcke breiter Holzweg. Er schraubt sich in 1,35 Runden an "
                  "der Wand entlang 78 Blöcke tief bis zum See. Laternen hängen an Ketten über dem Abgrund."),
        dict(name="Glasboden-Plattform", typ="highlight", pos=(px0 + 6, PLAT + 1, pz_rim - 10),
             text="Eine Plattform mit Glasboden ragt 20 Blöcke weit über den Abgrund. Darunter geht es fast 80 "
                  "Blöcke in die Tiefe."),
        dict(name="Shop am Rand", typ="shop", pos=(CX, PLAT + 2, shop_z + 7),
             text="Ein Marktplatz aus Steinziegeln direkt hinter der Plattform. Besucher sehen das Loch, kommen "
                  "aber nicht hinein."),
        dict(name="Wohnbereich", typ="wohnen", innen=True, pos=wohn, cut=8,
             text="Ein großer Raum in der Wand, kurz unter dem Rand, mit einem Holzbalkon über dem Abgrund."),
        dict(name="Werkstatt", typ="werkstatt", innen=True, pos=werk,
             text="Eine Kammer auf halber Höhe des Spiralwegs, mit Steinboden für Amboss und Schmelzöfen."),
        dict(name="Lagerhalle", typ="lager", innen=True, pos=lager, cut=8,
             text="Die größte Kammer (26 × 26, 10 hoch) liegt tief im Fels. Hier ist viel Platz für ein "
                  "Sortiersystem."),
        dict(name="Farm-Stollen", typ="farm", innen=True, pos=farm, cut=10,
             text="Eine 14 Blöcke hohe Halle kurz über dem See. Hier passen Eisen- und Mobfarmen hin, die man "
                  "von oben nicht sieht."),
        dict(name="Unterwasser-Raum", typ="wohnen", innen=True, pos=uw or (CX, uw_y, CZ), cut=9,
             text="Er liegt 12 Blöcke unter dem Seespiegel. Durch die Glaswand sieht man in den türkisen See. "
                  "Eine Treppe führt vom Ende des Spiralwegs hinunter."),
        dict(name="Insel mit Riesenbaum", typ="highlight", pos=(CX + 8, WATER + 4, CZ + 12),
             text="Ein 50 Blöcke hoher Urwaldriese wächst aus der Insel in der Seemitte dem Licht entgegen."),
        dict(name="Kleine Doline und Höhlenfluss", typ="highlight", pos=(98, WATER + 2, 78),
             text="Ein zweites, kleineres Loch im Norden. Ein unterirdischer Fluss verbindet es mit dem großen "
                  "See. Mit dem Boot kann man hindurchfahren."),
        dict(name="Wasserfälle", typ="highlight", pos=(170, PLAT - 20, 170),
             text="Drei Bäche stürzen über den Rand frei bis in den See, fast 80 Blöcke tief."),
    ]
    info = dict(
        slug=SLUG, nr=3, title="Die Riesen-Doline",
        tagline="Ein riesiges Loch im Dschungel. Unten liegt eine eigene Welt.",
        story=[
            "Von weitem sieht man nur Dschungel. Dann öffnet sich der Boden: Ein 120 Blöcke breites Loch fällt "
            "78 Blöcke tief ab. Darunter weitet es sich wie eine Glocke auf über 160 Blöcke.",
            "Unten liegt ein türkiser See mit einer Insel, auf der ein Urwaldriese dem Licht entgegenwächst. "
            "Lianen und Wurzeln hängen von der Decke, drei Wasserfälle stürzen hinab.",
            "Die Base hängt an der Wand: Ein Spiralweg führt hinunter. Von ihm gehen Wohnbereich, Werkstatt, "
            "Lager und Farmen ab, und ganz unten liegt ein Raum mit Glaswand unter Wasser.",
        ],
        ground_y=int(PLAT), water_level=WATER, paste_y=63 - PLAT,
        paste_note="Dann liegt das Plateau auf Y 63 und der See unten auf Y {water_world}.",
        water_color="#27b3b0", sky_color="#a8cfe3",
        surround=dict(kind="grass", color="#5f9a3c"),
        camera=dict(target=(CX, 40, CZ + 10), pos=(CX + 110, 270, CZ + 230)),
        clip=None,
        zones=zones,
        phasen=[
            ("Umriss markieren", "Den oberen Rand des Lochs (ca. 120 Blöcke Durchmesser) auf dem Boden "
                                 "abstecken, ebenso die kleine Doline im Norden."),
            ("Ausheben", "Das Loch Schicht für Schicht ausgraben und dabei die Glockenform beachten: unten "
                         "breiter als oben. Das sind Millionen Blöcke, also mit Spitzhacke Effizienz V, Eile "
                         "und Beacon arbeiten."),
            ("See und Insel", "Den Boden als Schüssel formen, mit Wasser füllen und die Insel aufschütten."),
            ("Spiralweg", "Den Weg von oben nach unten an der Wand entlang bauen. Er dient gleichzeitig als "
                          "Gerüst für alles Weitere."),
            ("Räume", "Wohnbereich, Werkstatt, Lager, Farm-Stollen und Unterwasser-Raum vom Weg aus in den Fels "
                      "graben."),
            ("Leben", "Riesenbaum, Lianen, Wurzeln, Tropfsteine, Wasserfälle und die Glasplattform."),
        ],
        tipps=[
            "Beim Ausheben fällt extrem viel Stein an. Damit kannst du die Farmen und den Rand des Plateaus "
            "bauen.",
            "Damit der See türkis aussieht, die Doline in ein warmes Biom bauen (Dschungel oder warmer "
            "Ozean). Die Wasserfarbe hängt vom Biom ab.",
            "Glasboden über dem Abgrund: Mit getöntem Glas darunter wirkt es noch tiefer.",
        ],
    )
    return w, info
