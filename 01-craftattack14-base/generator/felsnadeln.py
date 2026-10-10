"""Landschaft 2: Die Felsnadeln.

Ein dichter Urwald mit Fluss und See, aus dem über 40 Felstürme bis zu 185 Blöcke hoch aufragen.
Jeder Funktionsturm der Base ist ein eigener Fels, verbunden durch Hängebrücken.
"""
import numpy as np

from mclib import (B, World, arch, bridge, bush, carve_room, fbm2, float_island, leaf_blob, paint_path, pillar,
                   polyline_dist, radial_surface, retexture, smooth_polyline, smoothstep, tree_big, tree_jungle,
                   tree_round, tree_spruce, tunnel_out, vine_curtain)

W, H, D = 360, 232, 540
GROUND = 30
WATER = GROUND - 1
SLUG = "felsnadeln"
CX, CZ = 180, 270


def generate():
    w = World(W, H, D, seed=22)
    X, Z = w.X, w.Z
    rng = w.rng

    # ---------------- Urwaldboden ----------------
    wx = X + fbm2(X, Z, 60, 3, 1) * 18
    wz = Z + fbm2(X, Z, 60, 3, 2) * 18
    e = np.hypot((wx - CX) / 168, (wz - CZ) / 255)
    foot = e < 1.0
    h = GROUND + fbm2(X, Z, 45, 4, 3) * 3.5 + np.maximum(0, fbm2(X, Z, 70, 3, 4)) * 6
    h = GROUND + (h - GROUND) * (1 - smoothstep(0.85, 1.0, e))

    river_pts = smooth_polyline([(120, 0), (150, 70), (122, 150), (160, 215), (140, 330), (182, 392),
                                 (240, 470), (225, 540)], 10)
    rd = polyline_dist(X, Z, river_pts)
    ld = np.hypot((X - 190) / 46, (Z - 405) / 30) + fbm2(X, Z, 18, 2, 5) * 0.15
    water = ((rd < 4.5) | (ld < 1.0)) & foot
    h = np.where(rd < 9, np.minimum(h, WATER - 3 + smoothstep(4.5, 9, rd) * (h - WATER + 3)), h)
    h = np.where(ld < 1.25, np.minimum(h, WATER - 2 - 5 * smoothstep(1.0, 0.2, ld)
                                       + smoothstep(1.0, 1.25, ld) * 6), h)

    surf = np.full(h.shape, B("grass"), np.uint8)
    r = rng.random(h.shape)
    mixn = fbm2(X, Z, 14, 2, 6)
    surf[(mixn > 0.25) & (r < 0.7)] = B("podzol")
    surf[(mixn < -0.3) & (r < 0.6)] = B("moss")
    surf[(rd < 6.5) | (ld < 1.1)] = B("gravel")
    surf[((rd < 7.5) | (ld < 1.2)) & (h >= WATER) & (r < 0.6)] = B("mud")
    rock = w.strata(["stone", "andesite", "stone", "tuff"], band=3, seed=7)
    w.fill_heightmap(np.where(foot, h, -1), surf, "dirt", 3, rock_fn=rock, bottom=np.full(h.shape, GROUND - 14.0))
    w.flood(WATER, region=water | ((rd < 9) & foot) | ((ld < 1.25) & foot))

    # ---------------- Felsnadeln ----------------
    towers = {
        "haupt": dict(x=CX, z=262, r=25, h=172, rough=0.1),
        "lager": dict(x=104, z=212, r=17, h=128, rough=0.18),
        "farm": dict(x=258, z=214, r=19, h=118, rough=0.18),
        "werk": dict(x=236, z=338, r=15, h=112, rough=0.2),
        "aussicht": dict(x=112, z=326, r=10, h=188, rough=0.18, taper=0.45),
    }
    radius = {}
    seed = 100
    for k, t in towers.items():
        seed += 7
        top = w.column_top()
        base = int(top[t["z"], t["x"]]) - 2
        t["base"] = base
        radius[k] = pillar(w, t["x"], t["z"], base, t["h"], t["r"], seed=seed, rough=t["rough"],
                           taper=t.get("taper", 0.3))
    placed = [(t["x"], t["z"], t["r"]) for t in towers.values()]
    others = []
    cand = rng.permutation(np.argwhere(foot & (e < 0.86) & (rd > 12) & (ld > 1.3)))
    for z, x in cand:
        r0 = float(rng.uniform(6, 17))
        ok = all(np.hypot(x - px, z - pz) > (r0 + pr) * 1.35 + 8 for px, pz, pr in placed)
        if not ok:
            continue
        placed.append((int(x), int(z), r0))
        others.append((int(x), int(z), r0))
        if len(others) >= 40:
            break
    top = w.column_top()
    other_info = []
    for i, (x, z, r0) in enumerate(others):
        hh = int(rng.uniform(45, 150) * (0.6 + r0 / 25))
        hh = min(hh, H - GROUND - 12)
        base = int(top[z, x]) - 2
        fn = pillar(w, x, z, base, hh, r0, seed=300 + i * 13, rough=float(rng.uniform(0.15, 0.32)),
                    taper=float(rng.uniform(0.2, 0.45)))
        other_info.append((x, z, r0, base, hh, fn))

    # ---------------- Grün auf und an den Nadeln ----------------
    allp = [(t["x"], t["z"], t["r"], t["base"], t["h"]) for t in towers.values()] + \
           [(x, z, r0, b, hh) for x, z, r0, b, hh, _ in other_info]
    for i, (x, z, r0, base, hh) in enumerate(allp):
        top_y = base + hh
        # Bäume oben
        n_trees = max(1, int(r0 * r0 / 70))
        for _ in range(n_trees):
            a = rng.uniform(0, 2 * np.pi)
            rr = rng.uniform(0, r0 * 0.45)
            tx, tz = int(x + np.cos(a) * rr), int(z + np.sin(a) * rr)
            colt = w.column_top()[tz, tx]
            if w.b[colt, tz, tx] in (B("grass"), B("dirt")):
                kind = rng.random()
                if kind < 0.4:
                    tree_spruce(w, tx, colt + 1, tz, h=int(rng.integers(8, 15)))
                elif kind < 0.7:
                    tree_round(w, tx, colt + 1, tz, log="dark_oak_log", leaf="dark_oak_leaves",
                               r=rng.uniform(2.5, 3.5))
                else:
                    bush(w, tx, colt + 1, tz, leaf="flowering_azalea_leaves", r=rng.uniform(2, 3))
        # Lianenvorhänge
        for _ in range(int(2 + r0 / 4)):
            vine_curtain(w, x, z, top_y - 1, rng.uniform(8, hh * 0.5), rng.uniform(0, 2 * np.pi),
                         leaf="azalea_leaves" if rng.random() < 0.6 else "jungle_leaves", width=int(rng.integers(1, 4)))
        # bewachsene Simse
        for _ in range(int(rng.integers(0, 3))):
            yl = int(base + hh * rng.uniform(0.3, 0.8))
            for a in np.linspace(0, 2 * np.pi, int(r0 * 1.5), endpoint=False):
                if rng.random() < 0.55:
                    p = radial_surface(w, x, z, yl, a + rng.uniform(-0.1, 0.1))
                    if p:
                        leaf_blob(w, p[0], yl, p[1], rng.uniform(1.2, 2.2), "jungle_leaves", ry=1.0)

    # ---------------- Wasserfälle von Nadeln ----------------
    falls = []
    for k in ("haupt", "farm", "aussicht"):
        t = towers[k]
        falls.append((t["x"], t["z"], t["base"] + t["h"] - 3, t["r"]))
    for x, z, r0, base, hh, _ in sorted(other_info, key=lambda o: -o[4])[:4]:
        falls.append((x, z, base + hh - 3, r0))
    for i, (x, z, ytop, r0) in enumerate(falls):
        side = [(1, "x"), (-1, "x"), (1, "z"), (-1, "z")][i % 4]
        s, ax = side
        if ax == "x":
            start = int(x + s * (r0 * 2.2 + 6))
            w.face_water(int(z) - 1, int(z) + 1, ytop, WATER - 1, min(W - 1, max(0, start)), -s, axis="x", depth=1)
        else:
            start = int(z + s * (r0 * 2.2 + 6))
            w.face_water(int(x) - 1, int(x) + 1, ytop, WATER - 1, min(D - 1, max(0, start)), -s, axis="z", depth=1)

    # ---------------- Schwebende Felsen ----------------
    float_pos = [(70, 150, 120), (285, 175, 150), (300, 160, 300), (60, 185, 430), (150, 195, 160),
                 (275, 170, 440)]
    for i, (fx, fy, fz) in enumerate(float_pos):
        res = float_island(w, fx, fy, fz, rng.uniform(9, 15), rng.uniform(8, 13), rng.uniform(12, 20), seed=500 + i)
        top = w.column_top()
        if res is not None:
            if top[fz, fx] > 0:
                tree_round(w, fx, top[fz, fx] + 1, fz, log="dark_oak_log", leaf="azalea_leaves", r=3.2)
            vine_curtain(w, fx, fz, fy - 2, 14, rng.uniform(0, 6.28), leaf="azalea_leaves")

    # ---------------- Himmelsbrücke (natürlicher Bogen) ----------------
    a, b = towers["haupt"], towers["werk"]
    ya = a["base"] + 120
    pa = radial_surface(w, a["x"], a["z"], ya, np.arctan2(b["z"] - a["z"], b["x"] - a["x"]))
    pb = radial_surface(w, b["x"], b["z"], b["base"] + 90, np.arctan2(a["z"] - b["z"], a["x"] - b["x"]))

    # ---------------- Base im Hauptturm ----------------
    t = towers["haupt"]
    hx, hz, hb = t["x"], t["z"], t["base"]
    floors = [hb + 30, hb + 62, hb + 94, hb + 126]
    names = ["Eingangshalle", "Wohnbereich", "Schlafzimmer", "Bibliothek"]
    for i, fy in enumerate(floors):
        rr = radius["haupt"](fy + 4) * 0.62
        carve_room(w, hx - rr, fy, hz - rr, hx + rr, fy + 9, hz + rr, floor="spruce_planks", light="lantern")
        # Fenster rundum
        for k in range(6):
            ang = k / 6 * 2 * np.pi + i * 0.3
            p = radial_surface(w, hx, hz, fy + 4, ang)
            if p:
                for s in np.arange(rr - 1, p[2] + 0.5, 0.5):
                    for o in (-2, -1, 0, 1, 2):
                        x = hx + np.cos(ang) * s - np.sin(ang) * o
                        z = hz + np.sin(ang) * s + np.cos(ang) * o
                        for yy in range(fy + 2, fy + 7):
                            w.set(x, yy, z, 0)
                for o in (-2, -1, 0, 1, 2):
                    x = hx + np.cos(ang) * (p[2] - 1) - np.sin(ang) * o
                    z = hz + np.sin(ang) * (p[2] - 1) + np.cos(ang) * o
                    for yy in range(fy + 2, fy + 7):
                        w.set(x, yy, z, B("glass"))
    w.box(hx - 4, floors[3] - 1, hz - 6, hx + 4, floors[3] + 3, hz + 6, B("bookshelf"), replace=[0])
    # Wasser-Aufzug (Blasensäule) durch alle Stockwerke
    w.set(hx, hb, hz, B("soul_sand"))
    for y in range(hb + 1, floors[3] + 8):
        w.set(hx, y, hz, B("water"))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            if w.get(hx + dx, y, hz + dz) == 0 or (y - hb) % 32 not in range(30, 32):
                w.set(hx + dx, y, hz + dz, B("glass"))
    for fy in floors:
        w.box(hx - 1, fy, hz - 1, hx + 1, fy + 2, hz + 1, B("glass"))
        w.set(hx, fy, hz, B("water"))
        w.set(hx + 1, fy, hz, 0)
        w.set(hx + 1, fy + 1, hz, 0)
    # Tor am Fuß
    door = tunnel_out(w, (hx, int(w.column_top()[hz, hx + int(t["r"] * 2)]) + 1, hz), (hx, hz + 200), width=5,
                      height=7, floor="stone_bricks")
    w.box(hx - 3, hb + 4, hz - 3, hx + 3, hb + 10, hz + 3, 0)

    # Wendeltreppe außen um den Hauptturm bis zur Eingangshalle
    y_start = GROUND + 1
    y_end = floors[0] - 1
    turns = 1.6
    nst = int((y_end - y_start) * 3)
    for i in range(nst):
        tt = i / nst
        ang = np.pi / 2 + tt * turns * 2 * np.pi
        yy = int(y_start + (y_end - y_start) * tt)
        p = radial_surface(w, hx, hz, yy + 2, ang)
        if not p:
            continue
        for o in range(0, 4):
            x = hx + np.cos(ang) * (p[2] + o - 0.5)
            z = hz + np.sin(ang) * (p[2] + o - 0.5)
            w.set(x, yy, z, B("spruce_planks"))
            for k in range(1, 4):
                if w.get(x, yy + k, z) not in (0,):
                    w.set(x, yy + k, z, 0)
        x = hx + np.cos(ang) * (p[2] + 3.6)
        z = hz + np.sin(ang) * (p[2] + 3.6)
        w.set(x, yy + 1, z, B("spruce_fence"), only_air=True)
        if i % 24 == 0:
            w.set(x, yy + 2, z, B("lantern"), only_air=True)
    top_ang = np.pi / 2 + turns * 2 * np.pi
    tunnel_out(w, (hx, y_end + 1, hz), (hx + np.cos(top_ang) * 100, hz + np.sin(top_ang) * 100), width=3,
               height=4)

    # ---------------- Lagerturm ----------------
    t = towers["lager"]
    ly = t["base"] + 62
    lr = radius["lager"](ly + 4) * 0.62
    carve_room(w, t["x"] - lr, ly, t["z"] - lr, t["x"] + lr, ly + 10, t["z"] + lr, floor="spruce_planks",
               light="lantern")
    for x in range(int(t["x"] - lr + 2), int(t["x"] + lr - 1), 3):
        w.box(x, ly, t["z"] - lr * 0.5, x, ly + 2, t["z"] + lr * 0.5, B("barrel"))
    # ---------------- Farmturm ----------------
    t = towers["farm"]
    farm_floors = [t["base"] + 30, t["base"] + 46, t["base"] + 62]
    for fy in farm_floors:
        fr = radius["farm"](fy + 4) * 0.62
        carve_room(w, t["x"] - fr, fy, t["z"] - fr, t["x"] + fr, fy + 11, t["z"] + fr, floor="stone_bricks",
                   light="lantern", round_=False)
    # ---------------- Werkstatt ----------------
    t = towers["werk"]
    wy = t["base"] + t["h"] - 12
    wr = radius["werk"](wy) * 0.6
    carve_room(w, t["x"] - wr, wy, t["z"] - wr, t["x"] + wr, wy + 7, t["z"] + wr, floor="stone_bricks",
               light="lantern")
    for i, blk in enumerate(["crafting_table", "smithing_table", "anvil", "blast_furnace", "blast_furnace", "barrel"]):
        w.set(t["x"] - wr + 2 + i * 2, wy, t["z"] - wr + 2, B(blk))
    # ---------------- Aussicht ----------------
    t = towers["aussicht"]
    ay = int(w.column_top()[t["z"], t["x"]]) + 1
    w.box(t["x"] - 5, ay, t["z"] - 5, t["x"] + 5, ay, t["z"] + 5, B("spruce_planks"))
    w.box(t["x"] - 5, ay + 1, t["z"] - 5, t["x"] + 5, ay + 12, t["z"] + 5, 0)
    for (x, z) in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
        for k in range(1, 4):
            w.set(t["x"] + x, ay + k, t["z"] + z, B("spruce_fence"))
        w.set(t["x"] + x, ay + 4, t["z"] + z, B("lantern"))

    # ---------------- Hängebrücken ----------------
    def link(a, ya, b, yb, sag):
        ta, tb = towers[a], towers[b]
        ea = tunnel_out(w, (ta["x"], ya, ta["z"]), (tb["x"], tb["z"]), width=3, height=4)
        eb = tunnel_out(w, (tb["x"], yb, tb["z"]), (ta["x"], ta["z"]), width=3, height=4)
        if ea and eb:
            bridge(w, ea, eb, sag=sag)
        return ea, eb
    link("haupt", floors[1], "lager", ly, 6)
    link("haupt", floors[0], "farm", farm_floors[1], 5)
    link("haupt", floors[2], "werk", wy, 5)
    link("haupt", floors[1], "aussicht", floors[1] - 8, 4)
    arch(w, (pa[0], ya - 30, pa[1]) if pa else (200, 150, 300), (pb[0], b["base"] + 70, pb[1]) if pb else (230, 140, 330),
         height=18, thick=3.0, blk="stone")

    # ---------------- Steg und Shop am See ----------------
    sx, sz = 196, 372
    w.box(sx - 3, WATER + 1, sz, sx + 3, WATER + 1, sz + 24, B("spruce_planks"))
    for z in range(sz, sz + 25, 4):
        for x in (sx - 3, sx + 3):
            for y in range(WATER - 4, WATER + 1):
                w.set(x, y, z, B("spruce_log"))
            w.set(x, WATER + 2, z, B("spruce_fence"))
    w.box(sx - 10, WATER + 1, sz - 12, sx + 10, WATER + 1, sz - 1, B("spruce_planks"))
    w.box(sx - 10, WATER + 2, sz - 12, sx + 10, WATER + 10, sz - 1, 0)
    for x in range(sx - 8, sx + 9, 5):
        w.box(x, WATER + 2, sz - 10, x + 2, WATER + 2, sz - 10, B("barrel"))
        w.set(x + 1, WATER + 3, sz - 10, B("lantern"))
    paint_path(w, smooth_polyline([(sx, sz - 10), (186, 330), (CX, door[2] + 3 if door else 300)], 8), width=1.6,
               lanterns=10)

    # ---------------- Urwald ----------------
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    ground = np.isin(gb, [B("grass"), B("podzol"), B("moss")]) & (np.abs(top - GROUND) < 10) & foot
    for zz, xx in scatter_points_safe(w, ground, 170, 13):
        tree_jungle(w, xx, top[zz, xx] + 1, zz)
    for zz, xx in scatter_points_safe(w, ground, 300, 8):
        if rng.random() < 0.5:
            tree_round(w, xx, top[zz, xx] + 1, zz, log="dark_oak_log", leaf="dark_oak_leaves",
                       r=rng.uniform(2.6, 3.8), h=int(rng.integers(6, 10)))
        else:
            tree_round(w, xx, top[zz, xx] + 1, zz, log="jungle_log", leaf="jungle_leaves")
    for zz, xx in scatter_points_safe(w, ground, 600, 4):
        bush(w, xx, top[zz, xx] + 1, zz, leaf="azalea_leaves" if rng.random() < 0.6 else "flowering_azalea_leaves")
    for zz, xx in scatter_points_safe(w, ground & (e < 0.7), 6, 60):
        tree_big(w, xx, top[zz, xx] + 1, zz, h=int(rng.integers(28, 38)), trunk_r=2.2, log="jungle_log",
                 leaf="jungle_leaves", crown=11, leaf2="azalea_leaves")

    tH = towers["haupt"]
    zones = [
        dict(name="Tor am Fuß des Hauptturms", typ="eingang", pos=(CX, GROUND + 3, door[2] if door else 300),
             text="Ein 5 Blöcke breites Tor führt in den Fels. Von hier geht es mit dem Wasser-Aufzug nach oben, "
                  "oder außen über die Wendeltreppe."),
        dict(name="Wendeltreppe", typ="highlight", pos=(CX + 26, GROUND + 18, tH["z"]),
             text="Eine 4 Blöcke breite Holztreppe windet sich 1,6-mal um den Hauptturm, vom Waldboden bis zur "
                  "Eingangshalle 30 Blöcke darüber. Alle paar Meter hängt eine Laterne."),
        dict(name="Eingangshalle", innen=True, typ="wohnen", pos=(CX, floors[0] + 1, tH["z"]),
             text="Die erste runde Halle im Hauptturm hat sechs Panoramafenster. Durch die Mitte läuft der "
                  "gläserne Wasser-Aufzug. Eine Hängebrücke führt zum Farmturm."),
        dict(name="Wohnbereich", innen=True, typ="wohnen", pos=(CX, floors[1] + 1, tH["z"]),
             text="Die zweite Halle liegt 62 Blöcke über dem Boden. Von hier gehen Brücken zum Lagerturm und "
                  "zum Aussichtsturm."),
        dict(name="Schlafzimmer", innen=True, typ="wohnen", pos=(CX, floors[2] + 1, tH["z"]),
             text="Die dritte Halle mit Blick über den Urwald. Eine Brücke führt zur Werkstatt."),
        dict(name="Bibliothek", innen=True, typ="werkstatt", pos=(CX, floors[3] + 1, tH["z"]),
             text="Die oberste Halle mit Bücherregalen in der Mitte. Gut geeignet zum Verzaubern. Darüber liegt "
                  "der Gipfelgarten."),
        dict(name="Lagerturm", innen=True, typ="lager", pos=(towers["lager"]["x"], ly + 1, towers["lager"]["z"]),
             text="Eine runde Halle 62 Blöcke über dem Boden mit Regalreihen aus Fässern. Sie ist per "
                  "Hängebrücke mit dem Wohnbereich verbunden."),
        dict(name="Farmturm", innen=True, typ="farm", pos=(towers["farm"]["x"], farm_floors[1] + 1, towers["farm"]["z"]),
             text="Drei übereinanderliegende Farm-Etagen (je 11 hoch), zum Beispiel für Eisen, Tiere und "
                  "Mobs. Die Brücke kommt in der mittleren Etage an."),
        dict(name="Werkstatt", innen=True, typ="werkstatt", pos=(towers["werk"]["x"], wy + 1, towers["werk"]["z"]),
             text="Die Werkstatt liegt direkt unter dem Gipfel des Werkstattturms. Daneben spannt sich die "
                  "Himmelsbrücke, ein natürlicher Felsbogen."),
        dict(name="Aussichtsturm", typ="highlight", pos=(towers["aussicht"]["x"], ay, towers["aussicht"]["z"]),
             text=f"Die dünnste und höchste Nadel: {ay - GROUND} Blöcke über dem Wald. Oben ist eine Plattform mit "
                  "Laternen."),
        dict(name="Bootssteg und Shop", typ="shop", pos=(sx, WATER + 2, sz - 6),
             text="Ein Marktplatz aus Holz am See mit einem Steg. Besucher kommen mit dem Boot über den Fluss."),
        dict(name="Schwebende Felsen", typ="highlight", pos=(float_pos[1][0], float_pos[1][1] + 3, float_pos[1][2]),
             text="Sechs Felsbrocken schweben zwischen den Nadeln, mit Bäumen oben und Wurzeln unten."),
    ]
    info = dict(
        slug=SLUG, nr=2, title="Die Felsnadeln",
        tagline=f"{5 + len(others)} Felstürme ragen aus dem Urwald, verbunden durch Hängebrücken.",
        story=[
            f"Ein dichter Urwald mit Fluss und See. Daraus ragen {5 + len(others)} Felsnadeln bis zu 188 Blöcke hoch auf. "
            "Oben wachsen Bäume, an den Seiten hängen Lianen, und von manchen stürzen Wasserfälle.",
            "Die Base verteilt sich auf fünf Türme: Im Hauptturm liegen vier runde Hallen übereinander. Ein "
            "gläserner Wasser-Aufzug verbindet sie. Hängebrücken führen zum Lagerturm, Farmturm, Werkstattturm "
            "und Aussichtsturm.",
            "Zwischen den Nadeln schweben Felsbrocken. Ein natürlicher Felsbogen, die Himmelsbrücke, verbindet "
            "zwei Türme.",
        ],
        ground_y=GROUND, water_level=WATER, paste_y=63 - GROUND,
        paste_note="Dann liegt der Waldboden auf Y 63, und die höchste Nadel reicht bis Y {welt_max}.",
        water_color="#2f86a8", sky_color="#a9cbe0",
        surround=dict(kind="grass", color="#4f7f30"),
        camera=dict(target=(CX, 110, 290), pos=(CX + 300, 230, 640)),
        clip=None,
        zones=zones,
        phasen=[
            ("Grundriss", "Positionen der Nadeln mit Wollsäulen markieren. Zuerst die fünf Base-Türme, dann die "
                          "Deko-Nadeln dazwischen."),
            ("Hauptturm hochziehen", "Den Hauptturm als Hülle bauen (außen Fels, innen hohl). Die vier Hallen "
                                     "gleich beim Hochbauen aussparen. Das spart Hunderttausende Blöcke."),
            ("Aufzug und Treppe", "Seelensand unten, Wassersäule bis oben, Glas drumherum. Danach außen die "
                                  "Wendeltreppe anbringen."),
            ("Weitere Türme", "Lager-, Farm-, Werkstatt- und Aussichtsturm bauen und mit Hängebrücken verbinden."),
            ("Deko-Nadeln", "Die übrigen Nadeln nach und nach hinzufügen. Hier reicht eine Hülle von 2 Blöcken "
                            "Dicke."),
            ("Urwald und Wasser", "Fluss, See, Wasserfälle und zuletzt der Urwald mit Lianen."),
        ],
        tipps=[
            "Die Nadeln mit senkrechten Streifen aus Stein, Andesit und Tuff bauen und Moosflecken einstreuen. "
            "So sehen sie aus wie echter, verwitterter Fels.",
            "Hohl bauen: Eine 2–3 Blöcke dicke Hülle sieht von außen genauso aus und braucht nur einen "
            "Bruchteil der Blöcke.",
            "Für den Wasser-Aufzug unten Seelensand setzen (nach oben) oder Magmablock (nach unten).",
        ],
    )
    return w, info


def scatter_points_safe(w, mask, n, dist):
    from mclib import scatter_points
    return scatter_points(w, mask, n, dist)
