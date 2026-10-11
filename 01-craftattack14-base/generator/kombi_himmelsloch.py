"""Kombination 8: Das Himmelsloch (Riesen-Doline + schwebende Inseln + türkiser See).

Ein riesiges Einsturzloch im Dschungel. In der Glocke darunter schweben vier Inseln über einem flachen,
türkisen See. Ein Spiralweg an der Wand führt hinab, Hängebrücken verbinden Wand und Inseln.
"""
import numpy as np

from doline import fall_column, wall_point
from mclib import (B, OCCLUDES, World, bridge, bush, carve_room, fbm2, fbm3, float_island, paint_path, polyline_dist,
                   retexture, scatter_points, smooth_polyline, smoothstep, tree_big, tree_cherry, tree_jungle,
                   tree_palm, tree_round, vine_curtain)

W, H, D = 350, 150, 440
PLAT = 110
WATER = 30
BOT = 16
SLUG = "himmelsloch"
CX, CZ = 175, 228
A0, TURNS = -0.4, 1.35


def spiral_y(a):
    """Höhe des Spiralwegs beim Winkel a (erste Runde, in der er diesen Winkel erreicht)."""
    t = ((a - A0) % (2 * np.pi)) / (TURNS * 2 * np.pi)
    return PLAT - (PLAT - (WATER + 2)) * t


def generate():
    w = World(W, H, D, seed=88)
    X, Z = w.X, w.Z
    rng = w.rng

    # ---------------- Plateau ----------------
    wx = X + fbm2(X, Z, 60, 3, 1) * 16
    wz = Z + fbm2(X, Z, 60, 3, 2) * 16
    e = np.hypot((wx - CX) / 165, (wz - 215) / 205)
    foot = e < 1
    h = PLAT + fbm2(X, Z, 50, 4, 3) * 3 + np.maximum(0, fbm2(X, Z, 80, 3, 4)) * 8
    h = PLAT + (h - PLAT) * (1 - smoothstep(0.8, 1.0, e))
    rivers = [smooth_polyline([(175, 4), (165, 60), (180, 120), (176, 150)], 10),
              smooth_polyline([(340, 240), (300, 232), (262, 236)], 10)]
    rd = np.min([polyline_dist(X, Z, p) for p in rivers], axis=0)
    h = np.where(rd < 7, np.minimum(h, PLAT - 3 + smoothstep(3, 7, rd) * (h - PLAT + 3)), h)
    surf = np.full(h.shape, B("grass"), np.uint8)
    r = rng.random(h.shape)
    surf[(fbm2(X, Z, 12, 2, 5) > 0.2) & (r < 0.6)] = B("podzol")
    surf[rd < 4] = B("gravel")
    rock = w.strata(["stone", "calcite", "stone", "andesite", "stone", "diorite", "stone", "tuff", "andesite"],
                    band=3, seed=8, warp=9)
    w.fill_heightmap(np.where(foot, h, -1), surf, "dirt", 3, rock_fn=rock, bottom=np.full(h.shape, float(BOT - 4)))
    retexture(w, 0, 0, 0, W, PLAT, D, ["stone"], [("andesite", 0.14), ("cobblestone", 0.04), ("diorite", 0.06)])
    w.flood(PLAT - 1, region=(rd < 3.6) & foot)

    # ---------------- Das Loch: weite Glocke, flacher See ----------------
    R = 58 + 32 + 12
    bb = w._bbox(CX - R, BOT - 2, CZ - R, CX + R, H - 1, CZ + R)
    x0, y0, z0, x1, y1, z1 = bb
    Y, Zg, Xg = np.meshgrid(np.arange(y0, y1, dtype=float), np.arange(z0, z1, dtype=float),
                            np.arange(x0, x1, dtype=float), indexing="ij")
    th = np.arctan2(Zg - CZ, Xg - CX)
    dist = np.hypot(Xg - CX, Zg - CZ)
    t = PLAT + 2 - Y
    rr = 58 + 32 * smoothstep(0, 30, t) - 6 * smoothstep(60, 80, t)
    n = fbm3(np.cos(th) * 3 + 1, Y / 14.0, np.sin(th) * 3 - 1, 1.0, 3, 1)
    rr = rr * (1 + 0.09 * n) + fbm3(Xg, Y, Zg, 9, 2, 2) * 2.5
    below = Y < WATER
    bowl = np.clip(1 - ((WATER - Y) / (WATER - BOT)) ** 3, 0, 1) ** 0.5
    rr = np.where(below, rr * bowl, rr)
    hole = dist < rr
    sub = w.b[y0:y1, z0:z1, x0:x1]
    sub[hole] = 0
    sub[hole & (Y <= WATER)] = B("water")
    del Y, Zg, Xg, th, dist, t, rr, n, hole
    # heller Seegrund
    for y in range(BOT - 4, WATER):
        layer = w.b[y]
        g = (layer != 0) & (layer != B("water")) & (w.b[y + 1] == B("water"))
        rnd = rng.random(layer.shape)
        layer[g & (rnd < 0.6)] = B("sand")
        layer[g & (rnd >= 0.6) & (rnd < 0.85)] = B("calcite")
        layer[g & (rnd >= 0.85)] = B("clay")
    # Oberlichter
    for k, a in enumerate((0.9, 2.5, 4.0, 5.4)):
        w.cylinder(CX + np.cos(a) * 76, CZ + np.sin(a) * 76, PLAT - 26, PLAT + 12, 3.5 + k % 2, 0)
    retexture(w, 0, WATER, 0, W, WATER + 30, D, ["stone", "andesite", "diorite", "calcite"],
              [("moss", 0.18), ("mossy_cobblestone", 0.08), ("dripstone_block", 0.06)])
    # Sandinsel mit Palmen im See
    si = np.hypot(X - (CX + 34), Z - (CZ + 30))
    for y in range(BOT - 2, WATER + 2):
        m = si < (9 - max(0, y - WATER) * 3 + max(0, WATER - y) * 0.6)
        w.b[y][m] = B("sand")

    # ---------------- Spiralweg (vor den Inseln, damit er nur an der Wand entlangläuft) ----------------
    nst = 900
    spots = {}
    for i in range(nst):
        tt = i / nst
        a = A0 + tt * TURNS * 2 * np.pi
        y = int(round(PLAT - (PLAT - (WATER + 2)) * tt))
        p = wall_point(w, CX, CZ, y + 2, a, rmin=45)
        if not p:
            continue
        rwall = p[2]
        c, s_ = np.cos(a), np.sin(a)
        for q in np.arange(rwall - 3.5, rwall + 2.5, 0.5):
            x, z = CX + c * q, CZ + s_ * q
            w.set(x, y, z, B("spruce_planks"))
            for k in range(1, 5):
                if w.get(x, y + k, z) != B("water"):
                    w.set(x, y + k, z, 0)
        x, z = CX + c * (rwall - 4), CZ + s_ * (rwall - 4)
        w.set(x, y + 1, z, B("spruce_fence"), only_air=True)
        if i % 30 == 0:
            w.set(x, y + 2, z, B("lantern"), only_air=True)
        spots[i] = (a, y, rwall)

    def spot_near(a_target, y_target):
        best = min(spots.items(), key=lambda kv: abs(((kv[1][0] - a_target + np.pi) % (2 * np.pi)) - np.pi) * 40
                   + abs(kv[1][1] - y_target))
        return best[1]

    def wall_room(i, depth, width, height, floor="spruce_planks"):
        a, y, rwall = spots[min(spots, key=lambda k: abs(k - i))]
        c, s_ = np.cos(a), np.sin(a)
        mid = rwall + 2 + depth / 2
        cx, cz = CX + c * mid, CZ + s_ * mid
        carve_room(w, cx - width / 2, y + 1, cz - width / 2, cx + width / 2, y + height, cz + width / 2, floor=floor,
                   light="lantern")
        for q in np.arange(rwall - 1, rwall + 3, 0.5):
            for o in (-1, 0, 1):
                for k in range(1, 5):
                    w.set(CX + c * q - s_ * o, y + k, CZ + s_ * q + c * o, 0)
        return (int(cx), y + 1, int(cz))
    werk = wall_room(240, 14, 16, 7, floor="stone_bricks")
    farmhoehle = wall_room(780, 22, 26, 13, floor="stone_bricks")

    # Unterwasser-Raum am Spiralende
    a_uw = A0 + TURNS * 2 * np.pi
    uw_y = WATER - 10
    p = wall_point(w, CX, CZ, uw_y + 4, a_uw, rmin=30)
    uw = (CX, uw_y, CZ)
    if p:
        c, s_ = np.cos(a_uw), np.sin(a_uw)
        mid = p[2] + 9
        cx, cz = CX + c * mid, CZ + s_ * mid
        carve_room(w, cx - 8, uw_y, cz - 8, cx + 8, uw_y + 7, cz + 8, floor="dark_prismarine", light="sea_lantern",
                   round_=False)
        for o in np.arange(-6, 6.5, 0.5):
            for k in range(0, 7):
                for q in np.arange(p[2] - 2, p[2] + 6, 0.5):
                    xx, zz = CX + c * q - s_ * o, CZ + s_ * q + c * o
                    if w.get(xx, uw_y + k, zz) == B("water"):
                        continue
                    near = any(w.get(xx + dx, uw_y + k, zz + dz) == B("water")
                               for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    w.set(xx, uw_y + k, zz, B("glass") if near else 0)
        for k in range(0, WATER + 3 - uw_y):
            xx, zz = CX + c * (p[2] + 3), CZ + s_ * (p[2] + 3)
            w.box(xx - 1, uw_y + k, zz - 1, xx + 1, uw_y + k + 3, zz + 1, 0)
            w.set(xx, uw_y + k - 1, zz, B("spruce_planks"))
        uw = (int(cx), uw_y, int(cz))

    # ---------------- Schwebende Inseln in der Glocke ----------------
    isl = {}

    def place(name, ang, rx, rz, depth, seed, y=None, inset=14):
        yy = int(spiral_y(ang)) + 1 if y is None else y
        a, ys, rwall = spot_near(ang, yy)
        dist_c = rwall - 4 - inset - rx
        cx, cz = CX + np.cos(ang) * dist_c, CZ + np.sin(ang) * dist_c
        float_island(w, cx, yy, cz, rx, rz, depth, seed=seed)
        isl[name] = dict(x=int(cx), y=yy, z=int(cz), rx=rx, rz=rz, ang=ang, spot=(a, ys, rwall))
    place("lager", np.pi, 15, 14, 22, 11)
    place("zauber", np.pi / 2, 9, 9, 14, 12)
    place("farm", 1.5 * np.pi, 16, 15, 22, 13)
    float_island(w, CX - 4, 68, CZ - 2, 27, 23, 30, seed=14)
    isl["haupt"] = dict(x=CX - 4, y=68, z=CZ - 2, rx=27, rz=23)
    for i, (dx, dy, dz) in enumerate(((30, 80, 34), (-30, 58, 40), (36, 92, -34), (-38, 96, -30))):
        float_island(w, CX + dx, dy, CZ + dz, 5, 5, 8, seed=30 + i)

    top = w.column_top()
    # Hauptinsel: Kirschbaum, Teich mit Wasserfall, Wohnraum im Inselkörper
    hx, hz = isl["haupt"]["x"], isl["haupt"]["z"]
    ty = int(top[hz, hx - 6]) + 1
    tree_big(w, hx - 6, ty, hz, h=34, trunk_r=2.8, log="cherry_log", leaf="cherry_leaves", crown=16, branches=7,
             leaf2="flowering_azalea_leaves")
    bot = 68 - 30
    for k in range(7):
        a = k / 7 * 2 * np.pi
        ex, ez = hx - 6 + np.cos(a) * rng.uniform(8, 18), hz + np.sin(a) * rng.uniform(8, 18)
        ey = bot + rng.uniform(-6, 8)
        w.line((hx - 6, ty - 3, hz), (ex, ey, ez), B("cherry_log"), r=0.8)
        for j in range(int(rng.integers(4, 10))):
            w.set(ex, ey - 1 - j, ez, B("hanging_roots"), only_air=True)
    py = int(top[hz + 8, hx + 12])
    for z, x in zip(*np.nonzero(np.hypot(X - (hx + 12), Z - (hz + 8)) < 5.5)):
        w.b[py - 1:py + 1, z, x] = B("water")
        w.b[py - 2, z, x] = B("calcite")
    for x in range(hx + 12, hx + 40):
        if w.b[py - 1, hz + 8, x] == 0 and not OCCLUDES[w.b[py - 2, hz + 8, x]]:
            fall_column(w, x, x + 1, hz + 7, hz + 9, py)
            break
        w.b[py - 1:py + 1, hz + 7:hz + 10, x] = B("water")
    wy = 68 - 9
    carve_room(w, hx - 14, wy, hz - 10, hx + 6, wy + 6, hz + 8, floor="spruce_planks", light="lantern",
               round_=False)
    for z in range(hz - 8, hz + 7, 3):
        xs = hx - 15
        while xs > hx - 30 and OCCLUDES[w.b[wy + 3, z, xs]]:
            xs -= 1
        w.box(xs + 1, wy + 2, z, hx - 15, wy + 4, z, B("glass"))
    w.box(hx + 3, wy, hz + 8, hx + 5, 69, hz + 10, 0)
    for k in range(wy, 69):
        w.set(hx + 4, k, hz + 11, B("stripped_spruce_log"))
    wohn = (hx - 4, wy + 1, hz)

    # Lagerinsel innen hohl
    L_ = isl["lager"]
    ly = L_["y"] - 12
    carve_room(w, L_["x"] - 10, ly, L_["z"] - 9, L_["x"] + 10, ly + 8, L_["z"] + 9, floor="spruce_planks",
               light="lantern")
    for x in range(L_["x"] - 8, L_["x"] + 9, 3):
        w.box(x, ly, L_["z"] - 6, x, ly + 2, L_["z"] + 6, B("barrel"))
    w.box(L_["x"] + 6, ly, L_["z"] - 1, L_["x"] + 8, L_["y"] + 2, L_["z"] + 1, 0)
    lager = (L_["x"], ly + 1, L_["z"])
    # Farminsel: Felder
    F_ = isl["farm"]
    top = w.column_top()
    for z in range(F_["z"] - 10, F_["z"] + 11):
        for x in range(F_["x"] - 11, F_["x"] + 12):
            tt_ = top[z, x]
            if tt_ > 0 and w.b[tt_, z, x] == B("grass") and abs(tt_ - F_["y"]) < 6:
                if (x - F_["x"]) % 6 == 0:
                    w.b[tt_, z, x] = B("water")
                else:
                    w.b[tt_, z, x] = B("farmland")
                    w.set(x, tt_ + 1, z, B("wheat"))
    farm = (F_["x"], F_["y"] + 2, F_["z"])
    # Verzauberung
    Z_ = isl["zauber"]
    vy = int(w.column_top()[Z_["z"], Z_["x"]]) + 1
    for a in np.linspace(0, 2 * np.pi, 20, endpoint=False):
        if np.cos(a) < -0.85:
            continue
        w.set(Z_["x"] + 4 * np.cos(a), vy, Z_["z"] + 4 * np.sin(a), B("bookshelf"))
        w.set(Z_["x"] + 4 * np.cos(a), vy + 1, Z_["z"] + 4 * np.sin(a), B("bookshelf"))
    w.set(Z_["x"], vy, Z_["z"], B("lantern"))
    zauber = (Z_["x"], vy, Z_["z"])

    # ---------------- Brücken ----------------
    top = w.column_top()

    def island_edge(name, toward):
        c = isl[name]
        dv = np.array([toward[0] - c["x"], toward[1] - c["z"]], float)
        dv /= np.linalg.norm(dv)
        last = None
        for q in np.arange(0, 60, 0.5):
            x, z = int(c["x"] + dv[0] * q), int(c["z"] + dv[1] * q)
            if top[z, x] < 0 or abs(top[z, x] - c["y"]) > 8:
                break
            last = (x, int(top[z, x]) + 1, z)
        return last
    for name in ("lager", "zauber", "farm"):
        a, ys, rwall = isl[name]["spot"]
        pw = (CX + np.cos(a) * (rwall - 3.5), ys, CZ + np.sin(a) * (rwall - 3.5))
        pe = island_edge(name, (pw[0], pw[2]))
        if pe:
            bridge(w, pw, pe, sag=3)
    for a_, b_ in (("lager", "haupt"), ("farm", "haupt"), ("zauber", "lager")):
        pa = island_edge(a_, (isl[b_]["x"], isl[b_]["z"]))
        pb = island_edge(b_, (isl[a_]["x"], isl[a_]["z"]))
        if pa and pb:
            bridge(w, pa, pb, sag=4)

    # ---------------- Lianen, Wasserfälle über den Rand ----------------
    for a in np.linspace(0, 2 * np.pi, 110, endpoint=False):
        p = wall_point(w, CX, CZ, PLAT - 1, a + rng.uniform(-0.03, 0.03), rmin=45)
        if not p:
            continue
        L = rng.uniform(10, 50)
        leaf = "jungle_leaves" if rng.random() < 0.5 else ("azalea_leaves" if rng.random() < 0.7 else "cave_vines")
        for y in range(PLAT, int(PLAT - L), -1):
            if w.get(p[0], y, p[1]) == 0:
                w.set(p[0], y, p[1], B(leaf))
    fall_column(w, 172, 177, 166, 171, PLAT)
    fall_column(w, 255, 258, 233, 238, PLAT)
    for (x0_, x1_, z0_, z1_) in ((171, 178, 145, 172), (250, 262, 230, 241)):
        for x in range(x0_, x1_ + 1):
            for z in range(z0_, z1_ + 1):
                if w.b[PLAT - 1, z, x] == 0 and OCCLUDES[w.b[PLAT - 2, z, x]]:
                    w.b[PLAT - 1, z, x] = B("water")
    for name in ("lager", "farm", "haupt"):
        c = isl[name]
        for _ in range(3):
            vine_curtain(w, c["x"], c["z"], c["y"] - 1, rng.uniform(6, 16), rng.uniform(0, 6.28), leaf="azalea_leaves")
    tree_palm(w, CX + 34, WATER + 2, CZ + 30, h=9)
    tree_palm(w, CX + 30, WATER + 2, CZ + 33, h=7)

    # ---------------- Glasplattform + Shop am Rand ----------------
    p = wall_point(w, CX, CZ, PLAT + 1, np.pi * 0.5, rmin=40)
    rim_r = p[2] if p else 60
    px0 = CX - 6
    pz_rim = int(CZ + rim_r)
    w.box(px0, PLAT, pz_rim - 22, px0 + 12, PLAT, pz_rim + 2, B("glass"))
    for x in range(px0, px0 + 13):
        w.set(x, PLAT + 1, pz_rim - 22, B("spruce_fence"))
    for z in range(pz_rim - 22, pz_rim + 3):
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
    ground = np.isin(gb, [B("grass"), B("podzol")]) & (top > PLAT - 6) & foot & (np.hypot(X - CX, Z - CZ) > 76)
    for zz, xx in scatter_points(w, ground, 140, 12):
        tree_jungle(w, xx, top[zz, xx] + 1, zz)
    for zz, xx in scatter_points(w, ground, 240, 7):
        tree_round(w, xx, top[zz, xx] + 1, zz, log="jungle_log", leaf="jungle_leaves", r=rng.uniform(2.4, 3.4))
    for zz, xx in scatter_points(w, ground, 450, 4):
        bush(w, xx, top[zz, xx] + 1, zz, leaf="azalea_leaves" if rng.random() < 0.5 else "jungle_leaves")
    isl_grass = (gb == B("grass")) & (top < PLAT - 8) & (top > WATER + 10)
    for zz, xx in scatter_points(w, isl_grass, 30, 6):
        bush(w, xx, top[zz, xx] + 1, zz, leaf="flowering_azalea_leaves")
    paint_path(w, smooth_polyline([(CX, shop_z + 14), (CX + 10, shop_z + 40), (CX + 30, 420)], 8), width=1.6,
               lanterns=12, allowed=("grass", "podzol", "dirt"))

    a, ys, rwall = spots[0]
    zones = [
        dict(name="Einstieg zum Spiralweg", typ="eingang", pos=(int(CX + np.cos(a) * rwall), PLAT + 1,
                                                                  int(CZ + np.sin(a) * rwall)),
             text="Am Rand beginnt der Holzweg an der Wand. Von ihm zweigen Hängebrücken zu den schwebenden "
                  "Inseln ab, unten endet er am türkisen See."),
        dict(name="Glasplattform und Shop", typ="shop", pos=(CX, PLAT + 2, shop_z + 7),
             text="Eine Glasplattform ragt 22 Blöcke über den Abgrund. Dahinter liegt der Marktplatz für Besucher."),
        dict(name="Hauptinsel mit Kirschbaum", typ="highlight", pos=(hx - 6, ty + 20, hz),
             text="Die größte Insel schwebt mitten im Loch, 38 Blöcke über dem See. Ein Kirschbaum wächst zur "
                  "Öffnung hinauf, Wurzeln hängen nach unten, ein Teich läuft als Wasserfall in den See."),
        dict(name="Wohnraum in der Hauptinsel", typ="wohnen", innen=True, pos=wohn, cut=6,
             text="Ein Raum im Inselkörper unter dem Kirschbaum, mit Glasfenstern zur Seite. Eine Leiter führt "
                  "nach oben auf die Insel."),
        dict(name="Lagerinsel", typ="lager", innen=True, pos=lager, cut=7,
             text="Eine hohle Insel an der Westseite mit Fassregalen. Eine Brücke kommt vom Spiralweg, eine "
                  "zweite führt zur Hauptinsel."),
        dict(name="Farminsel", typ="farm", pos=farm,
             text="Weizenfelder auf einer schwebenden Insel an der Nordseite, verbunden mit Wand und Hauptinsel."),
        dict(name="Verzauberungsinsel", typ="werkstatt", pos=zauber,
             text="Eine kleine Insel mit Bücherregal-Ring an der Südseite, direkt unter der Glasplattform."),
        dict(name="Werkstatt in der Wand", typ="werkstatt", innen=True, pos=werk, cut=7,
             text="Eine Kammer am oberen Teil des Spiralwegs."),
        dict(name="Farmhöhle", typ="farm", innen=True, pos=farmhoehle, cut=10,
             text="Eine 13 Blöcke hohe Halle kurz über dem See, für Eisen- oder Mobfarmen."),
        dict(name="Türkiser See", typ="highlight", pos=(CX + 34, WATER + 2, CZ + 30),
             text="Ein flacher See mit weißem Sand- und Calcitgrund, eine Sandinsel mit Palmen. Hier landen alle "
                  "Wasserfälle."),
        dict(name="Unterwasser-Raum", typ="wohnen", innen=True, pos=uw, cut=8,
             text="Am Ende des Spiralwegs geht es hinunter in einen Raum mit Glaswand zum türkisen See."),
    ]
    info = dict(
        slug=SLUG, nr=8, title="Das Himmelsloch",
        tagline="Ein Riesenloch im Dschungel mit schwebenden Inseln über einem türkisen See.",
        story=[
            "Kombination aus Riesen-Doline, schwebenden Inseln und türkisem See. Oben öffnet sich im Dschungel "
            "ein 120 Blöcke breites Loch, darunter weitet es sich zu einer Glocke von 180 Blöcken.",
            "In der Glocke schweben vier Inseln über einem flachen, türkisen See. Auf der größten wächst ein "
            "Kirschbaum dem Licht entgegen, von ihr läuft ein Wasserfall in den See.",
            "Ein Spiralweg führt an der Wand hinunter. Hängebrücken gehen von ihm zu den Inseln: Lager, Farm, "
            "Verzauberung und die Hauptinsel mit dem Wohnraum.",
        ],
        ground_y=PLAT, water_level=WATER, paste_y=63 - PLAT,
        paste_note="Dann liegt der Dschungel auf Y 63 und der türkise See auf Y {water_world}.",
        water_color="#38cfe0", sky_color="#a8cfe3",
        surround=dict(kind="grass", color="#4a8a2c"),
        camera=dict(target=(CX, 50, CZ + 10), pos=(CX + 100, 280, CZ + 220)),
        clip=None,
        zones=zones,
        phasen=[
            ("Loch ausheben", "Oben 120 Blöcke Durchmesser, darunter breiter (Glocke). Den Boden flach "
                              "lassen, er wird zum See."),
            ("See", "Grund mit weißem Sand und Calcit auslegen, 2–14 Blöcke tief füllen. Eine Sandinsel mit "
                    "Palmen aufschütten."),
            ("Spiralweg", "Den Weg an der Wand von oben nach unten bauen. Er dient als Gerüst für alles Weitere."),
            ("Schwebende Inseln", "Vom Spiralweg aus Brücken ins Leere bauen und daran die Inseln aufhängen: "
                                  "erst die Oberseite, dann die Unterseite nach unten."),
            ("Base", "Wohnraum, Lager, Farm, Verzauberung, Werkstatt, Unterwasser-Raum."),
            ("Leben", "Kirschbaum, Lianen, Wasserfälle, Glasplattform und Dschungel oben."),
        ],
        tipps=[
            "Türkis wird das Wasser am stärksten in warmen Biomen (warmer Ozean). Ein heller, flacher Grund "
            "hilft überall.",
            "In der Glocke ist es schattig. Laternen an Ketten unter den Inseln und Seelaternen im See machen "
            "es nachts magisch.",
            "Beim Bau der Inseln über dem Abgrund: Gerüst nutzen und Feder-Fall-Stiefel anziehen.",
        ],
    )
    return w, info
