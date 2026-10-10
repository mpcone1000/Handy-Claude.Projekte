"""Landschaft 1: Das versteckte Tal.

Ein Tal, rundum von bis zu 110 Blöcke hohen Felswänden eingeschlossen. Hinein kommt man nur durch einen
Tunnel, dessen Eingang hinter einem Wasserfall an der Außenwand liegt.
"""
import numpy as np

from mclib import (B, World, arch, bridge, bush, carve_room, fbm2, green_tops, paint_path, polyline_dist,
                   retexture, ridged2, scatter_points, smooth_polyline, smoothstep, tree_cherry, tree_round,
                   tree_spruce)

W, H, D = 300, 176, 600
FLOOR = 53
LAKE = 50
GROUND = 57
SLUG = "verstecktes-tal"


def generate():
    w = World(W, H, D, seed=11)
    X, Z = w.X, w.Z
    rng = w.rng

    # ---------------- Grundform ----------------
    wx = X + fbm2(X, Z, 70, 3, 1) * 14
    wz = Z + fbm2(X, Z, 70, 3, 2) * 22
    d = np.sqrt(((wx - 150) / 88) ** 2 + ((wz - 300) / 236) ** 2)

    floor_h = (FLOOR + fbm2(X, Z, 60, 4, 3) * 3.5 + 6 * smoothstep(0.62, 0.9, d)
               + np.maximum(0, fbm2(X, Z, 35, 3, 31)) * 6)

    # Abstand (in Blöcken) nach außen vom Talrand
    gdz, gdx = np.gradient(d)
    s = (d - 0.985) / np.maximum(np.hypot(gdx, gdz), 1e-4)
    sp = np.maximum(s, 0)
    peak = 112 + ridged2(X, Z, 60, 5, 4) * 62
    rid = ridged2(X, Z, 34, 4, 12)
    mtn = 62 + (peak - 62) * (0.6 * np.exp(-sp / 26) + 0.4 * rid * np.exp(-sp / 55))
    mtn = np.minimum(mtn, H - 5)

    t = smoothstep(0.885, 0.985, d + fbm2(X, Z, 22, 3, 5) * 0.022)
    tq = np.floor(t * 7) / 7
    t2 = 0.55 * t + 0.45 * tq          # kleine Stufen/Simse in der Wand
    inner = floor_h + (mtn - floor_h) * t2
    h = np.where(s <= 0, inner, mtn)

    # organischer Umriss: die Berge laufen nach außen ins normale Gelände aus, außerhalb ist nichts
    bd = np.minimum(np.minimum(X, W - 1 - X), np.minimum(Z, D - 1 - Z))
    send = 46 + fbm2(X, Z, 45, 3, 6) * 12
    gate = (1 - smoothstep(30, 50, np.abs(X - 150))) * smoothstep(440, 520, Z)
    fade = (1 - smoothstep(0.4, 1.0, sp / send)) * smoothstep(2, 12, bd)
    fade_gate = 1 - smoothstep(29, 34, sp)
    fade = fade * (1 - gate) + fade_gate * gate
    h = np.where(s > 0, GROUND + (h - GROUND) * fade, h)
    foot = ((sp < send) | ((gate > 0.5) & (sp < 50))) & (bd > 1)
    fore = (gate > 0.5) & (sp >= 33) & (sp < 50)
    h = np.where(fore, np.minimum(h, GROUND - 1), h)

    # ---------------- See ----------------
    ld = np.sqrt(((wx - 148) / 64) ** 2 + ((wz - 392) / 88) ** 2)
    lake_bot = LAKE - 2 - 12 * smoothstep(1.0, 0.25, ld) + fbm2(X, Z, 12, 2, 7) * 1.5
    shore = LAKE - 1 + smoothstep(1.0, 1.35, ld) * (h - LAKE + 1)
    h = np.where(ld < 1.0, np.minimum(h, lake_bot), np.where(ld < 1.35, np.minimum(h, shore), h))
    lake = ld < 1.0

    # Inseln
    i1 = np.hypot((X - 176) / 17, (Z - 410) / 13)
    h = np.where(i1 < 1, np.maximum(h, LAKE + 1 + 6 * smoothstep(1, 0.25, i1)), h)
    i2 = np.hypot((X - 116) / 7, (Z - 446) / 8)
    h = np.where(i2 < 1, np.maximum(h, LAKE + 1 + 11 * smoothstep(1, 0.35, i2)), h)
    i3 = np.hypot((X - 132) / 6, (Z - 352) / 6)
    h = np.where(i3 < 1, np.maximum(h, LAKE + 2 + 5 * smoothstep(1, 0.3, i3)), h)

    # ---------------- Bach, Gumpe, Terrassen ----------------
    river_pts = smooth_polyline([(150, 86), (139, 112), (158, 150), (141, 196), (157, 240), (148, 312)], 10)
    west_pts = smooth_polyline([(70, 452), (84, 446), (100, 432)], 8)
    east_pts = smooth_polyline([(224, 488), (208, 470), (194, 452)], 8)
    rd = np.minimum(polyline_dist(X, Z, river_pts), np.minimum(polyline_dist(X, Z, west_pts),
                                                                 polyline_dist(X, Z, east_pts)))
    river = (rd < 3.2) & (d < 0.9)
    h = np.where(rd < 6.5, np.minimum(h, FLOOR - 4 + smoothstep(3.2, 6.5, rd) * (h - FLOOR + 4)), h)
    pool_d = np.hypot((X - 150) / 13, (Z - 80) / 10)
    pool = pool_d < 1
    h = np.where(pool_d < 1.4, np.minimum(h, LAKE - 1 - 7 * smoothstep(1, 0.2, pool_d)
                                          + smoothstep(1.0, 1.4, pool_d) * 12), h)
    pool_e = np.hypot((X - 226) / 8, (Z - 492) / 8) < 1
    h = np.where(pool_e, np.minimum(h, LAKE - 3), h)

    terr = (X > 186) & (X < 226) & (Z > 132) & (Z < 252) & (d < 0.9)
    tier = np.clip(np.floor((X - 186) / 10), 0, 3)
    feather = smoothstep(132, 140, Z) * (1 - smoothstep(244, 252, Z))
    h_terr = FLOOR + 1 + tier * 3
    h = np.where(terr, h * (1 - feather) + h_terr * feather, h)
    terr_core = terr & (feather > 0.99)


    # ---------------- Oberflächen ----------------
    gz, gx = np.gradient(h)
    slope = np.hypot(gx, gz)
    surf = np.full(h.shape, B("grass"), np.uint8)
    sub = np.full(h.shape, B("dirt"), np.uint8)
    r = rng.random(h.shape)
    mid = (slope > 0.9) & (slope <= 1.7)
    surf[mid & (r < 0.5)] = B("moss")
    surf[mid & (r >= 0.5)] = B("coarse_dirt")
    steep = slope > 1.7
    surf[steep] = 255
    sub[steep] = 255
    snow = (h > 156 + fbm2(X, Z, 15, 2, 8) * 6) & (slope < 1.9)
    surf[snow] = B("snow")
    beach = (ld < 1.18) & (h <= LAKE + 1.5) & ~lake
    surf[beach] = B("sand")
    sub[beach] = B("sand")
    bed = (lake | river | pool | pool_e) & (h < LAKE)
    surf[bed & (r < 0.45)] = B("sand")
    surf[bed & (r >= 0.45) & (r < 0.8)] = B("gravel")
    surf[bed & (r >= 0.8)] = B("clay")
    surf[terr_core] = B("farmland")
    surf[(i2 < 1) & (h > LAKE + 3)] = 255

    rock = w.strata(["stone", "stone", "andesite", "stone", "tuff", "stone", "stone", "andesite", "stone",
                     "diorite", "stone", "andesite", "tuff", "stone"], band=3, seed=9, warp=7)
    h_fill = np.where(foot, h, -1)
    w.fill_heightmap(h_fill, surf, sub, 3, rock_fn=rock, bottom=np.full(h.shape, 28.0))
    # Felswände sprenkeln, damit die Schichten nicht zu gleichmäßig wirken
    retexture(w, 0, 40, 0, W, H, D, ["stone"], [("andesite", 0.12), ("cobblestone", 0.04), ("tuff", 0.05)])
    retexture(w, 0, 40, 0, W, H, D, ["diorite"], [("stone", 0.35), ("calcite", 0.2)])
    w.flood(LAKE, region=(lake | river | pool | pool_e | (ld < 1.02)) & (d < 0.95) & foot)

    # Terrassen: Stützmauern + Wasserrinnen + Weizen
    top = w.column_top()
    for k in range(1, 4):
        xw = 186 + 10 * k
        for z in range(140, 245):
            ylo = FLOOR + 1 + (k - 1) * 3
            for y in range(ylo - 2, ylo + 3):
                w.set(xw, y, z, B("mossy_stone_bricks") if rng.random() < 0.6 else B("stone_bricks"))
    for k in range(4):
        xc = 186 + 10 * k + 5
        y = FLOOR + 1 + k * 3
        for z in range(141, 244):
            w.set(xc, y, z, B("water"))
    zz, xx = np.nonzero(terr_core)
    for z, x in zip(zz, xx):
        y = top[z, x]
        if w.b[y, z, x] == B("farmland"):
            w.set(x, y + 1, z, B("wheat"), only_air=True)

    # ---------------- Wasserfälle ----------------
    # Hauptwasserfall im Norden (Quelle aus einer Felsspalte), dahinter das Lager
    w.face_water(144, 156, 128, LAKE - 1, 90, -1, axis="z", depth=2)
    # Westlicher Fall in den See
    w.face_water(436, 444, 112, LAKE, 100, -1, axis="x", depth=2)
    # Östlicher Fall in eine kleine Gumpe
    w.face_water(489, 495, 104, LAKE - 2, 210, +1, axis="x", depth=2)
    # Zwei schmale Schleierfälle an der Ostwand über den Terrassen
    w.face_water(300, 302, 120, FLOOR, 200, +1, axis="x", depth=1)
    w.face_water(170, 171, 98, FLOOR, 200, +1, axis="x", depth=1)
    # Außenwasserfall vor dem Tunnel (Süden)
    w.face_water(141, 159, 132, GROUND, D - 1, -1, axis="z", depth=2)
    tf = w.face_pos(150, 62, D - 1, -1, "z")

    # ---------------- Lager hinter dem Wasserfall ----------------
    fz = w.face_pos(150, 55, 90, -1, "z")
    lz1 = fz - 3
    lz0 = lz1 - 24
    carve_room(w, 132, 52, lz0, 168, 61, lz1, floor="spruce_planks", light="lantern", shelf="barrel")
    w.box(147, 52, lz1, 153, 57, fz + 1, 0)          # Durchgang hinter dem Wasservorhang
    w.box(147, 51, lz1, 153, 51, fz + 1, B("spruce_planks"))
    for x in range(134, 167, 4):                       # Regalreihen aus Fässern
        if abs(x - 150) > 3:
            w.box(x, 52, lz0 + 4, x, 54, lz1 - 4, B("barrel"))
    lager_pos = (150, 54, (lz0 + lz1) // 2)

    # ---------------- Tunnel durch die Torwand ----------------
    tz0, tz1 = 522, tf + 1
    w.box(146, GROUND, tz0, 154, GROUND + 8, tz1, 0)
    w.box(147, GROUND + 9, tz0, 153, GROUND + 9, tz1, 0)
    w.box(146, GROUND - 1, tz0, 154, GROUND - 1, tz1, B("stone_bricks"))
    retexture(w, 146, GROUND - 1, tz0, 154, GROUND - 1, tz1, ["stone_bricks"],
              [("mossy_stone_bricks", 0.35), ("cobblestone", 0.15)])
    for z in range(tz0 + 4, tz1 - 2, 8):
        w.set(146, GROUND, z, B("lantern"))
        w.set(154, GROUND, z, B("lantern"))
    # Talseite des Tunnels ebnen
    w.box(140, GROUND, tz0 - 14, 160, GROUND + 16, tz0, 0)
    w.box(140, GROUND - 1, tz0 - 14, 160, GROUND - 1, tz0, B("dirt_path"))

    # Vorplatz (Shop) neben dem Wasserfall
    pz0, pz1 = tf + 3, tf + 14
    w.box(110, GROUND - 1, pz0, 136, GROUND - 1, pz1, B("stone_bricks"))
    retexture(w, 110, GROUND - 1, pz0, 136, GROUND - 1, pz1, ["stone_bricks"], [("mossy_stone_bricks", 0.3)])
    w.box(110, GROUND, pz0, 136, GROUND + 14, pz1, 0)
    for x in range(112, 135, 6):
        w.box(x, GROUND, pz0 + 2, x + 2, GROUND, pz0 + 2, B("barrel"))
        w.set(x + 1, GROUND + 1, pz0 + 2, B("lantern"))
    pool_out = np.hypot(X - 150, Z - (tf + 8)) < 6.5
    zz, xx = np.nonzero(pool_out)
    for z, x in zip(zz, xx):
        for y in range(GROUND - 4, GROUND):
            w.set(x, y, z, B("water"))
        w.set(x, GROUND - 5, z, B("gravel"))
    shop_pos = (123, GROUND, (pz0 + pz1) // 2)

    # ---------------- Wohnbereich in der Westwand ----------------
    fx = w.face_pos(338, 72, 150, -1, "x")
    rx1 = fx - 3
    rx0 = rx1 - 18
    carve_room(w, rx0, 66, 326, rx1, 77, 352, floor="spruce_planks", light="lantern", round_=False)
    w.box(rx0, 72, 326, rx1, 72, 352, B("spruce_planks"))          # Zwischendecke
    w.box(rx0 + 2, 72, 328, rx0 + 5, 72, 332, 0)                     # Treppenloch
    for i in range(6):
        w.set(rx0 + 3, 66 + i, 330, B("stripped_spruce_log"))
    w.box(rx0, 66, 326, rx0, 70, 352, B("bookshelf"))
    for z in range(330, 350, 6):
        w.set(rx0 + 8, 73, z, B("lantern"))
    w.box(rx1, 66, 328, fx + 1, 77, 350, 0)                           # Fensterfront
    w.box(rx1 + 1, 66, 328, rx1 + 1, 77, 350, B("glass"))
    w.box(rx1 + 1, 66, 337, rx1 + 1, 69, 340, 0)                      # Tür zum Balkon
    w.box(rx1 + 1, 65, 330, fx + 12, 65, 348, B("spruce_planks"))     # Balkon
    for z in (330, 348):
        for x in range(rx1 + 2, fx + 13):
            w.set(x, 66, z, B("spruce_fence"))
    for z in range(330, 349):
        if not 336 <= z <= 341:
            w.set(fx + 12, 66, z, B("spruce_fence"))
    for (x, z) in ((fx + 12, 330), (fx + 12, 348)):
        top = w.column_top()
        for y in range(40, 65):
            if w.b[y, z, x] == 0 or w.b[y, z, x] == B("water"):
                w.b[y, z, x] = B("spruce_log")
        w.set(x, 67, z, B("lantern"))
    wohn_pos = ((rx0 + rx1) // 2, 68, 339)

    # ---------------- Werkstatt in der Westwand (Norden) ----------------
    fxw = w.face_pos(176, 58, 150, -1, "x")
    carve_room(w, fxw - 20, FLOOR + 3, 164, fxw - 3, FLOOR + 11, 188, floor="stone_bricks", light="lantern",
               round_=True)
    w.box(fxw - 3, FLOOR + 3, 172, fxw + 1, FLOOR + 8, 180, 0)
    w.box(fxw - 2, FLOOR + 2, 172, fxw + 1, FLOOR + 2, 180, B("stone_bricks"))
    for i, blk in enumerate(["crafting_table", "smithing_table", "anvil", "blast_furnace", "blast_furnace",
                             "barrel"]):
        w.set(fxw - 18, FLOOR + 3, 168 + i * 3, B(blk))
    werk_pos = (fxw - 11, FLOOR + 4, 176)

    # ---------------- Farm-Kammern in der Ostwand ----------------
    farm_pos = []
    for k, (z0, z1) in enumerate([(146, 170), (178, 202), (210, 234)]):
        fxe = w.face_pos((z0 + z1) // 2, 64, 200, +1, "x")
        carve_room(w, fxe + 3, 60, z0, fxe + 24, 76, z1, floor="stone_bricks", light="lantern", round_=False)
        w.box(fxe - 1, 60, (z0 + z1) // 2 - 1, fxe + 3, 63, (z0 + z1) // 2 + 1, 0)
        w.box(fxe, 66, z0 + 3, fxe + 3, 70, z1 - 3, 0)
        w.box(fxe + 2, 66, z0 + 3, fxe + 2, 70, z1 - 3, B("glass"))
        farm_pos.append((fxe + 13, 64, (z0 + z1) // 2))

    # ---------------- Felsbogen und Brücken ----------------
    arch(w, (88, LAKE - 4, 362), (130, LAKE - 2, 353), height=27, thick=3.2,
         blk="stone")
    retexture(w, 80, 40, 340, 140, 90, 372, ["stone"], [("andesite", 0.3), ("tuff", 0.15),
                                                         ("mossy_cobblestone", 0.1)])
    green_tops(w, mask2d=(X > 80) & (X < 140) & (Z > 340) & (Z < 372), blk="grass")
    arch_top = (109, LAKE + 26, 358)
    bridge(w, (fx + 12, 65, 339), (arch_top[0] - 2, arch_top[1] + 4, arch_top[2]), sag=3)
    bridge(w, (133, LAKE + 7, 354), (170, LAKE + 6, 404), sag=5)

    # ---------------- Verzauberungsinsel ----------------
    top = w.column_top()
    cx, cz = 176, 410
    cy = top[cz, cx] + 1
    for a in np.linspace(0, 2 * np.pi, 22, endpoint=False):
        x, z = cx + 4 * np.cos(a), cz + 4 * np.sin(a)
        if not (np.cos(a) < -0.85):
            w.set(x, cy, z, B("bookshelf"))
            w.set(x, cy + 1, z, B("bookshelf"))
    w.box(cx - 3, cy - 1, cz - 3, cx + 3, cy - 1, cz + 3, B("polished_andesite"))
    w.set(cx, cy, cz, B("lantern"))
    tree_cherry(w, cx + 8, top[cz - 4, cx + 8] + 1, cz - 4, h=7)
    zauber_pos = (cx, cy, cz)

    # ---------------- Aussichtspunkt ----------------
    region = (X > 240) & (Z > 280) & (Z < 360)
    hh = np.where(region, h, -1)
    az, ax_ = np.unravel_index(np.argmax(hh), hh.shape)
    ay = int(h[az, ax_]) + 1
    w.box(ax_ - 4, ay, az - 4, ax_ + 4, ay, az + 4, B("spruce_planks"))
    w.box(ax_ - 4, ay + 1, az - 4, ax_ + 4, ay + 8, az + 4, 0)
    for (x, z) in ((ax_ - 4, az - 4), (ax_ + 4, az - 4), (ax_ - 4, az + 4), (ax_ + 4, az + 4)):
        w.set(x, ay + 1, z, B("spruce_fence"))
        w.set(x, ay + 2, z, B("lantern"))
    aus_pos = (int(ax_), ay, int(az))

    # ---------------- Wege ----------------
    path = [(150, 520), (165, 495), (205, 466), (224, 420), (226, 360), (210, 300), (186, 262),
            (176, 214), (172, 160), (163, 112), (152, 86)]
    paint_path(w, smooth_polyline(path, 8), width=1.4, lanterns=16)
    paint_path(w, smooth_polyline([(150, 520), (118, 498), (92, 470), (72, 420), (fx + 14, 352)], 8),
               width=1.2, lanterns=16)

    # ---------------- Bäume ----------------
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    grass = (gb == B("grass")) | (gb == B("moss"))
    valley = (d < 0.86) & grass & ~terr & (rd > 7)
    north = valley & (Z < 140) & (pool_d > 1.6)
    for z, x in scatter_points(w, north, 70, 7):
        tree_spruce(w, x, top[z, x] + 1, z, h=int(rng.integers(12, 22)))
    meadow = valley & (Z >= 140) & (Z < 270) & (X < 190)
    for z, x in scatter_points(w, meadow, 34, 11):
        tree_cherry(w, x, top[z, x] + 1, z)
    river_side = valley & (rd < 14) & (Z >= 140)
    for z, x in scatter_points(w, river_side, 26, 9):
        tree_round(w, x, top[z, x] + 1, z, log="birch_log", leaf="birch_leaves")
    south = valley & (Z > 470) & (np.abs(X - 150) > 12)
    for z, x in scatter_points(w, south, 30, 9):
        tree_round(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, valley & (Z > 140), 140, 5):
        bush(w, x, top[z, x] + 1, z, leaf="flowering_azalea_leaves" if rng.random() < 0.45 else "azalea_leaves")
    island = (i1 < 0.9) & grass
    for z, x in scatter_points(w, island, 4, 6):
        bush(w, x, top[z, x] + 1, z, leaf="flowering_azalea_leaves")
    outside = (d > 1.05) & grass & (slope < 1.2) & ~fore & foot
    for z, x in scatter_points(w, outside, 260, 6):
        tree_spruce(w, x, top[z, x] + 1, z)
    ledges = (d > 0.9) & (d < 1.0) & grass
    for z, x in scatter_points(w, ledges, 60, 8):
        bush(w, x, top[z, x] + 1, z)
    tree_spruce(w, 118, top[446, 116] + 1, 446, h=14)

    zones = [
        dict(name="Geheimer Eingang", typ="eingang", pos=(150, GROUND + 3, tf + 2),
             text="An der Außenwand stürzt ein 75 Blöcke hoher Wasserfall herab. Direkt dahinter beginnt ein "
                  f"9 Blöcke breiter Tunnel. Er führt {tz1 - tz0} Blöcke durch den Fels ins Tal und ist mit Laternen "
                  "beleuchtet."),
        dict(name="Shop-Platz", typ="shop", pos=shop_pos,
             text="Ein kleiner Platz aus Steinziegeln vor dem Wasserfall mit Marktständen aus Fässern. Hier "
                  "können Besucher handeln, ohne dass sie dein Tal sehen."),
        dict(name="Lager hinter dem Wasserfall", innen=True, typ="lager", pos=lager_pos,
             text="Eine 36 × 25 Blöcke große Höhle hinter dem Hauptwasserfall im Norden. Man geht durch den "
                  "Wasservorhang hinein. Drinnen stehen Regalreihen aus Fässern, Platz für ein Sortiersystem "
                  "ist genug da."),
        dict(name="Wohnbereich in der Felswand", innen=True, typ="wohnen", pos=wohn_pos,
             text="Zwei Stockwerke sind in die Westwand gehauen, mit einer 23 Blöcke breiten Glasfront zum See. "
                  "Davor liegt ein Balkon auf Stelzen, und eine Hängebrücke führt zum Felsbogen."),
        dict(name="Werkstatt", innen=True, typ="werkstatt", pos=werk_pos,
             text="Eine gewölbte Kammer in der Westwand mit Werkbank, Schmiedetisch, Amboss und Schmelzöfen. "
                  "Sie liegt nah am Lager."),
        dict(name="Farm-Kammer 1", innen=True, typ="farm", pos=farm_pos[0],
             text="22 × 17 × 25 Blöcke im Fels der Ostwand. Gut geeignet für eine Eisenfarm. Von außen sieht "
                  "man nur schmale Glasschlitze."),
        dict(name="Farm-Kammer 2", innen=True, typ="farm", pos=farm_pos[1],
             text="Gleiche Größe wie Kammer 1. Hier passen Tierfarmen hin, zum Beispiel Kühe, Schafe und "
                  "Hühner."),
        dict(name="Farm-Kammer 3", innen=True, typ="farm", pos=farm_pos[2],
             text="Hier passt eine XP-Farm hin, zum Beispiel ein Mob-Spawner-Raum mit Wasserrinne. Sie liegt "
                  "direkt hinter den Feldern."),
        dict(name="Reisterrassen", typ="farm", pos=(206, FLOOR + 6, 192),
             text="Vier Terrassen mit Stützmauern aus bemoosten Steinziegeln. Wasserrinnen versorgen den "
                  "Weizen. Zwei schmale Schleierfälle kommen von der Ostwand."),
        dict(name="Felsbogen", typ="highlight", pos=arch_top,
             text="Ein natürlicher Steinbogen spannt sich 27 Blöcke hoch über den See. Oben wächst Gras. "
                  "Hängebrücken verbinden ihn mit dem Wohnbereich und der Verzauberungsinsel."),
        dict(name="Verzauberungsinsel", typ="werkstatt", pos=zauber_pos,
             text="Ein Ring aus Bücherregalen auf der Insel im See, mit einem Kirschbaum daneben. In die Mitte "
                  "kommt der Zaubertisch."),
        dict(name="Hauptwasserfall", typ="highlight", pos=(150, 95, fz + 1),
             text="Er fällt aus einer Felsspalte 78 Blöcke tief in eine Gumpe. Von dort fließt ein Bach durch "
                  "die Kirschwiese zum See."),
        dict(name="Aussichtspunkt", typ="highlight", pos=aus_pos,
             text="Eine Plattform auf dem höchsten Gipfel der Ostwand. Von hier sieht man das ganze Tal."),
    ]
    info = dict(
        slug=SLUG, nr=1, title="Das versteckte Tal",
        tagline="Rundum Felswände, rein kommt man nur durch einen Wasserfall.",
        story=[
            "Von außen sieht man nur einen wilden Bergkamm mit Schneegipfeln. Der einzige Weg hinein führt "
            "durch einen Tunnel hinter einem Wasserfall.",
            "Drinnen öffnet sich ein rund 180 × 470 Blöcke großes Tal mit Kirschwiese, Bach, Fichtenwald und einem "
            "großen See. Über den See spannt sich ein Felsbogen. Von den Wänden stürzen fünf Wasserfälle.",
            "Die ganze Base steckt im Fels: Das Lager liegt hinter dem Hauptwasserfall, der Wohnbereich hat "
            "eine Glasfront zum See, die Farmen sind in der Ostwand versteckt.",
        ],
        ground_y=GROUND, water_level=LAKE, paste_y=63 - GROUND,
        paste_note="Dann liegt der Boden rund um die Berge auf normaler Höhe (Y 63), und die Gipfel reichen bis Y {welt_max}.",
        water_color="#2f7fc4", sky="day",
        camera=dict(target=(150, 58, 330), pos=(250, 250, 650)),
        clip=None,
        zones=zones,
        phasen=[
            ("Abstecken", "Den Umriss des Tals (Ellipse, ca. 180 × 470) und die Lage von Tunnel, See und "
                          "Wasserfällen mit Wolle markieren."),
            ("Wände hochziehen", "Den Bergring rundum aufbauen, außen flacher und innen steil mit kleinen "
                                 "Simsen. Hier werden die meisten Blöcke verbaut."),
            ("Tal ausheben", "See (bis 14 tief), Bachbett und Gumpe ausgraben. Was dabei abgebaut wird, "
                             "geht direkt in die Wände."),
            ("Wasser", "Quellen in die Felsspalten setzen. Fallendes Wasser fließt nicht seitlich, deshalb "
                       "bleibt der Höhleneingang hinter dem Vorhang frei."),
            ("Base einbauen", "Lager, Werkstatt, Wohnbereich und Farm-Kammern in den Fels hauen und dann "
                              "Fensterfronten und Balkon bauen."),
            ("Natur", "Bäume, Büsche, Terrassen, Wege mit Laternen. Zuletzt Schnee auf die Gipfel."),
        ],
        tipps=[
            "Die Wände mit 3–4 Gesteinsarten in Schichten bauen (Stein, Andesit, Tuff, Calcit). Dann sehen "
            "sie aus wie echte Felsen.",
            "Damit Laub nicht zerfällt, entweder mit Schere abgebautes Laub benutzen oder es nah an Stämmen "
            "platzieren. In der Schematic ist es als dauerhaft markiert.",
            "Den Tunnel-Eingang erst ganz zum Schluss öffnen. So bleibt das Tal bis zur Enthüllung geheim.",
        ],
    )
    return w, info
