"""Landschaft 6: Die Vulkaninsel.

Eine eigene Insel im Meer: ein 135 Blöcke hoher Vulkan mit Lavasee im Krater und zwei Lavaströmen,
Dschungel an den Hängen, eine türkise Lagune mit Sandstrand, schwarzer Strand und ein Hafen.
"""
import numpy as np

from mclib import (B, OCCLUDES, World, bridge, bush, carve_room, fbm2, fbm3, leaf_blob, paint_path, polyline_dist,
                   retexture, ridged2, scatter_points, smooth_polyline, smoothstep, tree_jungle, tree_palm,
                   tree_round)

W, H, D = 370, 190, 490
WATER = 40
SLUG = "vulkaninsel"
VX, VZ = 172, 182


def generate():
    w = World(W, H, D, seed=66)
    X, Z = w.X, w.Z
    rng = w.rng

    wx = X + fbm2(X, Z, 55, 3, 1) * 20
    wz = Z + fbm2(X, Z, 55, 3, 2) * 20
    e = np.hypot((wx - 182) / 140, (wz - 245) / 205)
    foot = e < 1.12

    # ---------------- Grundform ----------------
    sea_floor = WATER - 3 - 13 * smoothstep(0.9, 1.12, e)
    low = WATER + 3 + fbm2(X, Z, 45, 4, 3) * 5 + np.maximum(0, fbm2(X, Z, 70, 3, 4)) * 10
    coast = smoothstep(0.82, 0.92, e)
    land = low * (1 - coast) + (WATER - 1) * coast
    h = np.where(e < 0.92, land, sea_floor)
    h = np.where((e >= 0.9) & (e < 0.95), np.minimum(h, WATER), h)

    rv = np.hypot(X - VX, Z - VZ) * (1 + fbm2(X, Z, 30, 3, 5) * 0.12)
    cone = WATER + 136 * np.clip(1 - rv / 128, 0, 1) ** 1.35 + ridged2(X, Z, 22, 3, 6) * 8 * np.clip(1 - rv / 110, 0, 1)
    crater = rv < 24
    cone = np.where(rv < 30, np.minimum(cone, WATER + 122 + (rv - 24) * 2.2), cone)
    cone = np.where(crater, WATER + 112 + fbm2(X, Z, 6, 2, 7) * 1.5, cone)
    h = np.maximum(h, np.where(e < 0.95, cone, -1))

    # Lagune
    ld = np.hypot((wx - 192) / 52, (wz - 398) / 38)
    lagoon = ld < 1
    h = np.where(lagoon, np.minimum(h, WATER - 3 - 3 * smoothstep(1, 0.3, ld)), h)
    reef = (ld >= 1) & (ld < 1.22) & (np.abs(X - 192) > 9)
    h = np.where(reef & (e > 0.82), np.maximum(np.minimum(h, WATER + 1), WATER), h)
    h = np.where((ld >= 1) & (ld < 1.22) & (np.abs(X - 192) <= 9) & (Z > 398), np.minimum(h, WATER - 3), h)
    # Klippe am Nordufer der Lagune (für den Wasserfall und den Wohnbereich)
    cliff = (np.abs(X - 192) < 40) & (Z > 330) & (Z < 362) & (ld > 1.0)
    h = np.where(cliff, np.maximum(h, WATER + 22 + fbm2(X, Z, 8, 2, 9) * 3), h)

    # Lavaströme
    flow1 = smooth_polyline([(VX + 18, VZ + 4), (220, 200), (262, 228), (300, 250), (328, 262)], 10)
    flow2 = smooth_polyline([(VX - 16, VZ + 14), (130, 228), (96, 262), (66, 288), (44, 300)], 10)
    fd = np.minimum(polyline_dist(X, Z, flow1), polyline_dist(X, Z, flow2))
    h = np.where((fd < 6) & (rv > 26), h - 2 * smoothstep(6, 2, fd), h)
    lava = (fd < 2.6) & (rv > 26) & (h > WATER + 1)

    # ---------------- Oberflächen ----------------
    gz, gx = np.gradient(h)
    slope = np.hypot(gx, gz)
    r = rng.random(h.shape)
    surf = np.full(h.shape, B("grass"), np.uint8)
    sub = np.full(h.shape, B("dirt"), np.uint8)
    volc = h > WATER + 55 + fbm2(X, Z, 12, 2, 8) * 10
    mid = (h > WATER + 32 + fbm2(X, Z, 12, 2, 9) * 8) & ~volc
    for m_, opts in ((volc, [("basalt", .3), ("blackstone", .2), ("tuff", .2), ("smooth_basalt", .15), ("gravel", .15)]),
                     (mid, [("coarse_dirt", .35), ("gravel", .2), ("grass", .3), ("tuff", .15)])):
        acc = 0.0
        for blk, p in opts:
            surf[m_ & (r >= acc) & (r < acc + p)] = B(blk)
            acc += p
        sub[m_] = 255
    surf[slope > 2.2] = 255
    sub[slope > 2.2] = 255
    beach = (h <= WATER + 2.5) & (e < 0.95) & ~volc
    surf[beach] = B("sand")
    sub[beach] = B("sand")
    blackbeach = beach & ((np.hypot(X - 325, Z - 262) < 34) | (np.hypot(X - 46, Z - 300) < 30))
    surf[blackbeach] = B("black_sand")
    sub[blackbeach] = B("black_sand")
    seab = h < WATER
    surf[seab & (r < 0.75)] = B("sand")
    surf[seab & (r >= 0.75) & (r < 0.9)] = B("gravel")
    surf[seab & (r >= 0.9)] = B("clay")
    sub[seab] = B("sand")
    surf[(fd < 6) & ~lava & (h > WATER + 1)] = B("basalt")
    surf[crater] = B("magma_block")
    rock_low = w.strata(["stone", "andesite", "stone", "tuff", "granite"], band=3, seed=10)
    rock_high = w.strata(["blackstone", "basalt", "tuff", "smooth_basalt", "basalt", "stone"], band=3, seed=11)

    def rock_fn(y):
        return np.where(rv < 100, rock_high(y), rock_low(y))
    w.fill_heightmap(np.where(foot, h, -1), surf, sub, 3, rock_fn=rock_fn, bottom=np.full(h.shape, WATER - 22.0))
    w.flood(WATER, region=foot & (e > 0.8) | lagoon)

    # Lavasee im Krater, Lavaströme mit Obsidian-Rand
    top = w.column_top()
    zz, xx = np.nonzero(crater & foot)
    for z, x in zip(zz, xx):
        t = top[z, x]
        w.b[t - 2:t + 1, z, x] = B("lava")
    zz, xx = np.nonzero(lava & foot)
    for z, x in zip(zz, xx):
        t = top[z, x]
        w.b[t, z, x] = B("lava")
        w.b[t - 1, z, x] = B("magma_block")
    edge = (fd >= 2.6) & (fd < 4) & (rv > 26) & foot
    zz, xx = np.nonzero(edge)
    for z, x in zip(zz, xx):
        t = top[z, x]
        if t > WATER:
            w.b[t, z, x] = B("obsidian") if rng.random() < 0.4 else B("magma_block")

    # ---------------- Magmakammer + Schmiede im Vulkan ----------------
    w.ellipsoid(VX, WATER + 52, VZ, 18, 12, 18, 0, noise=0.2, seed=4)
    w.ellipsoid(VX, WATER + 44, VZ, 17, 5, 17, B("lava"), replace=[0])
    w.cylinder(VX, VZ, WATER + 60, WATER + 113, 3.5, B("lava"))
    sy = WATER + 46
    fx = w.face_pos(VZ + 4, sy + 3, W - 1, -1, "x")
    carve_room(w, VX + 26, sy, VZ - 10, VX + 44, sy + 8, VZ + 14, floor="polished_andesite", light="lantern",
               round_=True)
    w.box(VX + 17, sy, VZ - 6, VX + 26, sy + 7, VZ + 10, 0)
    w.box(VX + 18, sy, VZ - 6, VX + 18, sy + 7, VZ + 10, B("glass"))
    for i, blk in enumerate(["smithing_table", "anvil", "blast_furnace", "blast_furnace", "crafting_table", "barrel"]):
        w.set(VX + 42, sy, VZ - 8 + i * 4, B(blk))
    # Gang von der Schmiede nach draußen (Osthang)
    tx = VX + 44
    while tx < W - 1 and OCCLUDES[w.b[sy + 2, VZ + 2, tx]]:
        tx += 1
    w.box(VX + 44, sy, VZ, tx + 1, sy + 4, VZ + 4, 0)
    w.box(VX + 44, sy - 1, VZ, tx + 1, sy - 1, VZ + 4, B("polished_andesite"))
    for x in range(VX + 46, tx, 6):
        w.set(x, sy + 3, VZ, B("lantern"))
    schmiede = (VX + 34, sy + 1, VZ + 2)

    # ---------------- Lager in der Lavaröhre ----------------
    tube = smooth_polyline([(VX - 100, VZ + 40), (VX - 70, VZ + 30), (VX - 42, VZ + 12)], 12)
    ty_ = WATER + 14
    for (px, pz) in tube:
        w.ellipsoid(px, ty_ + 4, pz, 6, 5, 6, B("smooth_basalt"), replace=[B(k) for k in
                    ("stone", "andesite", "tuff", "granite", "blackstone", "basalt", "dirt", "coarse_dirt", "gravel")])
    for (px, pz) in tube:
        w.ellipsoid(px, ty_ + 4, pz, 4.6, 4.2, 4.6, 0)
    for i, (px, pz) in enumerate(tube):
        w.box(px - 3, ty_, pz - 3, px + 3, ty_, pz + 3, B("spruce_planks"), replace=[0, B("smooth_basalt")])
        if i % 3 == 0:
            w.set(px - 3, ty_ + 1, pz, B("barrel"))
            w.set(px + 3, ty_ + 1, pz, B("barrel"))
            w.set(px - 3, ty_ + 2, pz, B("barrel"))
            w.set(px + 3, ty_ + 2, pz, B("barrel"))
        if i % 6 == 0:
            w.set(px, ty_ + 7, pz, B("shroomlight"))
    lager = (int(tube[len(tube) // 2][0]), ty_ + 1, int(tube[len(tube) // 2][1]))

    # ---------------- Wohnbereich an der Lagune ----------------
    cz0 = 336
    wy = WATER + 3
    fz = w.face_pos(192, wy + 4, 420, -1, "z")
    carve_room(w, 170, wy, fz - 18, 214, wy + 10, fz - 3, floor="jungle_planks", light="lantern", round_=False)
    w.box(170, wy + 6, fz - 18, 214, wy + 6, fz - 3, B("jungle_planks"))
    w.box(171, wy + 6, fz - 17, 174, wy + 6, fz - 14, 0)
    w.box(172, wy, fz - 3, 212, wy + 10, fz + 1, 0)
    w.box(172, wy, fz - 1, 212, wy + 10, fz - 1, B("glass"))
    w.box(190, wy, fz - 1, 194, wy + 3, fz - 1, 0)
    w.box(168, wy - 1, fz - 1, 216, wy - 1, fz + 12, B("jungle_planks"))
    for x in range(168, 217):
        w.set(x, wy, fz + 12, B("spruce_fence"))
    for (x, z) in ((168, fz + 12), (216, fz + 12), (192, fz + 12)):
        for y in range(WATER - 6, wy - 1):
            if not OCCLUDES[w.b[y, z, x]]:
                w.b[y, z, x] = B("jungle_log")
        w.set(x, wy + 1, z, B("lantern"))
    wohn = (192, wy + 1, fz - 10)
    # Wasserfall von der Klippe in die Lagune
    for x in range(220, 226):
        for z in range(326, 342):
            t = w.column_top()[z, x]
            if t > WATER + 15:
                w.b[t, z, x] = B("water")
    w.face_water(220, 225, WATER + 24, WATER - 2, 420, -1, axis="z", depth=2)

    # ---------------- Hafen und Shop (Ostküste) ----------------
    hz = 300
    hx0 = 280
    for x in range(hx0, W):
        if w.b[WATER, hz, x] == B("water") and w.b[WATER + 1, hz, x] == 0:
            hx0 = x
            break
    w.box(hx0 - 2, WATER + 1, hz - 2, hx0 + 34, WATER + 1, hz + 2, B("spruce_planks"))
    w.box(hx0 + 30, WATER + 1, hz - 10, hx0 + 34, WATER + 1, hz + 10, B("spruce_planks"))
    for x in range(hx0, hx0 + 35, 5):
        for z in (hz - 2, hz + 2):
            for y in range(WATER - 10, WATER + 1):
                if not OCCLUDES[w.b[y, z, x]]:
                    w.b[y, z, x] = B("spruce_log")
            w.set(x, WATER + 2, z, B("spruce_fence"))
    w.set(hx0 + 34, WATER + 3, hz - 10, B("lantern"))
    w.set(hx0 + 34, WATER + 3, hz + 10, B("lantern"))
    sxp, szp = hx0 - 20, hz
    sy2 = int(w.column_top()[szp, sxp]) + 1
    w.box(sxp - 14, sy2 - 1, szp - 10, sxp + 12, sy2 - 1, szp + 10, B("jungle_planks"))
    w.box(sxp - 14, sy2, szp - 10, sxp + 12, sy2 + 12, szp + 10, 0)
    for x in range(sxp - 12, sxp + 11, 6):
        for z in (szp - 7, szp + 7):
            w.box(x, sy2, z, x + 2, sy2, z, B("barrel"))
            w.set(x + 1, sy2 + 1, z, B("lantern"))
    # Leuchtfeuer am Hafen
    for y in range(WATER - 2, WATER + 26):
        w.cylinder(hx0 + 32, hz - 14, y, y, 2.6, B("stone_bricks") if (y // 4) % 2 else B("mossy_stone_bricks"))
    w.cylinder(hx0 + 32, hz - 14, WATER + 26, WATER + 28, 2.6, B("glowstone"))
    w.cylinder(hx0 + 32, hz - 14, WATER + 29, WATER + 29, 3, B("stone_bricks"))
    shop = (sxp, sy2, szp)

    # ---------------- Farmen in einer Dschungel-Lichtung ----------------
    fxc, fzc = 92, 150
    top = w.column_top()
    farm_y = int(np.median(top[fzc - 16:fzc + 16, fxc - 20:fxc + 20]))
    for z in range(fzc - 16, fzc + 17):
        for x in range(fxc - 20, fxc + 21):
            t = top[z, x]
            w.b[farm_y + 1:H, z, x] = 0
            w.b[min(t, farm_y):farm_y + 1, z, x] = B("dirt")
            if (x - fxc) % 8 == 0:
                w.b[farm_y, z, x] = B("water")
            elif z < fzc + 4:
                w.b[farm_y, z, x] = B("farmland")
                w.b[farm_y + 1, z, x] = B("wheat")
            else:
                w.b[farm_y, z, x] = B("grass")
    for x in range(fxc - 20, fxc + 21):
        w.set(x, farm_y + 1, fzc + 16, B("spruce_fence"))
        w.set(x, farm_y + 1, fzc + 5, B("spruce_fence"))
    for z in range(fzc + 5, fzc + 17):
        w.set(fxc - 20, farm_y + 1, z, B("spruce_fence"))
        w.set(fxc + 20, farm_y + 1, z, B("spruce_fence"))
    farm = (fxc, farm_y + 1, fzc)

    # ---------------- Aussicht am Kraterrand ----------------
    top = w.column_top()
    ring = (rv > 26) & (rv < 34) & (Z > VZ)
    hh = np.where(ring, top, -1)
    az, ax_ = np.unravel_index(np.argmax(hh), hh.shape)
    ay = int(top[az, ax_]) + 1
    w.box(ax_ - 3, ay, az - 3, ax_ + 3, ay, az + 3, B("polished_andesite"))
    w.box(ax_ - 3, ay + 1, az - 3, ax_ + 3, ay + 8, az + 3, 0)
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        w.set(ax_ + dx, ay + 1, az + dz, B("spruce_fence"))
        w.set(ax_ + dx, ay + 2, az + dz, B("soul_lantern"))
    aus = (int(ax_), ay, int(az))

    # ---------------- Vegetation ----------------
    top = w.column_top()
    gb = w.b[np.clip(top, 0, H - 1), np.arange(D)[:, None], np.arange(W)[None, :]]
    away_lava = (fd > 9) & (rv > 40)
    jungle = (gb == B("grass")) & away_lava & foot & (np.hypot(X - fxc, Z - fzc) > 26)
    for z, x in scatter_points(w, jungle & (top < WATER + 45), 160, 11):
        tree_jungle(w, x, top[z, x] + 1, z)
    for z, x in scatter_points(w, jungle, 260, 7):
        tree_round(w, x, top[z, x] + 1, z, log="jungle_log", leaf="jungle_leaves", r=rng.uniform(2.3, 3.3))
    for z, x in scatter_points(w, jungle, 600, 4):
        bush(w, x, top[z, x] + 1, z, leaf="jungle_leaves" if rng.random() < 0.5 else "azalea_leaves")
    sandy = np.isin(gb, [B("sand")]) & (top >= WATER) & away_lava & foot
    for z, x in scatter_points(w, sandy, 70, 9):
        tree_palm(w, x, top[z, x] + 1, z)

    zones = [
        dict(name="Hafen", typ="eingang", pos=(hx0 + 32, WATER + 2, hz),
             text="Ein 35 Blöcke langer Steg mit Querplattform. Ein Leuchtfeuer aus Steinziegeln und Leuchtstein "
                  "zeigt Booten nachts den Weg."),
        dict(name="Strand-Markt", typ="shop", pos=shop,
             text="Ein Marktplatz aus Tropenholz direkt am Hafen, mit acht Ständen unter Palmen."),
        dict(name="Wohnhöhle an der Lagune", typ="wohnen", innen=True, pos=wohn, cut=7,
             text="Zwei Stockwerke in der Klippe am Nordufer der Lagune mit einer 40 Blöcke breiten Glasfront "
                  "und einer Holzterrasse auf Pfählen über dem Wasser."),
        dict(name="Lagune mit Wasserfall", typ="highlight", pos=(192, WATER + 1, 398),
             text="Eine flache, türkise Lagune hinter einem Sandriff, nur im Süden offen. Von der Klippe fällt "
                  "ein Wasserfall hinein."),
        dict(name="Schmiede mit Lavafenster", typ="werkstatt", innen=True, pos=schmiede, cut=7,
             text="Eine Halle in der Vulkanflanke. Durch eine Glaswand blickt man in die glühende Magmakammer. "
                  "Ein Gang führt hinaus auf den Osthang."),
        dict(name="Lager in der Lavaröhre", typ="lager", innen=True, pos=lager, cut=9,
             text="Eine alte Lavaröhre aus glattem Basalt, rund 60 Blöcke lang, mit Fässern an beiden Seiten. "
                  "Pilzlichter hängen in der Decke."),
        dict(name="Dschungel-Farm", typ="farm", pos=farm,
             text="Eine versteckte Lichtung mitten im Dschungel mit Weizenfeldern und Weiden für Tiere."),
        dict(name="Krater mit Lavasee", typ="highlight", pos=(VX, WATER + 113, VZ),
             text="Der Krater ist 48 Blöcke breit, darin brodelt ein Lavasee. Zwei Lavaströme fließen in "
                  "Basaltrinnen bis zum schwarzen Strand."),
        dict(name="Aussicht am Kraterrand", typ="highlight", pos=aus,
             text="Der höchste Punkt der Insel, eine Plattform mit Seelenlaternen direkt am Kraterrand."),
    ]
    info = dict(
        slug=SLUG, nr=6, title="Die Vulkaninsel",
        tagline="Feuer, Wasser und Dschungel auf einer eigenen Insel im Meer.",
        story=[
            "Mitten im Meer liegt eine Insel von rund 260 × 380 Blöcken. In ihrem Norden ragt ein Vulkan 136 Blöcke "
            "hoch auf, mit Lavasee im Krater und zwei Lavaströmen, die bis zum schwarzen Strand fließen.",
            "An den Hängen wächst Dschungel. Im Süden liegt eine türkise Lagune mit Sandriff, Palmen und einem "
            "Wasserfall. An der Ostküste gibt es einen Hafen mit Leuchtfeuer und Markt.",
            "Die Base nutzt die Insel: Wohnen in der Klippe an der Lagune, Schmiede mit Blick in die Magmakammer, "
            "Lager in einer Lavaröhre, Farmen in einer Dschungel-Lichtung.",
        ],
        ground_y=WATER, water_level=WATER, paste_y=63 - WATER,
        paste_note="Dann liegt der Meeresspiegel auf Y 63, und der Kraterrand reicht bis Y {welt_max}.",
        water_color="#1f9fc4", sky_color="#a9d3ee",
        surround=dict(kind="water", y=WATER + 0.9, color="#1f9fc4", floor="#c9b98a", floor_y=WATER - 16),
        camera=dict(target=(185, 62, 250), pos=(420, 215, 575)),
        clip=None,
        zones=zones,
        phasen=[
            ("Insel aufschütten", "Die Küstenlinie mit Sand abstecken und die Insel bis knapp über den "
                                  "Meeresspiegel aufschütten."),
            ("Vulkan", "Den Kegel in Ringen hochziehen, unten Stein, oben Basalt und Schwarzstein. Krater "
                       "aussparen, Magmakammer innen hohl lassen."),
            ("Lava", "Lava zuletzt einfüllen, nachdem die Rinnen aus Basalt und Obsidian fertig sind. Bäume "
                     "mindestens 6 Blöcke entfernt halten, sonst brennt der Dschungel."),
            ("Lagune und Küste", "Lagune ausheben, Riff aus Sand, Strände, schwarzer Strand aus schwarzem "
                                 "Trockenbeton."),
            ("Base", "Wohnhöhle, Schmiede, Lavaröhre, Farm-Lichtung, Hafen mit Markt und Leuchtfeuer."),
            ("Dschungel", "Tropenbäume, Palmen und Büsche. Zuletzt die Aussicht am Kraterrand."),
        ],
        tipps=[
            "Lava entzündet Holz und Laub in der Nähe. Lavaströme deshalb mit Stein einfassen und Abstand zum "
            "Dschungel halten. Feuerausbreitung lässt sich nur per Serverregel abschalten.",
            "Schwarzer Trockenbeton sieht aus wie Vulkansand. Er darf nicht nass werden, sonst wird er zu Beton.",
            "Die Schematic so einfügen, dass der Meeresspiegel auf Y 63 liegt (Unterkante auf Y {paste_y}).",
        ],
    )
    return w, info
