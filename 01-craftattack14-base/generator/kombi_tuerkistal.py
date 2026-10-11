"""Kombination 7: Das Türkis-Tal (Tal + türkiser See + Inseln).

Ein Tal mit Bergring wie das versteckte Tal, aber der Talboden ist ein großer türkiser See mit hellem
Sandgrund. Im See liegen Inseln, darüber schweben weitere. Rein kommt man durch den Tunnel hinter dem
Wasserfall.
"""
import numpy as np

from mclib import (B, OCCLUDES, World, bridge, bush, carve_room, fbm2, float_island, lake_bed, leaf_blob,
                   paint_path, polyline_dist, retexture, ring_valley, scatter_points, smooth_polyline, smoothstep,
                   surface_layers, tree_cherry, tree_palm, tree_round, tree_spruce, vine_curtain)

W, H, D = 330, 196, 540
CX, CZ, RX, RZ = 165, 268, 98, 220
FLOOR = 56
LAKE = 53
GROUND = 58
SLUG = "tuerkis-tal"


def fall_into(w, x0, x1, z0, z1, y_top):
    """Wasserfall von einer schwebenden Insel: senkrecht nach unten, bis er Wasser oder Boden trifft."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(int(y_top), 0, -1):
                b = w.b[y, z, x]
                if b == 0:
                    w.b[y, z, x] = B("water")
                elif y < y_top - 1 and (OCCLUDES[b] or b == B("water")):
                    break


def generate():
    w = World(W, H, D, seed=77)
    X, Z = w.X, w.Z
    rng = w.rng

    floor_h = (FLOOR + fbm2(X, Z, 60, 4, 3) * 2.5 + np.maximum(0, fbm2(X, Z, 35, 3, 31)) * 5)
    h, d, s, foot, fore = ring_valley(w, CX, CZ, RX, RZ, floor_h, GROUND, peak_lo=110, peak_amp=60, gate_x=CX,
                                      seed=70)
    floor_h = floor_h + 6 * smoothstep(0.62, 0.9, d)

    # ---------------- Der türkise See ----------------
    Lf = np.maximum(d / 0.84 + fbm2(X, Z, 25, 3, 9) * 0.05, 1 + (CZ - 118 - Z + fbm2(X, Z, 20, 2, 10) * 10) / 30)
    lake = Lf < 1
    bottom = LAKE - 2 - 10 * smoothstep(1.0, 0.45, Lf) + fbm2(X, Z, 12, 2, 7) * 1.5
    shore = LAKE - 1 + smoothstep(1.0, 1.14, Lf) * (h - LAKE + 1)
    h = np.where(Lf < 1, np.minimum(h, bottom), np.where(Lf < 1.14, np.minimum(h, shore), h))

    # ---------------- Inseln im See ----------------
    def raise_island(cx, cz, rx, rz, top, seed, steep=False):
        e = np.hypot((X - cx) / rx, (Z - cz) / rz) + fbm2(X, Z, 9, 2, seed) * 0.12
        prof = smoothstep(1.0, 0.55, e) if steep else 0.65 * smoothstep(1.0, 0.8, e) + 0.35 * smoothstep(0.8, 0.2, e)
        return np.where(e < 1, np.maximum(h, LAKE - 1 + (top - LAKE + 1) * prof), h), e
    h, e_wohn = raise_island(150, 300, 36, 27, LAKE + 4, 1)
    hill = np.hypot((X - 150) / 18, (Z - 288) / 12)
    h = np.where(hill < 1, np.maximum(h, LAKE + 4 + 13 * smoothstep(1, 0.3, hill)), h)
    h, e_lager = raise_island(220, 384, 13, 12, LAKE + 36, 2, steep=True)
    h, e_farm = raise_island(108, 402, 25, 20, LAKE + 3, 3)
    islets = [(198, 222, 6), (90, 330, 5), (238, 300, 7), (170, 440, 5), (128, 240, 4), (250, 420, 5)]
    for i, (x, z, r) in enumerate(islets):
        h, _ = raise_island(x, z, r, r, LAKE + 2 + i % 3, 20 + i)

    # Bach aus dem Norden
    river = smooth_polyline([(CX, 70), (150, 100), (172, 130), (160, 152)], 10)
    rd = polyline_dist(X, Z, river)
    h = np.where((rd < 6) & (d < 0.9), np.minimum(h, LAKE - 2 + smoothstep(3, 6, rd) * (h - LAKE + 2)), h)
    pool_d = np.hypot((X - CX) / 12, (Z - 64) / 9)
    h = np.where(pool_d < 1.4, np.minimum(h, LAKE - 5 + smoothstep(0.8, 1.4, pool_d) * 9), h)

    # ---------------- Oberflächen ----------------
    surf, sub, slope, r = surface_layers(w, h, rng, snow_at=156)
    beach = (Lf >= 1) & (Lf < 1.2) & (h <= LAKE + 1.5)
    surf[beach] = B("sand")
    sub[beach] = B("sand")
    bed = (h < LAKE) & ((Lf < 1.15) | (rd < 6) | (pool_d < 1.4))
    lake_bed(surf, sub, bed, r)
    isl_beach = ((e_wohn < 1) | (e_farm < 1)) & (h <= LAKE + 1.2) & (h >= LAKE - 0.5)
    surf[isl_beach] = B("sand")
    surf[(e_lager < 1) & (h > LAKE + 3)] = 255
    rock = w.strata(["stone", "stone", "andesite", "stone", "tuff", "stone", "andesite", "andesite", "stone",
                     "tuff"], band=3, seed=9, warp=7)
    w.fill_heightmap(np.where(foot, h, -1), surf, sub, 3, rock_fn=rock, bottom=np.full(h.shape, 34.0))
    retexture(w, 0, 40, 0, W, H, D, ["stone"], [("andesite", 0.12), ("cobblestone", 0.04), ("tuff", 0.05)])
    w.flood(LAKE, region=((Lf < 1.16) | (rd < 6) | (pool_d < 1.4)) & (d < 0.95) & foot)
    top = w.column_top()
    # Lagerinsel: grüne Kappe oben
    zz, xx = np.nonzero((e_lager < 0.7) & (h > LAKE + 30))
    for z, x in zip(zz, xx):
        w.b[top[z, x], z, x] = B("grass")

    # ---------------- Wasserfälle ----------------
    w.face_water(CX - 6, CX + 6, 132, LAKE - 4, 110, -1, axis="z", depth=2)            # Nordwand -> Gumpe
    w.face_water(250, 258, 118, LAKE, 120, -1, axis="x", depth=2)                      # Westwand
    w.face_water(330, 337, 112, LAKE, 210, +1, axis="x", depth=2)                      # Ostwand
    w.face_water(190, 192, 104, LAKE, 210, +1, axis="x", depth=1)                      # Schleierfall Ost
    w.face_water(CX - 9, CX + 9, 130, GROUND, D - 1, -1, axis="z", depth=2)           # Außen vor dem Tunnel
    tf = w.face_pos(CX, GROUND + 4, D - 1, -1, "z")

    # ---------------- Tunnel + Shop ----------------
    tz0, tz1 = 470, tf + 1
    w.box(CX - 4, GROUND, tz0, CX + 4, GROUND + 8, tz1, 0)
    w.box(CX - 3, GROUND + 9, tz0, CX + 3, GROUND + 9, tz1, 0)
    w.box(CX - 4, GROUND - 1, tz0, CX + 4, GROUND - 1, tz1, B("stone_bricks"))
    retexture(w, CX - 4, GROUND - 1, tz0, CX + 4, GROUND - 1, tz1, ["stone_bricks"], [("mossy_stone_bricks", 0.35)])
    for z in range(tz0 + 4, tz1 - 2, 8):
        w.set(CX - 4, GROUND, z, B("lantern"))
        w.set(CX + 4, GROUND, z, B("lantern"))
    w.box(CX - 10, GROUND, tz0 - 16, CX + 10, GROUND + 18, tz0, 0)
    w.box(CX - 10, GROUND - 1, tz0 - 16, CX + 10, GROUND - 1, tz0, B("dirt_path"))
    pz0, pz1 = tf + 3, tf + 14
    w.box(CX - 40, GROUND - 1, pz0, CX - 14, GROUND - 1, pz1, B("stone_bricks"))
    w.box(CX - 40, GROUND, pz0, CX - 14, GROUND + 14, pz1, 0)
    for x in range(CX - 38, CX - 15, 6):
        w.box(x, GROUND, pz0 + 2, x + 2, GROUND, pz0 + 2, B("barrel"))
        w.set(x + 1, GROUND + 1, pz0 + 2, B("lantern"))
    pool_out = np.hypot(X - CX, Z - (tf + 8)) < 6.5
    for z, x in zip(*np.nonzero(pool_out)):
        for y in range(GROUND - 4, GROUND):
            w.set(x, y, z, B("water"))
        w.set(x, GROUND - 5, z, B("calcite"))
    shop = (CX - 27, GROUND, (pz0 + pz1) // 2)

    # ---------------- Wohnbereich im Inselhügel ----------------
    hy = LAKE + 5
    carve_room(w, 138, hy, 278, 162, hy + 9, 296, floor="spruce_planks", light="lantern", round_=True)
    zf = 296
    while zf < 320 and OCCLUDES[w.b[hy + 4, zf, 150]]:
        zf += 1
    w.box(140, hy, 296, 160, hy + 7, zf, 0)
    w.box(140, hy, zf - 1, 160, hy + 7, zf - 1, B("glass"))
    w.box(149, hy, zf - 1, 151, hy + 3, zf - 1, 0)
    w.box(138, hy - 1, zf - 1, 162, hy - 1, zf + 8, B("spruce_planks"))
    for x in range(138, 163):
        w.set(x, hy, zf + 8, B("spruce_fence"))
    w.box(138, hy, 278, 138, hy + 3, 294, B("bookshelf"))
    wohn = (150, hy + 1, 287)
    # Steg vom Inselstrand in den See
    w.box(148, LAKE + 1, zf + 9, 152, LAKE + 1, zf + 30, B("spruce_planks"))
    for z in range(zf + 9, zf + 31, 5):
        for x in (148, 152):
            for y in range(LAKE - 8, LAKE + 1):
                if not OCCLUDES[w.b[y, z, x]]:
                    w.b[y, z, x] = B("spruce_log")
    w.set(148, LAKE + 2, zf + 30, B("lantern"))
    w.set(152, LAKE + 2, zf + 30, B("lantern"))

    # ---------------- Lager im Felsturm ----------------
    ly = LAKE + 2
    w.ellipsoid(220, ly + 5, 384, 8, 6, 8, 0)
    w.box(212, ly - 1, 376, 228, ly - 1, 392, B("spruce_planks"), replace=[0] + [B(k) for k in
          ("stone", "andesite", "tuff", "calcite", "diorite", "cobblestone", "dirt", "sand")])
    w.cylinder(220, 384, ly - 1, ly - 1, 8, B("spruce_planks"))
    for a in np.linspace(0, 2 * np.pi, 14, endpoint=False):
        for k in range(3):
            w.set(220 + np.cos(a) * 7, ly + k, 384 + np.sin(a) * 7, B("barrel"))
    w.box(206, ly, 382, 214, ly + 4, 386, 0)
    w.box(204, ly - 1, 382, 214, ly - 1, 386, B("spruce_planks"))
    for y in range(ly, LAKE + 37):
        a = (y - ly) * 0.5
        w.set(220 + np.cos(a) * 3, y, 384 + np.sin(a) * 3, B("spruce_planks"))
        w.set(220, y, 384, B("stripped_spruce_log"))
    lager = (220, ly + 1, 384)

    # ---------------- Werkstatt in der Westwand ----------------
    fxw = w.face_pos(200, LAKE + 4, CX, -1, "x")
    carve_room(w, fxw - 20, LAKE + 3, 188, fxw - 3, LAKE + 11, 212, floor="stone_bricks", light="lantern")
    w.box(fxw - 3, LAKE + 3, 196, fxw + 1, LAKE + 8, 204, 0)
    w.box(fxw - 3, LAKE + 2, 194, fxw + 10, LAKE + 2, 206, B("spruce_planks"))
    for i, blk in enumerate(["crafting_table", "smithing_table", "anvil", "blast_furnace", "blast_furnace", "barrel"]):
        w.set(fxw - 18, LAKE + 3, 192 + i * 3, B(blk))
    werk = (fxw - 11, LAKE + 4, 200)

    # ---------------- Farminsel + Farmhöhle ----------------
    top = w.column_top()
    for z in range(388, 416):
        for x in range(92, 126):
            t = top[z, x]
            if w.b[t, z, x] == B("grass") and t >= LAKE + 1:
                if (x - 92) % 7 == 3:
                    w.b[t, z, x] = B("water")
                else:
                    w.b[t, z, x] = B("farmland")
                    w.set(x, t + 1, z, B("wheat"))
    farm = (108, LAKE + 4, 402)
    fxe = w.face_pos(160, LAKE + 6, CX, +1, "x")
    carve_room(w, fxe + 3, LAKE + 3, 146, fxe + 26, LAKE + 18, 174, floor="stone_bricks", light="lantern",
               round_=False)
    w.box(fxe - 1, LAKE + 3, 158, fxe + 3, LAKE + 7, 162, 0)
    farm2 = (fxe + 14, LAKE + 4, 160)

    # ---------------- Schwebende Inseln über dem See ----------------
    float_island(w, 202, LAKE + 72, 248, 17, 14, 24, seed=91)
    float_island(w, 126, LAKE + 96, 198, 10, 10, 16, seed=92)
    float_island(w, 178, LAKE + 56, 432, 22, 18, 28, seed=93)
    float_island(w, 252, LAKE + 84, 330, 8, 7, 12, seed=94)
    top = w.column_top()
    # Verzauberung oben
    vy = int(top[248, 202]) + 1
    for a in np.linspace(0, 2 * np.pi, 22, endpoint=False):
        if np.cos(a) < -0.85:
            continue
        w.set(202 + 4 * np.cos(a), vy, 248 + 4 * np.sin(a), B("bookshelf"))
        w.set(202 + 4 * np.cos(a), vy + 1, 248 + 4 * np.sin(a), B("bookshelf"))
    w.set(202, vy, 248, B("lantern"))
    tree_cherry(w, 210, int(top[254, 210]) + 1, 254)
    zauber = (202, vy, 248)
    # Blasen-Aufzug von der Wohninsel zur Verzauberungsinsel
    ex, ez = 196, 262
    base_y = int(top[ez, ex])
    w.set(ex, base_y, ez, B("soul_sand"))
    yb = base_y + 1
    while yb < vy and not OCCLUDES[w.b[yb, ez, ex]]:
        yb += 1
    for y in range(base_y + 1, vy + 1):
        w.b[y, ez, ex] = B("water")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if y > yb + 2 or not OCCLUDES[w.b[y, ez + dz, ex + dx]]:
                w.set(ex + dx, y, ez + dz, B("glass"))
    w.set(ex + 1, vy, ez, 0)
    w.set(ex + 1, vy + 1, ez, 0)
    # Wasserfallinsel: kleiner See oben, Abfluss stürzt in den großen See
    fy = int(top[432, 178])
    for z, x in zip(*np.nonzero(np.hypot(X - 178, Z - 432) < 7)):
        w.b[fy - 2:fy + 1, z, x] = B("water")
        w.b[fy - 3, z, x] = B("calcite")
    for x in range(178, 210):
        if w.b[fy - 1, 432, x] == 0 and not OCCLUDES[w.b[fy - 2, 432, x]]:
            fall_into(w, x, x + 1, 430, 434, fy)
            break
        w.b[fy - 1:fy + 1, 430:435, x] = B("water")
    # Aussicht ganz oben
    ay = int(top[198, 126]) + 1
    w.box(122, ay, 194, 130, ay, 202, B("spruce_planks"))
    for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        w.set(126 + dx, ay + 1, 198 + dz, B("spruce_fence"))
        w.set(126 + dx, ay + 2, 198 + dz, B("lantern"))
    aus = (126, ay, 198)
    # Ketten unter den schwebenden Inseln
    for (x, z) in ((202, 248), (178, 432), (126, 198)):
        col = OCCLUDES[w.b[:, z + 3, x + 2]]
        if col.any():
            yb2 = int(np.argmax(col))
            for y in range(yb2 - 1, yb2 - 18, -1):
                w.set(x + 2, y, z + 3, B("chain"), only_air=True)
            w.set(x + 2, yb2 - 18, z + 3, B("lantern"), only_air=True)
        vine_curtain(w, x, z, int(w.column_top()[z, x]) - 2, 14, rng.uniform(0, 6.28), leaf="azalea_leaves")

    # ---------------- Brücken ----------------
    top = w.column_top()

    def tp(x, z):
        return (x, int(top[z, x]) + 1, z)
    bridge(w, tp(150, 262), tp(150, 208), sag=4)                 # Nordufer -> Wohninsel
    bridge(w, tp(126, 312), tp(112, 384), sag=4)                 # Wohninsel -> Farminsel
    bridge(w, tp(176, 314), (206, ly, 384), sag=4)                # Wohninsel -> Lagerturm
    bridge(w, (220, LAKE + 37, 380), tp(186, 432), sag=7)        # Lagerturm oben -> Wasserfallinsel

    # ---------------- Vegetation ----------------
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    grass = (gb == B("grass")) | (gb == B("moss"))
    valley = (d < 0.86) & grass & (rd > 7)
    north = valley & (Z < CZ - 130) & (pool_d > 1.6)
    for z, x in scatter_points(w, north, 60, 7):
        tree_spruce(w, x, top[z, x] + 1, z, h=int(rng.integers(12, 20)))
    meadow = valley & (Z >= CZ - 130) & (Lf > 1.15)
    for z, x in scatter_points(w, meadow, 30, 10):
        tree_cherry(w, x, top[z, x] + 1, z)
    isl = grass & ((e_wohn < 0.95) | (e_farm < 0.6)) & (hill > 1.2)
    for z, x in scatter_points(w, isl, 14, 9):
        tree_cherry(w, x, top[z, x] + 1, z) if rng.random() < 0.6 else tree_round(
            w, x, top[z, x] + 1, z, log="birch_log", leaf="birch_leaves")
    sandy = (gb == B("sand")) & (top >= LAKE) & (d < 0.9)
    for z, x in scatter_points(w, sandy, 24, 14):
        tree_palm(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, valley, 160, 5):
        bush(w, x, top[z, x] + 1, z, leaf="flowering_azalea_leaves" if rng.random() < 0.5 else "azalea_leaves")
    outside = (d > 1.05) & grass & (slope < 1.2) & ~fore & foot
    for z, x in scatter_points(w, outside, 240, 6):
        tree_spruce(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, (d > 0.9) & (d < 1.0) & grass, 50, 8):
        bush(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, grass & (e_lager < 0.6), 1, 3):
        tree_round(w, x, top[z, x] + 1, z, log="dark_oak_log", leaf="azalea_leaves", r=3)
    paint_path(w, smooth_polyline([(CX, tz0 - 4), (200, 450), (236, 400), (240, 330), (220, 250), (190, 200),
                                   (170, 160), (CX, 90)], 8), width=1.4, lanterns=16)

    zones = [
        dict(name="Geheimer Eingang", typ="eingang", pos=(CX, GROUND + 3, tf + 2),
             text=f"Hinter einem 72 Blöcke hohen Wasserfall an der Außenwand beginnt ein {tz1 - tz0} Blöcke "
                  "langer Tunnel. Am Ende öffnet sich der Blick auf den türkisen See."),
        dict(name="Shop-Platz", typ="shop", pos=shop,
             text="Ein Marktplatz vor dem Wasserfall. Besucher handeln hier draußen und sehen den See nicht."),
        dict(name="Türkiser See", typ="highlight", pos=(CX + 20, LAKE + 1, 340),
             text="Der See füllt fast das ganze Tal, rund 160 × 300 Blöcke. Durch den hellen Grund aus weißem "
                  "Sand und Calcit leuchtet er türkis. Am Rand ist er nur 2–4 Blöcke tief, in der Mitte bis 12."),
        dict(name="Wohninsel", typ="wohnen", innen=True, pos=wohn, cut=8,
             text="Die größte Insel im See. Im Hügel liegt eine gewölbte Wohnhöhle mit Glasfront zum See und "
                  "einer Terrasse. Davor führt ein Steg aufs Wasser."),
        dict(name="Lager im Felsturm", typ="lager", innen=True, pos=lager, cut=8,
             text="Ein 36 Blöcke hoher Felsturm im See. Unten liegt eine runde Lagerhalle mit Fässern rundum, "
                  "eine Wendeltreppe führt nach oben."),
        dict(name="Farminsel", typ="farm", pos=farm,
             text="Eine flache Insel voller Weizenfelder mit Wasserrinnen. Eine Hängebrücke führt zur Wohninsel."),
        dict(name="Farmhöhle", typ="farm", innen=True, pos=farm2, cut=12,
             text="Eine 16 Blöcke hohe Halle in der Ostwand für Eisen- oder Mobfarm."),
        dict(name="Werkstatt am Ufer", typ="werkstatt", innen=True, pos=werk, cut=7,
             text="Eine Höhle in der Westwand direkt am Wasser, mit Holzsteg davor."),
        dict(name="Verzauberungsinsel", typ="werkstatt", pos=zauber,
             text="Sie schwebt 72 Blöcke über dem See. Ein gläserner Blasen-Aufzug fährt von der Wohninsel hinauf."),
        dict(name="Wasserfallinsel", typ="highlight", pos=(178, LAKE + 58, 432),
             text="Eine schwebende Insel mit eigenem kleinen See. Sein Abfluss stürzt über die Kante in den "
                  "großen See. Eine lange Hängebrücke kommt vom Felsturm herauf."),
        dict(name="Aussichtsinsel", typ="highlight", pos=aus,
             text="Die höchste schwebende Insel, fast 100 Blöcke über dem Wasser."),
    ]
    info = dict(
        slug=SLUG, nr=7, title="Das Türkis-Tal",
        tagline="Ein verstecktes Tal mit türkisem See, Inseln darin und Inseln darüber.",
        story=[
            "Kombination aus verstecktem Tal, türkisem See und schwebenden Inseln. Von außen sieht man nur "
            "Berge. Durch einen Tunnel hinter dem Wasserfall kommt man hinein.",
            "Drinnen füllt ein türkiser See fast das ganze Tal. Im Wasser liegen eine große Wohninsel, eine "
            "Farminsel, ein Felsturm mit dem Lager und kleine Palmeninseln. Darüber schweben vier Inseln, von "
            "einer stürzt ein Wasserfall in den See.",
            "Hängebrücken, Stege und ein gläserner Blasen-Aufzug verbinden alles. Im Norden liegen eine "
            "Kirschwiese und ein Fichtenwald, von den Wänden fallen Wasserfälle.",
        ],
        ground_y=GROUND, water_level=LAKE, paste_y=63 - GROUND,
        paste_note="Dann liegt der Boden rund um die Berge auf Y 63 und der Seespiegel auf Y {water_world}.",
        water_color="#38cfe0", sky_color="#a7d2ec",
        camera=dict(target=(CX, 52, 310), pos=(CX + 70, 290, 560)),
        clip=None,
        zones=zones,
        phasen=[
            ("Abstecken", "Talumriss, Seeufer, Inseln und Tunnel mit Wolle markieren."),
            ("Berge", "Den Bergring hochziehen: innen steil, außen flacher, oben Schnee."),
            ("See ausheben", "Den See flach ausheben (am Rand 2–4 tief, Mitte bis 12) und den Grund mit "
                             "weißem Sand und Calcit auslegen. Das macht das Wasser türkis."),
            ("Inseln", "Wohninsel mit Hügel, Farminsel, Felsturm und Palmeninseln aufschütten. Dann die "
                       "schwebenden Inseln mit Gerüst bauen."),
            ("Wasser", "See füllen, Wasserfälle setzen, Blasen-Aufzug bauen."),
            ("Base und Natur", "Räume, Brücken, Stege, Bäume, Wege mit Laternen."),
        ],
        tipps=[
            "Richtig türkis wird Wasser in Minecraft nur in warmen Biomen. Am stärksten im warmen Ozean, "
            "hellblau im Kirschhain. Ein heller Grund (Sand, Calcit) hilft überall.",
            "Flaches Wasser über hellem Sand sieht viel türkiser aus als tiefes. Deshalb ist der See am Rand "
            "nur 2–4 Blöcke tief.",
            "Den Tunnel erst zum Schluss öffnen, damit das Tal bis zur Enthüllung geheim bleibt.",
        ],
    )
    return w, info
