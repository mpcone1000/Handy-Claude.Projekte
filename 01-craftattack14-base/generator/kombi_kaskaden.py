"""Kombination 9: Das Kaskaden-Tal (Tal + türkise Seen + Doline).

Eine bewaldete Schlucht mit fünf türkisen Seen in Stufen (wie die Plitvicer Seen). Über Sinterdämme
stürzen Dutzende Wasserfälle von See zu See, ein großer Wasserfall fällt von der Hochebene herab, und
ganz unten verschwindet alles in einem runden Doline-Loch.
"""
import numpy as np

from doline import fall_column
from mclib import (B, OCCLUDES, World, bridge, bush, carve_room, fbm2, lake_bed, leaf_blob, paint_path,
                   polyline_dist, retexture, scatter_points, smooth_polyline, smoothstep, tree_cherry, tree_round,
                   tree_spruce)

W, H, D = 320, 150, 580
GROUND = 112
LV = [100, 90, 79, 68, 56]                 # Seespiegel von Nord nach Süd
ZB = [118, 212, 306, 398]                  # Sinterdämme zwischen den Seen
ZC = [72, 165, 259, 352, 444]              # Seemitten
SLUG = "kaskaden-tal"


def generate():
    w = World(W, H, D, seed=99)
    X, Z = w.X, w.Z
    rng = w.rng

    cxz = 160 + 22 * np.sin(Z / 85.0) + fbm2(X * 0 + 1, Z, 60, 2, 1) * 6
    hw = 64 + 14 * np.sin(Z / 57.0 + 1) + fbm2(X * 0 + 2, Z, 50, 2, 2) * 6
    across = np.abs(X - cxz) / hw

    # Hochebene mit organischem Umriss
    e = np.hypot((X - 160 + fbm2(X, Z, 60, 3, 3) * 16) / 158, (Z - 290 + fbm2(X, Z, 60, 3, 4) * 16) / 285)
    foot = e < 1
    plateau = GROUND + fbm2(X, Z, 50, 4, 5) * 3 + np.maximum(0, fbm2(X, Z, 80, 3, 6)) * 6
    plateau = GROUND + (plateau - GROUND) * (1 - smoothstep(0.8, 1.0, e))

    # Stufenboden der Schlucht: Dammkante leicht gewellt
    wave = fbm2(X, Z * 0 + 7, 25, 3, 8) * 5
    seg = np.zeros(X.shape, int)
    for k, zb in enumerate(ZB):
        seg = np.where(Z > zb + wave, k + 1, seg)
    lv = np.array(LV)[seg]
    floor = lv + 1 + np.maximum(0, fbm2(X, Z, 30, 3, 9)) * 3 + 6 * smoothstep(0.6, 0.9, across)
    cap = smoothstep(32, 12, Z) + smoothstep(540, 562, Z)
    t = smoothstep(0.86, 1.0, across + fbm2(X, Z, 18, 3, 10) * 0.05)
    t = np.clip(np.maximum(t, cap), 0, 1)
    tq = np.floor(t * 6) / 6
    t2 = 0.6 * t + 0.4 * tq
    h = floor + (plateau - floor) * t2

    # Seen
    lakes = []
    for k in range(5):
        z0 = ZB[k - 1] if k > 0 else 30
        z1 = ZB[k] if k < 4 else 492
        half = (z1 - z0) / 2 - 7
        ld = np.hypot(across / 0.8, (Z - (z0 + z1) / 2) / half) + fbm2(X, Z, 14, 2, 20 + k) * 0.08
        m = (ld < 1) & (seg == k)
        bottom = LV[k] - 2 - 8 * smoothstep(1.0, 0.35, ld) + fbm2(X, Z, 9, 2, 30 + k) * 1.2
        h = np.where(m, np.minimum(h, bottom), h)
        shore = (ld >= 1) & (ld < 1.18) & (seg == k)
        h = np.where(shore, np.minimum(h, LV[k] - 1 + smoothstep(1.0, 1.18, ld) * (h - LV[k] + 1)), h)
        lakes.append((ld, m))
    # Verzauberungsinsel im mittleren See
    iz = np.hypot(X - (160 + 22 * np.sin(ZC[2] / 85.0) + 8), Z - ZC[2])
    h = np.where(iz < 9, np.maximum(h, LV[2] + 1 + 3 * smoothstep(9, 3, iz)), h)

    # Überlauf-Rinnen an den Dämmen
    notches = []
    for k, zb in enumerate(ZB):
        cx = 160 + 22 * np.sin(zb / 85.0)
        hwz = 64 + 14 * np.sin(zb / 57.0 + 1)
        for f in (-0.66, -0.3, 0.05, 0.38, 0.7):
            xn = int(cx + hwz * f + rng.uniform(-5, 5))
            wn = int(rng.integers(2, 5))
            m = (np.abs(X - xn) <= wn) & (Z > zb - 26) & (Z < zb + 10) & (seg == k)
            h = np.where(m, np.minimum(h, LV[k] - 1), h)
            notches.append((k, xn, wn, m))
    # Abfluss des letzten Sees in die Doline
    m5 = (np.abs(X - (160 + 22 * np.sin(500 / 85.0))) <= 4) & (Z > 470) & (Z < 512)
    h = np.where(m5, np.minimum(h, LV[4] - 1), h)

    # Fluss auf der Hochebene (für den großen Wasserfall)
    riv = smooth_polyline([(318, 300), (290, 330), (262, 350), (232, 356)], 10)
    rdist = polyline_dist(X, Z, riv)
    h = np.where((rdist < 5) & (across > 1.0), np.minimum(h, GROUND - 3), h)
    rivn = smooth_polyline([(160, 0), (152, 20), (150, 34)], 8)
    rdn = polyline_dist(X, Z, rivn)
    h = np.where(rdn < 4, np.minimum(h, GROUND - 3), h)

    # ---------------- Oberflächen ----------------
    gz, gx = np.gradient(h)
    slope = np.hypot(gx, gz)
    r = rng.random(h.shape)
    surf = np.full(h.shape, B("grass"), np.uint8)
    sub = np.full(h.shape, B("dirt"), np.uint8)
    surf[(slope > 0.9) & (slope <= 1.7) & (r < 0.6)] = B("moss")
    steep = slope > 1.7
    surf[steep] = 255
    sub[steep] = 255
    any_lake = np.zeros(h.shape, bool)
    for k, (ld, m) in enumerate(lakes):
        any_lake |= (ld < 1.2) & (seg == k)
    bed = any_lake & (h < np.array(LV)[seg])
    lake_bed(surf, sub, bed, r)
    # Sinterdämme: Moos, Calcit, Tropfstein
    dam = np.zeros(h.shape, bool)
    for zb in ZB:
        dam |= (np.abs(Z - zb - wave) < 9) & (across < 0.9)
    damsurf = dam & ~bed
    surf[damsurf & (r < 0.45)] = B("moss")
    surf[damsurf & (r >= 0.45) & (r < 0.75)] = B("calcite")
    surf[damsurf & (r >= 0.75)] = B("dripstone_block")
    sub[damsurf] = B("calcite")
    surf[(rdist < 5) | (rdn < 4)] = B("gravel")
    rock = w.strata(["stone", "andesite", "stone", "calcite", "stone", "tuff", "diorite", "stone"], band=3, seed=11,
                    warp=6)
    w.fill_heightmap(np.where(foot, h, -1), surf, sub, 3, rock_fn=rock, bottom=np.full(h.shape, 12.0))
    retexture(w, 0, 20, 0, W, H, D, ["stone"], [("andesite", 0.14), ("cobblestone", 0.04), ("diorite", 0.05)])
    retexture(w, 0, 40, 0, W, GROUND - 4, D, ["calcite"], [("dripstone_block", 0.2), ("moss", 0.15)])

    # Wasser je Stufe
    for k in range(5):
        reg = (seg == k) & foot & (across < 1.0)
        reg &= (lakes[k][0] < 1.2) | np.any([m for kk, _, _, m in notches if kk == k] + [np.zeros(h.shape, bool)],
                                          axis=0)
        if k == 4:
            reg |= m5 & foot
        w.flood(LV[k], region=reg)
    w.flood(GROUND - 2, region=((rdist < 5) & (across > 1.0) | (rdn < 4)) & foot)

    # ---------------- Kaskaden über die Dämme ----------------
    for k, xn, wn, m in notches:
        w.face_water(xn - wn, xn + wn, LV[k], LV[k + 1], ZB[k] + 40, -1, axis="z", depth=1)
    # Nordfall: Bach von der Hochebene in den ersten See
    w.face_water(146, 154, GROUND - 2, LV[0], 60, -1, axis="z", depth=2)
    # Großer Wasserfall von Osten in den vierten See
    cx4 = int(160 + 22 * np.sin(354 / 85.0))
    w.face_water(350, 360, GROUND - 2, LV[3], cx4, +1, axis="x", depth=2)

    # ---------------- Doline am Südende ----------------
    dcx, dcz = int(160 + 22 * np.sin(522 / 85.0)), 522
    for y in range(14, GROUND + 4):
        rad = 22 + (4 if y < 40 else 0) * smoothstep(40, 30, y) + fbm2(np.array(y / 5.0), np.array(3.0), 2, 2, 40) * 2
        w.cylinder(dcx, dcz, y, y, rad, 0)
    for y in range(14, 30):
        w.cylinder(dcx, dcz, y, y, 24, B("water"), replace=[0])
    w.cylinder(dcx, dcz, 13, 13, 25, B("calcite"))
    fall_column(w, int(160 + 22 * np.sin(500 / 85.0)) - 3, int(160 + 22 * np.sin(500 / 85.0)) + 3, 499, 501, LV[4])
    for a in np.linspace(0, 2 * np.pi, 50, endpoint=False):
        x, z = dcx + np.cos(a) * 21.5, dcz + np.sin(a) * 21.5
        L = rng.uniform(8, 30)
        for y in range(int(LV[4]), int(LV[4] - L), -1):
            if w.get(x, y, z) == 0:
                w.set(x, y, z, B("jungle_leaves") if rng.random() < 0.6 else B("azalea_leaves"))

    # ---------------- Wohnbereich hinter dem großen Wasserfall ----------------
    wy = LV[3] + 3
    for z in range(348, 363):
        for y in range(wy, wy + 9):
            fx = w.face_pos(z, y, cx4, +1, "x")
            if fx is None:
                continue
            w.b[y, z, fx] = B("glass")
            w.b[y, z, fx + 1:fx + 20] = 0
    fxw = w.face_pos(355, wy + 4, cx4, +1, "x") or 230
    carve_room(w, fxw + 2, wy, 343, fxw + 22, wy + 10, 368, floor="spruce_planks", light="lantern", round_=False)
    w.box(fxw + 2, wy + 5, 343, fxw + 22, wy + 5, 368, B("spruce_planks"))
    w.box(fxw + 18, wy + 5, 345, fxw + 21, wy + 5, 348, 0)
    w.box(fxw + 22, wy, 343, fxw + 22, wy + 3, 368, B("bookshelf"))
    # Zugang: Holzsteg am Wasser entlang unter den Fall
    w.box(fxw - 3, LV[3] + 1, 336, fxw, LV[3] + 1, 370, B("spruce_planks"))
    w.box(fxw - 1, wy, 336, fxw + 1, wy + 3, 344, 0)
    wohn = (fxw + 12, wy + 1, 355)

    # ---------------- Lager im Damm hinter einer Kaskade ----------------
    zb = ZB[1]
    cxb = int(160 + 22 * np.sin(zb / 85.0))
    carve_room(w, cxb - 22, LV[2] + 1, zb - 16, cxb + 22, LV[2] + 6, zb - 4, floor="spruce_planks", light="lantern",
               round_=False)
    for x in range(cxb - 20, cxb + 21, 3):
        w.box(x, LV[2] + 1, zb - 14, x, LV[2] + 3, zb - 8, B("barrel"))
    w.box(cxb - 1, LV[2] + 1, zb - 4, cxb + 1, LV[2] + 4, zb + 6, 0)
    lager = (cxb, LV[2] + 2, zb - 10)

    # ---------------- Werkstatt in der Westwand am ersten See ----------------
    fxe = w.face_pos(80, LV[0] + 4, 150, -1, "x")
    werk = (150, LV[0] + 2, 80)
    if fxe:
        carve_room(w, fxe - 18, LV[0] + 2, 70, fxe - 3, LV[0] + 9, 92, floor="stone_bricks", light="lantern")
        w.box(fxe - 3, LV[0] + 2, 78, fxe + 1, LV[0] + 6, 84, 0)
        for i, blk in enumerate(["crafting_table", "smithing_table", "anvil", "blast_furnace", "barrel"]):
            w.set(fxe - 16, LV[0] + 2, 73 + i * 4, B(blk))
        werk = (fxe - 10, LV[0] + 3, 81)

    # ---------------- Farmhöhle in der Westwand am letzten See ----------------
    fxf = w.face_pos(440, LV[4] + 4, 150, -1, "x")
    farm2 = (100, LV[4] + 2, 440)
    if fxf:
        carve_room(w, fxf - 26, LV[4] + 2, 426, fxf - 3, LV[4] + 16, 454, floor="stone_bricks", light="lantern",
                   round_=False)
        w.box(fxf - 3, LV[4] + 2, 437, fxf + 1, LV[4] + 6, 443, 0)
        farm2 = (fxf - 14, LV[4] + 3, 440)

    # ---------------- Verzauberungsinsel ----------------
    ix = int(160 + 22 * np.sin(ZC[2] / 85.0) + 8)
    top = w.column_top()
    vy = int(top[ZC[2], ix]) + 1
    for a in np.linspace(0, 2 * np.pi, 20, endpoint=False):
        if np.cos(a) < -0.85:
            continue
        w.set(ix + 4 * np.cos(a), vy, ZC[2] + 4 * np.sin(a), B("bookshelf"))
        w.set(ix + 4 * np.cos(a), vy + 1, ZC[2] + 4 * np.sin(a), B("bookshelf"))
    w.set(ix, vy, ZC[2], B("lantern"))
    tree_cherry(w, ix + 5, int(top[ZC[2] + 4, ix + 5]) + 1, ZC[2] + 4, h=6)
    zauber = (ix, vy, ZC[2])

    # ---------------- Holzstege über die Seen ----------------
    def boardwalk(pts, y):
        sp = smooth_polyline(pts, 6)
        for (ax, az), (bx, bz) in zip(sp[:-1], sp[1:]):
            L = int(np.hypot(bx - ax, bz - az) * 2) + 1
            for t_ in np.linspace(0, 1, L):
                px, pz = ax + (bx - ax) * t_, az + (bz - az) * t_
                for o in (-0.5, 0.5):
                    for oo in (-0.5, 0.5):
                        w.set(px + o, y, pz + oo, B("spruce_planks"))
        for i, (px, pz) in enumerate(sp[::3]):
            for yy in range(y - 1, y - 14, -1):
                if OCCLUDES[w.get(px, yy, pz)]:
                    break
                w.set(px, yy, pz, B("spruce_log"))
    for k in (1, 2, 4):
        cz = ZC[k]
        cx = 160 + 22 * np.sin(cz / 85.0)
        hwz = 64 + 14 * np.sin(cz / 57.0 + 1)
        pts = [(cx - hwz * 0.75, cz - 30), (cx - hwz * 0.25, cz - 12), (cx + hwz * 0.15, cz - 22),
               (cx + hwz * 0.45, cz + 4), (cx + hwz * 0.05, cz + 18), (cx - hwz * 0.35, cz + 30),
               (cx - hwz * 0.6, cz + 42)]
        boardwalk(pts, LV[k] + 1)
    # Brücke über den großen Wasserfall-See zum Wohnbereich
    bridge(w, (cx4 - 50, LV[3] + 2, 352), (fxw - 3, LV[3] + 2, 352), sag=1)

    # ---------------- Eingang: Treppentunnel von der Hochebene ----------------
    ez = 470
    exw = w.face_pos(ez - 40, LV[4] + 4, 150, -1, "x") or 100
    start = (exw - 30, GROUND + 1, ez)
    end = (exw + 1, LV[4] + 2, ez - 44)
    n = 90
    for i in range(n + 1):
        t_ = i / n
        px = start[0] + (end[0] - start[0]) * t_
        py = int(round(start[1] + (end[1] - start[1]) * t_))
        pz = start[2] + (end[2] - start[2]) * t_
        w.box(px - 1.5, py, pz - 1.5, px + 1.5, py + 4, pz + 1.5, 0)
        w.box(px - 1.5, py - 1, pz - 1.5, px + 1.5, py - 1, pz + 1.5, B("stone_bricks"))
        if i % 9 == 0:
            w.set(px + 1.5, py + 3, pz, B("lantern"))
    w.box(start[0] - 3, GROUND, ez - 3, start[0] + 3, GROUND, ez + 3, B("mossy_stone_bricks"))
    # Shop auf der Hochebene
    sx, sz = start[0] - 26, ez + 18
    sy = int(w.column_top()[sz, sx]) + 1
    w.box(sx - 13, sy - 1, sz - 9, sx + 13, sy - 1, sz + 9, B("stone_bricks"))
    w.box(sx - 13, sy, sz - 9, sx + 13, sy + 12, sz + 9, 0)
    for x in range(sx - 11, sx + 12, 6):
        w.box(x, sy, sz - 6, x + 2, sy, sz - 6, B("barrel"))
        w.set(x + 1, sy + 1, sz - 6, B("lantern"))
    shop = (sx, sy, sz)

    # ---------------- Aussicht am Westrand ----------------
    az_ = 212
    ax_ = int(160 + 22 * np.sin(az_ / 85.0) - (64 + 14 * np.sin(az_ / 57.0 + 1)) - 8)
    ay = int(w.column_top()[az_, ax_]) + 1
    w.box(ax_ - 3, ay - 1, az_ - 5, ax_ + 12, ay - 1, az_ + 5, B("spruce_planks"))
    w.box(ax_ - 3, ay, az_ - 5, ax_ + 12, ay + 8, az_ + 5, 0)
    for x in range(ax_ - 3, ax_ + 13):
        w.set(x, ay, az_ - 5, B("spruce_fence"))
        w.set(x, ay, az_ + 5, B("spruce_fence"))
    for z in range(az_ - 5, az_ + 6):
        w.set(ax_ + 12, ay, z, B("spruce_fence"))
    for (x, z) in ((ax_ + 12, az_ - 5), (ax_ + 12, az_ + 5)):
        for y in range(LV[1], ay - 1):
            if not OCCLUDES[w.b[y, z, x]]:
                w.b[y, z, x] = B("spruce_log")
    aus = (ax_ + 6, ay, az_)

    # ---------------- Felder auf der Hochebene (Ost) ----------------
    top = w.column_top()
    fxc, fzc = 274, 160
    farm_y = int(np.median(top[fzc - 14:fzc + 14, fxc - 16:fxc + 16]))
    for z in range(fzc - 14, fzc + 15):
        for x in range(fxc - 16, fxc + 17):
            if not foot[z, x]:
                continue
            w.b[farm_y + 1:H, z, x] = 0
            w.b[min(top[z, x], farm_y):farm_y + 1, z, x] = B("dirt")
            if (x - fxc) % 7 == 0:
                w.b[farm_y, z, x] = B("water")
            else:
                w.b[farm_y, z, x] = B("farmland")
                w.b[farm_y + 1, z, x] = B("wheat")
    farm = (fxc, farm_y + 1, fzc)

    # ---------------- Wald ----------------
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    grass = (gb == B("grass")) | (gb == B("moss"))
    plat = grass & (across > 1.05) & foot & (np.hypot(X - fxc, Z - fzc) > 26) & (rdist > 7)
    for z, x in scatter_points(w, plat, 480, 7):
        k = rng.random()
        if k < 0.45:
            tree_spruce(w, x, top[z, x] + 1, z)
        elif k < 0.8:
            tree_round(w, x, top[z, x] + 1, z, r=rng.uniform(2.6, 3.6))
        else:
            tree_round(w, x, top[z, x] + 1, z, log="birch_log", leaf="birch_leaves")
    canyon = grass & (across < 1.0) & ~dam
    for z, x in scatter_points(w, canyon, 120, 8):
        if rng.random() < 0.5:
            tree_round(w, x, top[z, x] + 1, z, log="birch_log", leaf="birch_leaves")
        else:
            tree_round(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, grass & dam, 120, 4):
        bush(w, x, top[z, x] + 1, z, leaf="azalea_leaves", r=rng.uniform(1.0, 1.8))
    for z, x in scatter_points(w, grass & foot, 400, 5):
        bush(w, x, top[z, x] + 1, z, leaf="flowering_azalea_leaves" if rng.random() < 0.4 else "azalea_leaves")
    paint_path(w, smooth_polyline([(sx, sz), (start[0], ez)], 6), width=1.4, lanterns=8)

    zones = [
        dict(name="Treppentunnel (Eingang)", typ="eingang", pos=(start[0], GROUND + 1, ez),
             text=f"Auf der Hochebene führt ein Treppentunnel mit Laternen {GROUND - LV[4]} Blöcke hinab und "
                  "kommt am untersten See aus der Felswand."),
        dict(name="Shop auf der Hochebene", typ="shop", pos=shop,
             text="Ein Marktplatz im Wald direkt neben dem Tunneleingang."),
        dict(name="Fünf türkise Seen", typ="highlight", pos=(int(160 + 22 * np.sin(ZC[1] / 85.0)), LV[1] + 1, ZC[1]),
             text=f"Fünf Seen liegen in Stufen hintereinander, von Y {LV[0]} bis Y {LV[4]} (Schematic). "
                  "Heller Sand- und Calcitgrund macht sie türkis. Über die Dämme stürzen zwanzig Kaskaden."),
        dict(name="Wohnbereich hinter dem großen Wasserfall", typ="wohnen", innen=True, pos=wohn, cut=10,
             text=f"Ein Fluss von der Hochebene stürzt {GROUND - LV[3]} Blöcke tief in den vierten See. Direkt "
                  "dahinter liegt der Wohnbereich mit zwei Stockwerken. Durch die Glaswand sieht man den "
                  "Wasservorhang."),
        dict(name="Lager im Sinterdamm", typ="lager", innen=True, pos=lager, cut=6,
             text="Eine lange Halle im Damm zwischen zweitem und drittem See, hinter einer Kaskade. "
                  "Fassregale auf 44 Blöcken Länge."),
        dict(name="Werkstatt am ersten See", typ="werkstatt", innen=True, pos=werk, cut=7,
             text="Eine Höhle in der Westwand, direkt neben dem Nordfall."),
        dict(name="Verzauberungsinsel", typ="werkstatt", pos=zauber,
             text="Eine kleine Insel im mittleren See mit Bücherregal-Ring und Kirschbaum. Der Holzsteg führt "
                  "daran vorbei."),
        dict(name="Holzstege", typ="highlight", pos=(int(160 + 22 * np.sin(ZC[2] / 85.0)), LV[2] + 2, ZC[2] - 12),
             text="Zickzack-Stege aus Fichtenholz führen knapp über dem Wasser quer über drei Seen, wie in den "
                  "Plitvicer Seen."),
        dict(name="Felder auf der Hochebene", typ="farm", pos=farm,
             text="Eine Lichtung im Wald östlich der Schlucht mit Weizenfeldern und Wasserrinnen."),
        dict(name="Farmhöhle", typ="farm", innen=True, pos=farm2, cut=12,
             text="Eine 15 Blöcke hohe Halle in der Westwand am untersten See für Eisen- oder Mobfarmen."),
        dict(name="Doline am Südende", typ="highlight", pos=(dcx, 30, dcz),
             text=f"Der unterste See läuft in ein rundes Loch und stürzt {LV[4] - 29} Blöcke tief in einen "
                  "türkisen Teich. Lianen hängen am Rand."),
        dict(name="Aussicht am Westrand", typ="highlight", pos=aus,
             text="Eine Holzplattform ragt über die Schlucht. Von hier sieht man alle Kaskaden."),
    ]
    info = dict(
        slug=SLUG, nr=9, title="Das Kaskaden-Tal",
        tagline="Fünf türkise Seen in Stufen, zwanzig Wasserfälle und ganz unten ein Riesenloch.",
        story=[
            "Kombination aus Tal, türkisen Seen und Doline. In eine bewaldete Hochebene ist eine 550 Blöcke "
            "lange Schlucht geschnitten. Darin liegen fünf türkise Seen hintereinander, jeder etwa 10 Blöcke "
            "tiefer als der vorige.",
            "Über moosige Sinterdämme stürzen zwanzig Kaskaden von See zu See. Von der Hochebene fällt ein "
            "großer Wasserfall in den vierten See. Am Südende verschwindet alles in einem runden Doline-Loch.",
            "Holzstege führen im Zickzack über die Seen. Der Wohnbereich liegt hinter dem großen Wasserfall, "
            "das Lager im Damm hinter einer Kaskade.",
        ],
        ground_y=GROUND, water_level=LV[0], paste_y=63 - GROUND,
        paste_note="Dann liegt die Hochebene auf Y 63, und die Seen liegen darunter in der Schlucht.",
        water_color="#38cfe0", sky_color="#a9d0e8",
        surround=dict(kind="grass", color="#4f8a32"),
        camera=dict(target=(165, 62, 300), pos=(250, 230, 660)),
        clip=None,
        zones=zones,
        phasen=[
            ("Schlucht ausheben", "Die Schlucht Stufe für Stufe von Norden nach Süden ausheben. Jede Stufe "
                                  "etwa 10 Blöcke tiefer."),
            ("Seen und Dämme", "Seen flach ausheben, Grund mit weißem Sand und Calcit auslegen. Die Dämme "
                               "dazwischen aus Moos, Calcit und Tropfstein bauen."),
            ("Wasser", "Seen von oben nach unten füllen. In jeden Damm 4–5 Rinnen schneiden, aus denen Wasser "
                       "als Kaskade nach unten fällt."),
            ("Großer Wasserfall", "Den Fluss auf der Hochebene bauen und über die Kante fallen lassen. "
                                  "Dahinter den Wohnbereich mit Glaswand aushöhlen."),
            ("Doline", "Am Südende das runde Loch graben, Teich unten füllen."),
            ("Base und Natur", "Lager im Damm, Werkstatt, Farmen, Stege, Treppentunnel, Shop, Wald."),
        ],
        tipps=[
            "Wasser fließt in Minecraft nur 7 Blöcke weit. Für breite Kaskaden in jede Rinne mehrere "
            "Quellblöcke setzen.",
            "Türkis wird das Wasser in warmen Biomen am stärksten. Der helle Grund aus Sand und Calcit hilft "
            "überall.",
            "Die Seen sind am Rand nur 2–4 Blöcke tief. Flaches Wasser über hellem Grund leuchtet am schönsten.",
        ],
    )
    return w, info
