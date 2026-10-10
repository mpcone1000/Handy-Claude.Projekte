"""Landschaft 5: Die leuchtende Unterwelt.

Oben eine ganz normale Wiese mit einem unauffälligen Loch. Darunter eine 280 × 390 Blöcke große Höhle,
bis zu 75 Blöcke hoch, mit unterirdischem See, Riesenpilzen, Tropfsteinen, Leuchtbeeren und einer Amethyst-Geode.
"""
import numpy as np

from mclib import (B, OCCLUDES, World, arch, bush, carve_room, fbm2, fbm3, leaf_blob, paint_path, polyline_dist,
                   retexture, scatter_points, smooth_polyline, smoothstep, tree_round, tree_spruce)

W, H, D = 320, 130, 440
SURF = 112
WATER = 20
SLUG = "leuchtende-unterwelt"
CX, CZ = 160, 220


def mushroom(w, x, y, z, h, r, cap="red_mushroom_block", light="shroomlight", hollow=False):
    w.cylinder(x, z, y, y + h, 1.6 if r < 8 else 2.4, B("mushroom_stem"))
    w.cylinder(x, z, y, y + 1, (1.6 if r < 8 else 2.4) + 1.2, B("mushroom_stem"))
    w.ellipsoid(x, y + h, z, r, r * 0.55, r, B(cap), lower_only=False)
    w.ellipsoid(x, y + h - 1.5, z, r - 1.2, r * 0.45, r - 1.2, 0)
    w.box(x - r - 1, y + h - r, z - r - 1, x + r + 1, y + h - 1, z + r + 1, 0, replace=[B(cap)])
    # Lichter an der Unterseite des Hutes
    for a in np.linspace(0, 2 * np.pi, int(r * 1.6), endpoint=False):
        rr = r * w.rng.uniform(0.35, 0.85)
        w.set(x + np.cos(a) * rr, y + h - 1, z + np.sin(a) * rr, B(light), only_air=False)
    w.cylinder(x, z, y, y + h - 1, 1.6 if r < 8 else 2.4, B("mushroom_stem"))
    if hollow:
        w.ellipsoid(x, y + h + 1, z, r - 2, r * 0.38, r - 2, 0)
        w.cylinder(x, z, y + h, y + h, r - 2, B("spruce_planks"))


def generate():
    w = World(W, H, D, seed=55)
    X, Z = w.X, w.Z
    rng = w.rng

    # ---------------- Oberfläche ----------------
    wx = X + fbm2(X, Z, 60, 3, 1) * 16
    wz = Z + fbm2(X, Z, 60, 3, 2) * 16
    eo = np.hypot((wx - CX) / 158, (wz - CZ) / 218)
    foot = eo < 1
    hs = SURF + fbm2(X, Z, 55, 4, 3) * 3 + np.maximum(0, fbm2(X, Z, 90, 3, 4)) * 7
    hs = SURF + (hs - SURF) * (1 - smoothstep(0.8, 1.0, eo))
    rock = w.strata(["stone", "andesite", "stone", "tuff", "deepslate", "stone", "andesite"], band=4, seed=8)
    w.fill_heightmap(np.where(foot, hs, -1), "grass", "dirt", 3, rock_fn=rock, bottom=np.full(hs.shape, 2.0))
    # tiefer unten Tiefenschiefer
    for y in range(2, 40):
        layer = w.b[y]
        m = np.isin(layer, [B("stone"), B("andesite"), B("tuff")]) & (rng.random(layer.shape) < (40 - y) / 30)
        layer[m] = B("deepslate")

    # ---------------- Höhle ----------------
    ex = np.hypot((wx - CX) / 140, (wz - CZ) / 192) + fbm2(X, Z, 30, 3, 5) * 0.1
    cave = ex < 1
    floor = 16 + fbm2(X, Z, 40, 4, 6) * 5 + 14 * smoothstep(0.65, 1.0, ex)
    ceil = 34 + 60 * np.clip(1 - ex ** 2, 0, 1) + fbm2(X, Z, 28, 4, 7) * 9
    ceil = np.minimum(ceil, SURF - 16)
    ld = np.hypot((X - 176) / 58, (Z - 292) / 46) + fbm2(X, Z, 15, 2, 8) * 0.12
    lake = ld < 1
    floor = np.where(ld < 1.25, np.minimum(floor, WATER - 1 - 8 * smoothstep(1.0, 0.3, ld)
                                           + smoothstep(1.0, 1.25, ld) * 6), floor)
    il = np.hypot(X - 182, Z - 296)
    floor = np.where(il < 11, np.maximum(floor, WATER + 2 + (11 - il) * 0.25), floor)
    open_ = cave & (ceil - floor > 5)
    zz, xx = np.nonzero(open_)
    fl = np.floor(floor).astype(int)
    ce = np.floor(ceil).astype(int)
    for z, x in zip(zz, xx):
        w.b[fl[z, x] + 1:ce[z, x], z, x] = 0
    # Wände aufrauen: zufällige Ausbuchtungen in Wandnähe
    edge = cave & (ex > 0.8) & (ceil - floor > 10)
    ez, exs = np.nonzero(edge[::2, ::2])
    for z, x in zip(ez * 2, exs * 2):
        if rng.random() < 0.08:
            w.ellipsoid(x, rng.uniform(floor[z, x] + 2, ceil[z, x] - 2), z, rng.uniform(4, 9), rng.uniform(3, 6),
                        rng.uniform(4, 9), 0, noise=0.3, seed=int(x + z))

    # Boden: Moos, Ton, Kies, Tropfstein
    r = rng.random(floor.shape)
    for z, x in zip(zz, xx):
        y = fl[z, x]
        if ld[z, x] < 1.05 and y < WATER:
            w.b[y, z, x] = B("sand") if r[z, x] < 0.5 else B("clay")
        elif r[z, x] < 0.72:
            w.b[y, z, x] = B("moss")
        elif r[z, x] < 0.85:
            w.b[y, z, x] = B("rooted_dirt")
        else:
            w.b[y, z, x] = B("dripstone_block")
    w.flood(WATER, region=(ld < 1.3) & cave)

    # ---------------- Säulen ----------------
    pillars = []
    for z, x in scatter_points(w, open_ & ~(ld < 1.3) & (ex < 0.75), 7, 45):
        f0, c0 = floor[z, x], ceil[z, x]
        r0 = rng.uniform(4, 8)
        mid = (f0 + c0) / 2
        half = (c0 - f0) / 2
        for y in range(int(f0), int(c0) + 2):
            t = (y - mid) / half
            rad = r0 * (0.55 + 0.75 * t * t)
            w.cylinder(x, z, y, y, rad, B("dripstone_block") if (y // 3) % 3 == 0 else B("stone"))
        pillars.append((x, z))

    # ---------------- Tropfsteine, Leuchtbeeren, Kristalle ----------------
    for z, x in scatter_points(w, open_ & (ceil - floor > 14), 380, 5):
        c0 = int(ceil[z, x])
        if w.b[c0 - 1, z, x] != 0:
            continue
        L = int(rng.integers(3, 16))
        rad = rng.uniform(1.0, 3.2)
        for k in range(L):
            w.cylinder(x, z, c0 - 1 - k, c0 - 1 - k, rad * (1 - k / L) + 0.3, B("dripstone_block"), only_air=True)
    for z, x in scatter_points(w, open_ & ~(ld < 1.1), 200, 6):
        f0 = int(floor[z, x])
        L = int(rng.integers(2, 9))
        rad = rng.uniform(0.8, 2.2)
        for k in range(L):
            w.cylinder(x, z, f0 + 1 + k, f0 + 1 + k, rad * (1 - k / L) + 0.3, B("dripstone_block"), only_air=True)
    for z, x in scatter_points(w, open_, 900, 3):
        c0 = int(ceil[z, x])
        L = int(rng.integers(3, 22))
        for k in range(L):
            if w.get(x, c0 - 1 - k, z) != 0:
                break
            w.set(x, c0 - 1 - k, z, B("cave_vines"))
    lights = ["ochre_froglight", "verdant_froglight", "pearlescent_froglight", "amethyst"]
    for z, x in scatter_points(w, open_, 520, 4):
        c0 = int(ceil[z, x])
        w.set(x, c0, z, B(lights[int(rng.integers(0, 4))]))
    for z, x in scatter_points(w, open_ & ~(ld < 1.1), 260, 5):
        w.set(x, int(floor[z, x]), z, B(lights[int(rng.integers(0, 3))]))

    # ---------------- Riesenpilze ----------------
    caps = [("warped_wart", "verdant_froglight"), ("red_mushroom_block", "shroomlight"),
            ("brown_mushroom_block", "ochre_froglight")]
    shrooms = []
    for i, (z, x) in enumerate(scatter_points(w, open_ & ~(ld < 1.3) & (ex < 0.8) & (ceil - floor > 34), 14, 34)):
        if any(np.hypot(x - px, z - pz) < 16 for px, pz in pillars):
            continue
        hgt = int(min(ceil[z, x] - floor[z, x] - 12, rng.uniform(14, 30)))
        rad = rng.uniform(6, 12)
        cap, light = caps[i % 3]
        mushroom(w, x, int(floor[z, x]) + 1, z, hgt, rad, cap=cap, light=light)
        shrooms.append((x, int(floor[z, x]) + 1 + hgt, z))
    # Insel-Pilz im See (unter dem Lichtschacht)
    fi = int(floor[296, 182])
    mushroom(w, 182, fi + 1, 296, 24, 11, cap="warped_wart", light="verdant_froglight")
    for z, x in scatter_points(w, open_ & ~(ld < 1.15), 260, 5):
        f0 = int(floor[z, x])
        if w.b[f0, z, x] == B("moss"):
            bush(w, x, f0 + 1, z, leaf="azalea_leaves" if rng.random() < 0.5 else "flowering_azalea_leaves",
                 r=rng.uniform(1.0, 2.0))

    # ---------------- Lichtschacht ----------------
    for y in range(int(ceil[296, 182]) - 4, H):
        rad = 6.5 + fbm2(np.array(y / 6.0), np.array(1.0), 3) * 1.5
        w.cylinder(182, 296, y, y, rad, 0)
    for k in range(40):
        a = rng.uniform(0, 2 * np.pi)
        y = int(rng.uniform(ceil[296, 182], SURF))
        p = (182 + np.cos(a) * 7.5, y, 296 + np.sin(a) * 7.5)
        w.set(*p, B("azalea_leaves") if rng.random() < 0.6 else B("moss"))

    # ---------------- Amethyst-Geode (Verzauberung) ----------------
    gx, gy, gz = 44, 46, 190
    w.ellipsoid(gx, gy, gz, 15, 13, 15, B("smooth_basalt"), noise=0.08, seed=3)
    w.ellipsoid(gx, gy, gz, 13.5, 11.5, 13.5, B("calcite"), noise=0.08, seed=3)
    w.ellipsoid(gx, gy, gz, 12, 10, 12, B("amethyst"), noise=0.08, seed=3)
    w.ellipsoid(gx, gy, gz, 10.5, 8.5, 10.5, 0, noise=0.1, seed=4)
    w.cylinder(gx, gz, gy - 8, gy - 8, 7, B("amethyst"))
    for a in np.linspace(0, 2 * np.pi, 18, endpoint=False):
        w.set(gx + np.cos(a) * 4, gy - 7, gz + np.sin(a) * 4, B("bookshelf"))
        w.set(gx + np.cos(a) * 4, gy - 6, gz + np.sin(a) * 4, B("bookshelf"))
    fx = w.face_pos(gz, gy - 6, gx + 16, +1, axis="x")
    w.box(gx + 8, gy - 7, gz - 2, (fx or gx + 30) + 2, gy - 3, gz + 2, 0)
    w.box(gx + 8, gy - 8, gz - 2, (fx or gx + 30) + 2, gy - 8, gz + 2, B("polished_andesite"))

    # ---------------- Wohnbereich in der Nordwand ----------------
    wy = 46
    fz = w.face_pos(CX, wy + 4, CZ, -1, "z")
    carve_room(w, CX - 16, wy, fz - 22, CX + 16, wy + 10, fz - 4, floor="spruce_planks", light="lantern",
               round_=False)
    w.box(CX - 16, wy + 5, fz - 22, CX + 16, wy + 5, fz - 4, B("spruce_planks"))
    w.box(CX - 15, wy + 5, fz - 21, CX - 12, wy + 5, fz - 18, 0)
    w.box(CX - 14, wy, fz - 4, CX + 14, wy + 9, fz + 2, 0)
    w.box(CX - 14, wy, fz - 1, CX + 14, wy + 9, fz - 1, B("glass"))
    w.box(CX - 1, wy, fz - 1, CX + 1, wy + 2, fz - 1, 0)
    w.box(CX - 12, wy - 1, fz - 1, CX + 12, wy - 1, fz + 8, B("spruce_planks"))
    for x in range(CX - 12, CX + 13):
        w.set(x, wy, fz + 8, B("spruce_fence"))
    for z in range(fz - 1, fz + 9):
        w.set(CX - 12, wy, z, B("spruce_fence"))
        w.set(CX + 12, wy, z, B("spruce_fence"))
    for (x, z) in ((CX - 12, fz + 8), (CX + 12, fz + 8)):
        for y in range(5, wy):
            if w.b[y, z, x] == 0:
                w.b[y, z, x] = B("dark_oak_log")
        w.set(x, wy + 1, z, B("lantern"))
    w.box(CX - 16, wy, fz - 22, CX - 16, wy + 3, fz - 4, B("bookshelf"))
    wohn = (CX, wy + 1, fz - 12)

    # ---------------- Lager in der Westwand ----------------
    ly = int(floor[230, 60]) + 1 if open_[230, 60] else 22
    fxl = w.face_pos(230, ly + 3, CX, -1, "x")
    carve_room(w, fxl - 30, ly, 214, fxl - 3, ly + 9, 246, floor="spruce_planks", light="lantern")
    w.box(fxl - 4, ly, 227, fxl + 2, ly + 5, 233, 0)
    for z in range(216, 245, 3):
        w.box(fxl - 27, ly, z, fxl - 8, ly + 2, z, B("barrel"))
    lager = (fxl - 16, ly + 1, 230)

    # ---------------- Farm-Höhlen in der Ostwand ----------------
    farms = []
    for k, z0 in enumerate((150, 186, 222)):
        fy = 26
        fxe = w.face_pos(z0 + 12, fy + 4, CX, +1, "x")
        if fxe is None:
            continue
        carve_room(w, fxe + 3, fy, z0, fxe + 28, fy + 15, z0 + 24, floor="stone_bricks", light="lantern",
                   round_=False)
        w.box(fxe - 1, fy, z0 + 10, fxe + 3, fy + 4, z0 + 14, 0)
        farms.append((fxe + 15, fy + 1, z0 + 12))

    # ---------------- Pilz-Werkstatt ----------------
    mx, mz = 104, 300
    if open_[mz, mx]:
        mf = int(floor[mz, mx]) + 1
        mushroom(w, mx, mf, mz, 22, 13, cap="red_mushroom_block", light="shroomlight", hollow=True)
        for i, blk in enumerate(["crafting_table", "smithing_table", "anvil", "blast_furnace", "barrel"]):
            w.set(mx - 4 + i * 2, mf + 23, mz - 4, B(blk))
        for y in range(mf, mf + 22):
            w.set(mx + 3, y, mz, B("stripped_spruce_log"))
        werk = (mx, mf + 23, mz)
    else:
        werk = (mx, 40, mz)

    # ---------------- Steinbrücke über den See + Steg ----------------
    arch(w, (126, WATER - 3, 300), (232, WATER - 3, 284), height=20, thick=3.2, blk="stone")
    retexture(w, 120, WATER - 6, 270, 240, WATER + 30, 315, ["stone"], [("dripstone_block", 0.3), ("tuff", 0.15)])
    w.box(150, WATER + 1, 248, 156, WATER + 1, 262, B("spruce_planks"))
    for z in range(248, 263, 4):
        for x in (150, 156):
            w.set(x, WATER + 2, z, B("spruce_fence"))
            w.set(x, WATER + 3, z, B("lantern")) if z == 260 else None

    # ---------------- Eingang: Wendelschacht von der Wiese ----------------
    sx, sz = 92, 92
    top_s = int(w.column_top()[sz, sx])
    bottom = 22
    for y in range(bottom, top_s + 6):
        w.cylinder(sx, sz, y, y, 4.5, 0)
    for y in range(bottom - 1, top_s + 1):
        a = (y - bottom) * 0.42
        for rr in np.arange(1.5, 4.6, 0.5):
            for da in (0, 0.25, 0.5):
                w.set(sx + np.cos(a + da) * rr, y, sz + np.sin(a + da) * rr, B("spruce_planks"))
        if y % 6 == 0:
            w.set(sx + np.cos(a + 1.6) * 4.3, y + 1, sz + np.sin(a + 1.6) * 4.3, B("lantern"))
    w.cylinder(sx, sz, top_s + 1, top_s + 1, 6, B("mossy_stone_bricks"))
    w.cylinder(sx, sz, top_s + 1, top_s + 1, 4.5, 0)
    for k in range(0, 60):
        p = (sx + k * 0.75, bottom, sz + k * 0.95)
        w.box(p[0] - 2, bottom, p[2] - 2, p[0] + 2, bottom + 4, p[2] + 2, 0)
        w.box(p[0] - 2, bottom - 1, p[2] - 2, p[0] + 2, bottom - 1, p[2] + 2, B("spruce_planks"))
        if k % 8 == 0:
            w.set(p[0] + 2, bottom, p[2], B("lantern"))
        if open_[int(p[2]), int(p[0])] and k > 10:
            break

    # ---------------- Shop an der Oberfläche ----------------
    shx, shz = 120, 70
    sy = int(w.column_top()[shz, shx]) + 1
    w.box(shx - 14, sy - 1, shz - 9, shx + 14, sy - 1, shz + 9, B("stone_bricks"))
    retexture(w, shx - 14, sy - 1, shz - 9, shx + 14, sy - 1, shz + 9, ["stone_bricks"], [("mossy_stone_bricks", 0.3)])
    w.box(shx - 14, sy, shz - 9, shx + 14, sy + 12, shz + 9, 0)
    for x in range(shx - 12, shx + 13, 6):
        w.box(x, sy, shz - 6, x + 2, sy, shz - 6, B("barrel"))
        w.set(x + 1, sy + 1, shz - 6, B("lantern"))

    # Oberfläche: ein paar Bäume, damit es von oben normal aussieht
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    gr = (gb == B("grass")) & foot & (np.hypot(X - 182, Z - 296) > 14) & (np.hypot(X - sx, Z - sz) > 9)
    for z, x in scatter_points(w, gr, 120, 14):
        if rng.random() < 0.5:
            tree_round(w, x, top[z, x] + 1, z)
        else:
            tree_spruce(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, gr, 160, 6):
        bush(w, x, top[z, x] + 1, z)

    zones = [
        dict(name="Wendelschacht (Eingang)", typ="eingang", pos=(sx, top_s + 1, sz),
             text="Auf der Wiese liegt nur ein bemooster Steinring. Darin führt eine Wendeltreppe 90 Blöcke "
                  "in die Tiefe, dann geht ein Gang mit Laternen in die Höhle."),
        dict(name="Shop an der Oberfläche", typ="shop", pos=(shx, sy, shz),
             text="Ein kleiner Marktplatz neben dem Schacht. Besucher handeln hier oben und ahnen nicht, was "
                  "darunter liegt."),
        dict(name="Lichtschacht und Pilzinsel", typ="highlight", pos=(182, WATER + 4, 296),
             text="Ein 13 Blöcke breiter Schacht lässt Tageslicht auf die Insel im See fallen. Darauf steht ein "
                  "türkiser Riesenpilz mit grünen Froschlichtern."),
        dict(name="Wohnbereich mit Höhlenbalkon", typ="wohnen", innen=True, pos=wohn, cut=8,
             text="Zwei Stockwerke in der Nordwand mit Glasfront und einem Balkon auf Stelzen. Man blickt über "
                  "die ganze leuchtende Höhle."),
        dict(name="Lager", typ="lager", innen=True, pos=lager, cut=8,
             text="Eine gewölbte Halle (27 × 32) in der Westwand mit zehn Regalreihen aus Fässern."),
        dict(name="Farm-Höhlen", typ="farm", innen=True, pos=farms[1] if len(farms) > 1 else (250, 26, 200), cut=12,
             text="Drei 15 Blöcke hohe Kammern in der Ostwand, gut geeignet für Eisen-, Mob- und Tierfarmen. "
                  "Höhlen eignen sich besonders für Mobfarmen."),
        dict(name="Pilz-Werkstatt", typ="werkstatt", pos=werk,
             text="Ein riesiger roter Pilz mit hohlem Hut. Darin liegt die Werkstatt, und eine Leiter führt "
                  "durch den Stiel hinauf."),
        dict(name="Amethyst-Geode", typ="werkstatt", innen=True, pos=(gx, gy - 7, gz), cut=8,
             text="Eine echte Geode, außen glatter Basalt, dann Calcit, innen Amethyst. Ein Ring aus "
                  "Bücherregalen macht sie zum Verzauberungsraum."),
        dict(name="Steinbrücke über den See", typ="highlight", pos=(179, WATER + 17, 292),
             text="Ein natürlicher Bogen aus Tropfstein spannt sich über den unterirdischen See. Am Ufer liegt "
                  "ein Bootssteg."),
    ]
    info = dict(
        slug=SLUG, nr=5, title="Die leuchtende Unterwelt",
        tagline="Oben eine normale Wiese, darunter eine riesige leuchtende Höhle.",
        story=[
            "Von oben sieht alles normal aus: Wiese, ein paar Bäume, ein bemooster Steinring. Darin führt eine "
            "Wendeltreppe 90 Blöcke tief in eine Höhle von 280 × 390 Blöcken, die bis zu 75 Blöcke hoch ist.",
            "Unten leuchtet alles: Riesenpilze mit Pilzlicht, Hunderte Leuchtbeeren-Ranken, Froschlichter in "
            "der Decke, Tropfsteinsäulen und ein unterirdischer See. Ein Lichtschacht lässt Tageslicht auf die "
            "Insel fallen.",
            "Die Base ist in die Höhlenwände gebaut, dazu kommen eine Werkstatt im Pilzhut und eine Amethyst-Geode "
            "als Verzauberungsraum.",
        ],
        ground_y=SURF, water_level=WATER, paste_y=63 - SURF,
        paste_note="Dann liegt die Wiese auf Y 63, und der Höhlensee liegt auf Y {water_world}.",
        water_color="#2a9fc0", sky_color="#a6c8e2", ao=0.55,
        surround=dict(kind="grass", color="#6a9a3e"),
        camera=dict(target=(CX, 24, CZ + 20), pos=(CX + 150, 190, CZ + 260)),
        clip=58,
        zones=zones,
        phasen=[
            ("Höhle ausheben", "Mit Effizienz-V-Spitzhacke, Eile II und Beacon die Höhle von oben nach unten "
                               "aushöhlen. Die Decke als Gewölbe stehen lassen, mindestens 15 Blöcke dick."),
            ("Säulen und Tropfsteine", "Sieben Säulen stützen die Decke. Danach Hunderte Tropfsteine an "
                                       "Decke und Boden setzen."),
            ("See", "Den See ausheben und mit Wasser füllen. Danach Insel und Lichtschacht bauen."),
            ("Licht", "Froschlichter und Amethyst in die Decke einsetzen und Leuchtbeeren-Ranken (Höhlenranken) "
                      "hängen lassen."),
            ("Base", "Wohnbereich, Lager, Farm-Höhlen, Pilz-Werkstatt und Geode bauen."),
            ("Eingang tarnen", "Den Wendelschacht und den Shop oben bauen. Die Wiese darüber bleibt fast "
                               "unberührt."),
        ],
        tipps=[
            "Diese Landschaft liegt komplett unter der Erde. Sie lässt sich überall bauen, ohne die Oberfläche "
            "zu verändern.",
            "Moosblöcke mit Knochenmehl lassen den Boden schnell zuwachsen, Höhlenranken tragen Leuchtbeeren.",
            "Für Mobfarmen ist eine Höhle ideal, aber die Haupthöhle hell halten (Lichtlevel über 0), sonst "
            "spawnen dort Monster.",
        ],
    )
    return w, info
