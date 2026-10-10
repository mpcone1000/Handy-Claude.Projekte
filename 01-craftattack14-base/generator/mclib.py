"""Gemeinsame Bausteine für die Landschafts-Generatoren.

Koordinaten: das Volumen ist ein numpy-Array b[y, z, x] (Höhe, Länge, Breite).
Diese Reihenfolge entspricht direkt dem Index von .schem und .litematic
(index = x + z*W + y*W*L), deshalb kann das Array ohne Umsortieren exportiert werden.
"""
import gzip
import io
import json
import math
import os
import struct
import time
import zlib

import numpy as np

DATA_VERSION = 3955  # Minecraft 1.21.1 – neuere Versionen konvertieren automatisch

# --------------------------------------------------------------------------
# Blockregister
# kind: 0 Luft, 1 fest, 2 Wasser, 3 Glas, 4 klein/durchlässig, 5 Lava
# --------------------------------------------------------------------------
BLOCKS = []
ID = {}


def reg(key, state, color, de, kind=1, glow=0.0):
    ID[key] = len(BLOCKS)
    BLOCKS.append(dict(key=key, state=state, color=color, kind=kind, glow=glow, de=de))


reg("air", "minecraft:air", "#000000", "Luft", kind=0)
# Gestein
reg("stone", "minecraft:stone", "#7d7d7d", "Stein")
reg("andesite", "minecraft:andesite", "#88888a", "Andesit")
reg("granite", "minecraft:granite", "#9a6c58", "Granit")
reg("diorite", "minecraft:diorite", "#bcbcbe", "Diorit")
reg("tuff", "minecraft:tuff", "#6c6d66", "Tuffstein")
reg("calcite", "minecraft:calcite", "#dfe0dc", "Calcit")
reg("deepslate", "minecraft:deepslate", "#505053", "Tiefenschiefer")
reg("cobbled_deepslate", "minecraft:cobbled_deepslate", "#4a4a4e", "Bruchtiefenschiefer")
reg("cobblestone", "minecraft:cobblestone", "#7a7a7a", "Bruchstein")
reg("mossy_cobblestone", "minecraft:mossy_cobblestone", "#6b7a5c", "Bemooster Bruchstein")
reg("mossy_stone_bricks", "minecraft:mossy_stone_bricks", "#727a60", "Bemooste Steinziegel")
reg("stone_bricks", "minecraft:stone_bricks", "#7a797a", "Steinziegel")
reg("polished_andesite", "minecraft:polished_andesite", "#848685", "Polierter Andesit")
reg("gravel", "minecraft:gravel", "#837f7e", "Kies")
reg("dripstone_block", "minecraft:dripstone_block", "#866b5c", "Tropfsteinblock")
reg("smooth_basalt", "minecraft:smooth_basalt", "#48484e", "Glatter Basalt")
reg("basalt", "minecraft:basalt[axis=y]", "#535257", "Basalt")
reg("blackstone", "minecraft:blackstone", "#2c252b", "Schwarzstein")
reg("obsidian", "minecraft:obsidian", "#140f22", "Obsidian")
reg("magma_block", "minecraft:magma_block", "#8a3a1a", "Magmablock", glow=0.55)
reg("black_sand", "minecraft:black_concrete_powder", "#1b1c21", "Schwarzer Trockenbeton (schwarzer Sand)")
reg("terracotta", "minecraft:terracotta", "#985e43", "Terrakotta")
reg("brown_terracotta", "minecraft:brown_terracotta", "#4d3324", "Braune Terrakotta")
reg("light_gray_terracotta", "minecraft:light_gray_terracotta", "#876b62", "Hellgraue Terrakotta")
reg("white_terracotta", "minecraft:white_terracotta", "#d1b2a1", "Weiße Terrakotta")
# Erde & Boden
reg("dirt", "minecraft:dirt", "#866043", "Erde")
reg("coarse_dirt", "minecraft:coarse_dirt", "#77553b", "Grobe Erde")
reg("rooted_dirt", "minecraft:rooted_dirt", "#90674c", "Wurzelerde")
reg("podzol", "minecraft:podzol", "#5b3f18", "Podsol")
reg("grass", "minecraft:grass_block", "#6aa33a", "Grasblock")
reg("moss", "minecraft:moss_block", "#5a7a2c", "Moosblock")
reg("mud", "minecraft:mud", "#3c393d", "Schlamm")
reg("packed_mud", "minecraft:packed_mud", "#8e6b50", "Festgestampfter Schlamm")
reg("clay", "minecraft:clay", "#a0a6b3", "Ton")
reg("sand", "minecraft:sand", "#dbd3a0", "Sand")
reg("sandstone", "minecraft:sandstone", "#d8cb9b", "Sandstein")
reg("dirt_path", "minecraft:dirt_path", "#9b7f45", "Trampelpfad")
reg("snow", "minecraft:snow_block", "#f4f8f8", "Schneeblock")
reg("packed_ice", "minecraft:packed_ice", "#8db4fa", "Packeis")
reg("farmland", "minecraft:farmland[moisture=7]", "#52351a", "Ackerboden")
# Flüssigkeiten
reg("water", "minecraft:water[level=0]", "#3f76e4", "Wasser", kind=2)
reg("lava", "minecraft:lava[level=0]", "#ff7a14", "Lava", kind=5, glow=1.0)
# Holz & Laub (Laub immer persistent, damit es nicht zerfällt)
reg("oak_log", "minecraft:oak_log[axis=y]", "#6d5533", "Eichenstamm")
reg("oak_leaves", "minecraft:oak_leaves[persistent=true]", "#3f7a25", "Eichenlaub")
reg("spruce_log", "minecraft:spruce_log[axis=y]", "#3a2716", "Fichtenstamm")
reg("spruce_leaves", "minecraft:spruce_leaves[persistent=true]", "#2f5233", "Fichtennadeln")
reg("birch_log", "minecraft:birch_log[axis=y]", "#d8d7d2", "Birkenstamm")
reg("birch_leaves", "minecraft:birch_leaves[persistent=true]", "#66903a", "Birkenlaub")
reg("jungle_log", "minecraft:jungle_log[axis=y]", "#5a4720", "Tropenbaumstamm")
reg("jungle_leaves", "minecraft:jungle_leaves[persistent=true]", "#2f8a1e", "Tropenbaumlaub")
reg("cherry_log", "minecraft:cherry_log[axis=y]", "#3b1c24", "Kirschstamm")
reg("cherry_leaves", "minecraft:cherry_leaves[persistent=true]", "#efb0cd", "Kirschblätter")
reg("dark_oak_log", "minecraft:dark_oak_log[axis=y]", "#3c2e1a", "Schwarzeichenstamm")
reg("dark_oak_leaves", "minecraft:dark_oak_leaves[persistent=true]", "#2f5418", "Schwarzeichenlaub")
reg("azalea_leaves", "minecraft:azalea_leaves[persistent=true]", "#5a7f2a", "Azaleenlaub")
reg("flowering_azalea_leaves", "minecraft:flowering_azalea_leaves[persistent=true]", "#86924f",
    "Blühendes Azaleenlaub")
reg("mangrove_roots", "minecraft:mangrove_roots", "#4a3b27", "Mangrovenwurzeln", kind=4)
reg("spruce_planks", "minecraft:spruce_planks", "#735531", "Fichtenholzbretter")
reg("oak_planks", "minecraft:oak_planks", "#a2834f", "Eichenholzbretter")
reg("dark_oak_planks", "minecraft:dark_oak_planks", "#42291a", "Schwarzeichenholzbretter")
reg("jungle_planks", "minecraft:jungle_planks", "#a07351", "Tropenholzbretter")
reg("stripped_spruce_log", "minecraft:stripped_spruce_log[axis=y]", "#73592f", "Entrindeter Fichtenstamm")
reg("spruce_fence", "minecraft:spruce_fence", "#5e4527", "Fichtenholzzaun", kind=4)
reg("chain", "minecraft:chain[axis=y]", "#3a404c", "Kette", kind=4)
# Licht
reg("lantern", "minecraft:lantern", "#e8b04a", "Laterne", kind=4, glow=1.0)
reg("soul_lantern", "minecraft:soul_lantern", "#5fd6d6", "Seelenlaterne", kind=4, glow=1.0)
reg("sea_lantern", "minecraft:sea_lantern", "#bfe0d6", "Seelaterne", glow=1.0)
reg("shroomlight", "minecraft:shroomlight", "#f5a14e", "Pilzlicht", glow=1.0)
reg("glowstone", "minecraft:glowstone", "#fbd874", "Leuchtstein", glow=1.0)
reg("ochre_froglight", "minecraft:ochre_froglight[axis=y]", "#f6e3a0", "Ockernes Froschlicht", glow=1.0)
reg("verdant_froglight", "minecraft:verdant_froglight[axis=y]", "#c9f0c0", "Grünes Froschlicht", glow=1.0)
reg("pearlescent_froglight", "minecraft:pearlescent_froglight[axis=y]", "#f2d6ee", "Perlmutt-Froschlicht",
    glow=1.0)
reg("cave_vines", "minecraft:cave_vines_plant[berries=true]", "#d4913a", "Höhlenranken mit Leuchtbeeren",
    kind=4, glow=0.8)
reg("hanging_roots", "minecraft:hanging_roots", "#a07457", "Hängende Wurzeln", kind=4)
# Glas
reg("glass", "minecraft:glass", "#cfe6ee", "Glas", kind=3)
reg("blue_glass", "minecraft:light_blue_stained_glass", "#7bb8e6", "Hellblaues Glas", kind=3)
# Pilze, Kristalle, Meer
reg("red_mushroom_block", "minecraft:red_mushroom_block", "#c62e2c", "Roter Pilzblock")
reg("brown_mushroom_block", "minecraft:brown_mushroom_block", "#956f51", "Brauner Pilzblock")
reg("mushroom_stem", "minecraft:mushroom_stem", "#d6cfc2", "Pilzstiel")
reg("warped_wart", "minecraft:warped_wart_block", "#14868f", "Wirrwarzenblock")
reg("amethyst", "minecraft:amethyst_block", "#9a6fdb", "Amethystblock", glow=0.35)
reg("prismarine", "minecraft:prismarine", "#63a39b", "Prismarin")
reg("dark_prismarine", "minecraft:dark_prismarine", "#335b4b", "Dunkler Prismarin")
# Ausbau
reg("barrel", "minecraft:barrel[facing=up]", "#8a6639", "Fass")
reg("bookshelf", "minecraft:bookshelf", "#7a6038", "Bücherregal")
reg("hay", "minecraft:hay_block[axis=y]", "#c4a21c", "Heuballen")
reg("wheat", "minecraft:wheat[age=7]", "#d8be4e", "Weizen", kind=4)
reg("crafting_table", "minecraft:crafting_table", "#8c6a3e", "Werkbank")
reg("smithing_table", "minecraft:smithing_table", "#3d3540", "Schmiedetisch")
reg("blast_furnace", "minecraft:blast_furnace[facing=north]", "#5a5a5c", "Schmelzofen")
reg("anvil", "minecraft:anvil[facing=north]", "#444448", "Amboss")
reg("soul_sand", "minecraft:soul_sand", "#51402f", "Seelensand")
reg("copper", "minecraft:oxidized_copper", "#52a284", "Oxidierter Kupferblock")

KIND = np.array([b["kind"] for b in BLOCKS], np.uint8)
OCCLUDES = np.isin(KIND, [1, 5])


def B(key):
    return ID[key]


# --------------------------------------------------------------------------
# Noise (Gradientenrauschen, vollständig mit numpy vektorisiert)
# --------------------------------------------------------------------------
_ANG = np.linspace(0, 2 * np.pi, 256, endpoint=False)
_G2 = np.stack([np.cos(_ANG), np.sin(_ANG)], -1)
_rng_g3 = np.random.default_rng(1234)
_G3 = _rng_g3.normal(size=(256, 3))
_G3 /= np.linalg.norm(_G3, axis=1, keepdims=True)


def _hash(seed, *ints):
    h = np.int64(seed * 2654435761 + 97531) & 0xFFFFFFFF
    primes = (73856093, 19349663, 83492791)
    for i, a in enumerate(ints):
        h = h ^ ((a.astype(np.int64) * primes[i]) & 0xFFFFFFFF)
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 255).astype(np.intp)


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise2(x, z, seed=0):
    x = np.asarray(x, np.float64)
    z = np.asarray(z, np.float64)
    x, z = np.broadcast_arrays(x, z)
    xi = np.floor(x).astype(np.int64)
    zi = np.floor(z).astype(np.int64)
    fx = x - xi
    fz = z - zi
    out = 0
    u = _fade(fx)
    v = _fade(fz)
    res = []
    for dx in (0, 1):
        for dz in (0, 1):
            g = _G2[_hash(seed, xi + dx, zi + dz)]
            res.append(g[..., 0] * (fx - dx) + g[..., 1] * (fz - dz))
    n00, n01, n10, n11 = res
    a = n00 + u * (n10 - n00)
    b = n01 + u * (n11 - n01)
    out = a + v * (b - a)
    return out * 1.41


def noise3(x, y, z, seed=0):
    x, y, z = np.broadcast_arrays(np.asarray(x, np.float64), np.asarray(y, np.float64),
                                  np.asarray(z, np.float64))
    xi = np.floor(x).astype(np.int64)
    yi = np.floor(y).astype(np.int64)
    zi = np.floor(z).astype(np.int64)
    fx, fy, fz = x - xi, y - yi, z - zi
    u, v, w = _fade(fx), _fade(fy), _fade(fz)
    c = {}
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                g = _G3[_hash(seed, xi + dx, yi + dy, zi + dz)]
                c[dx, dy, dz] = g[..., 0] * (fx - dx) + g[..., 1] * (fy - dy) + g[..., 2] * (fz - dz)
    x00 = c[0, 0, 0] + u * (c[1, 0, 0] - c[0, 0, 0])
    x10 = c[0, 1, 0] + u * (c[1, 1, 0] - c[0, 1, 0])
    x01 = c[0, 0, 1] + u * (c[1, 0, 1] - c[0, 0, 1])
    x11 = c[0, 1, 1] + u * (c[1, 1, 1] - c[0, 1, 1])
    y0 = x00 + v * (x10 - x00)
    y1 = x01 + v * (x11 - x01)
    return (y0 + w * (y1 - y0)) * 1.6


def fbm2(x, z, scale, octaves=4, seed=0, gain=0.5):
    total = 0.0
    amp = 1.0
    norm = 0.0
    f = 1.0 / scale
    for o in range(octaves):
        total = total + amp * noise2(x * f, z * f, seed + o * 101)
        norm += amp
        amp *= gain
        f *= 2.0
    return total / norm


def fbm3(x, y, z, scale, octaves=3, seed=0, gain=0.5):
    total = 0.0
    amp = 1.0
    norm = 0.0
    f = 1.0 / scale
    for o in range(octaves):
        total = total + amp * noise3(x * f, y * f, z * f, seed + o * 131)
        norm += amp
        amp *= gain
        f *= 2.0
    return total / norm


def ridged2(x, z, scale, octaves=4, seed=0):
    total = 0.0
    amp = 1.0
    norm = 0.0
    f = 1.0 / scale
    for o in range(octaves):
        n = 1.0 - np.abs(noise2(x * f, z * f, seed + o * 77))
        total = total + amp * n * n
        norm += amp
        amp *= 0.5
        f *= 2.0
    return total / norm


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def box_blur2(a, r):
    """Einfacher 2D-Weichzeichner (separierbar, mit Randwiederholung)."""
    if r <= 0:
        return a
    out = a.astype(np.float64)
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode="edge")
        c = np.cumsum(p, axis=axis)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
        n = out.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        out = (hi - lo) / (2 * r + 1)
    return out


# --------------------------------------------------------------------------
# Welt
# --------------------------------------------------------------------------
class World:
    def __init__(self, W, H, D, seed=1):
        self.W, self.H, self.D = W, H, D
        self.b = np.zeros((H, D, W), np.uint8)
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        # 2D-Koordinatenraster [z, x]
        self.Z, self.X = np.meshgrid(np.arange(D, dtype=np.float64), np.arange(W, dtype=np.float64),
                                     indexing="ij")

    # ---- Grundoperationen ----
    def inside(self, x, y, z):
        return 0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.D

    def set(self, x, y, z, blk, only_air=False):
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        if self.inside(x, y, z):
            if only_air and self.b[y, z, x] != 0:
                return
            self.b[y, z, x] = blk

    def get(self, x, y, z):
        x, y, z = int(x), int(y), int(z)
        if self.inside(x, y, z):
            return self.b[y, z, x]
        return 0

    def _bbox(self, x0, y0, z0, x1, y1, z1):
        x0, y0, z0 = max(0, int(math.floor(x0))), max(0, int(math.floor(y0))), max(0, int(math.floor(z0)))
        x1 = min(self.W, int(math.ceil(x1)) + 1)
        y1 = min(self.H, int(math.ceil(y1)) + 1)
        z1 = min(self.D, int(math.ceil(z1)) + 1)
        if x0 >= x1 or y0 >= y1 or z0 >= z1:
            return None
        return x0, y0, z0, x1, y1, z1

    def box(self, x0, y0, z0, x1, y1, z1, blk, only_air=False, replace=None):
        bb = self._bbox(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1))
        if bb is None:
            return
        x0, y0, z0, x1, y1, z1 = bb
        sub = self.b[y0:y1, z0:z1, x0:x1]
        if only_air:
            sub[sub == 0] = blk
        elif replace is not None:
            sub[np.isin(sub, replace)] = blk
        else:
            sub[...] = blk

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, blk, only_air=False, replace=None, noise=0.0, seed=0,
                  nscale=6.0, keep=None, lower_only=False):
        bb = self._bbox(cx - rx - 2, cy - ry - 2, cz - rz - 2, cx + rx + 2, cy + ry + 2, cz + rz + 2)
        if bb is None:
            return None
        x0, y0, z0, x1, y1, z1 = bb
        Y, Zg, Xg = np.ogrid[y0:y1, z0:z1, x0:x1]
        d = ((Xg - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Zg - cz) / rz) ** 2
        if noise:
            Yf, Zf, Xf = np.meshgrid(np.arange(y0, y1), np.arange(z0, z1), np.arange(x0, x1), indexing="ij")
            d = d + noise * fbm3(Xf, Yf, Zf, nscale, 2, seed)
        m = d <= 1.0
        if lower_only:
            m &= np.broadcast_to(Y <= cy, m.shape)
        sub = self.b[y0:y1, z0:z1, x0:x1]
        if only_air:
            m &= sub == 0
        if replace is not None:
            m &= np.isin(sub, replace)
        if keep is not None:
            m &= self.rng.random(m.shape) < keep
        sub[m] = blk
        return m

    def cylinder(self, cx, cz, y0, y1, r, blk, only_air=False, replace=None):
        bb = self._bbox(cx - r - 1, min(y0, y1), cz - r - 1, cx + r + 1, max(y0, y1), cz + r + 1)
        if bb is None:
            return
        x0, yy0, z0, x1, yy1, z1 = bb
        _, Zg, Xg = np.ogrid[yy0:yy1, z0:z1, x0:x1]
        m = np.broadcast_to(((Xg - cx) ** 2 + (Zg - cz) ** 2) <= r * r + 0.3, (yy1 - yy0, z1 - z0, x1 - x0)).copy()
        sub = self.b[yy0:yy1, z0:z1, x0:x1]
        if only_air:
            m &= sub == 0
        if replace is not None:
            m &= np.isin(sub, replace)
        sub[m] = blk

    def line(self, p0, p1, blk, r=0.0, only_air=False, replace=None):
        p0 = np.array(p0, float)
        p1 = np.array(p1, float)
        n = int(np.linalg.norm(p1 - p0) * 2) + 1
        for t in np.linspace(0, 1, n):
            p = p0 + (p1 - p0) * t
            if r <= 0.6:
                x, y, z = int(round(p[0])), int(round(p[1])), int(round(p[2]))
                if self.inside(x, y, z):
                    cur = self.b[y, z, x]
                    if only_air and cur != 0:
                        continue
                    if replace is not None and cur not in replace:
                        continue
                    self.b[y, z, x] = blk
            else:
                self.ellipsoid(p[0], p[1], p[2], r, r, r, blk, only_air=only_air, replace=replace)

    def column_top(self):
        """Höchster Nicht-Luft-Block je Spalte (−1 wenn leer). Form [z, x]."""
        nz = self.b != 0
        any_ = nz.any(axis=0)
        top = self.H - 1 - np.argmax(nz[::-1], axis=0)
        top[~any_] = -1
        return top

    def solid_top(self):
        occ = OCCLUDES[self.b]
        any_ = occ.any(axis=0)
        top = self.H - 1 - np.argmax(occ[::-1], axis=0)
        top[~any_] = -1
        return top

    # ---- Gelände aus Höhenkarte ----
    def fill_heightmap(self, h, surface, sub="dirt", sub_depth=3, rock=None, rock_fn=None, from_y=None,
                       bottom=None):
        """Füllt Spalten bis Höhe h (float [z,x]). surface/sub: Blocknamen oder [z,x]-Arrays mit IDs."""
        hi = np.floor(h).astype(np.int32)
        surf = surface if isinstance(surface, np.ndarray) else np.full(hi.shape, B(surface), np.uint8)
        subb = sub if isinstance(sub, np.ndarray) else np.full(hi.shape, B(sub), np.uint8)
        sd = sub_depth if isinstance(sub_depth, np.ndarray) else np.full(hi.shape, sub_depth)
        lo = np.zeros_like(hi) if bottom is None else np.floor(bottom).astype(np.int32)
        ymax = min(self.H, int(hi.max()) + 1)
        ymin = max(0, int(lo.min())) if from_y is None else from_y
        for y in range(ymin, ymax):
            layer = self.b[y]
            inside = (y <= hi) & (y >= lo)
            if not inside.any():
                continue
            depth = hi - y
            if rock_fn is not None:
                rk = rock_fn(y)
            else:
                rk = B(rock or "stone")
            rk = rk if isinstance(rk, np.ndarray) else np.full(hi.shape, rk, np.uint8)
            s_ = np.where(surf == 255, rk, surf)
            u_ = np.where(subb == 255, rk, subb)
            blk = np.where(depth == 0, s_, np.where(depth <= sd, u_, rk))
            layer[inside] = blk[inside]

    def strata(self, palette, band=4, seed=0, warp=6.0, scale=60.0):
        """Liefert rock_fn(y) mit horizontalen Gesteinsschichten (wellig verzerrt)."""
        off = fbm2(self.X, self.Z, scale, 3, seed) * warp
        ids = np.array([B(p) for p in palette], np.uint8)
        jitter = fbm2(self.X, self.Z, 9.0, 2, seed + 5) * 1.5

        def fn(y):
            k = np.floor((y + off + jitter) / band).astype(np.int64) % len(ids)
            return ids[k]
        return fn

    # ---- Wasser ----
    def flood(self, level, region=None, blk="water"):
        """Füllt Luft unterhalb von level mit Wasser (optional nur in region [z,x])."""
        w = B(blk)
        for y in range(0, min(self.H, level + 1)):
            layer = self.b[y]
            m = layer == 0
            if region is not None:
                m &= region
            layer[m] = w

    def waterfall(self, x, z, ytop, ybot, width=3, depth=2, axis="x", blk="water"):
        """Wasserfall-Vorhang: width breit (entlang axis), depth tief, von ytop bis ybot (nur in Luft)."""
        w = B(blk)
        for y in range(int(ybot), int(ytop) + 1):
            for i in range(-(width // 2), width - width // 2):
                for j in range(depth):
                    if axis == "x":
                        self.set(x + i, y, z + j, w, only_air=True)
                    else:
                        self.set(x + j, y, z + i, w, only_air=True)

    def face_pos(self, a, y, start, step, axis="z"):
        """Erste feste Position, wenn man von start in Richtung step läuft (axis z: a=x, sonst a=z)."""
        line = OCCLUDES[self.b[y, :, a]] if axis == "z" else OCCLUDES[self.b[y, a, :]]
        if step > 0:
            seg = line[start:]
            if not seg.any():
                return None
            return start + int(np.argmax(seg))
        seg = line[:start + 1][::-1]
        if not seg.any():
            return None
        return start - int(np.argmax(seg))

    def face_water(self, a0, a1, y_top, y_bot, start, step, axis="z", depth=2, blk="water", spring=True):
        """Wasserfall, der an einer Felswand herabläuft. Läuft für jede Höhe von start in Richtung
        step bis zur Wand und legt dort depth Blöcke Wasser in die Luft davor."""
        wb = B(blk)
        placed = []
        for a in range(a0, a1 + 1):
            for y in range(int(y_bot), int(y_top) + 1):
                hit = self.face_pos(a, y, start, step, axis)
                if hit is None:
                    continue
                for k in range(1, depth + 1):
                    c = hit - step * k
                    if axis == "z":
                        if 0 <= c < self.D and self.b[y, c, a] == 0:
                            self.b[y, c, a] = wb
                            placed.append((a, y, c))
                    else:
                        if 0 <= c < self.W and self.b[y, a, c] == 0:
                            self.b[y, a, c] = wb
                            placed.append((c, y, a))
            if spring:
                hit = self.face_pos(a, int(y_top), start, step, axis)
                if hit is not None:
                    for k in range(0, 4):
                        c = hit + step * k
                        for yy in (int(y_top), int(y_top) + 1):
                            if axis == "z" and 0 <= c < self.D:
                                self.b[yy, c, a] = wb
                            elif axis == "x" and 0 <= c < self.W:
                                self.b[yy, a, c] = wb
        return placed

    def exposed_surface(self):
        occ = OCCLUDES[self.b]
        exp = np.zeros_like(occ)
        # Nachbarn: außerhalb gilt als verdeckt (Boden/Rand), außer oben
        exp[:-1] |= ~occ[1:]
        exp[-1] |= True
        exp[1:] |= ~occ[:-1]
        exp[:, :-1] |= ~occ[:, 1:]
        exp[:, 1:] |= ~occ[:, :-1]
        exp[:, :, :-1] |= ~occ[:, :, 1:]
        exp[:, :, 1:] |= ~occ[:, :, :-1]
        return occ & exp


# --------------------------------------------------------------------------
# Bäume und Pflanzen
# --------------------------------------------------------------------------
def leaf_blob(w, cx, cy, cz, r, leaf, ry=None, keep_shell=0.75, seed=None):
    ry = ry if ry is not None else r * 0.75
    bb = w._bbox(cx - r - 1, cy - ry - 1, cz - r - 1, cx + r + 1, cy + ry + 1, cz + r + 1)
    if bb is None:
        return
    x0, y0, z0, x1, y1, z1 = bb
    Y, Zg, Xg = np.ogrid[y0:y1, z0:z1, x0:x1]
    d = ((Xg - cx) / r) ** 2 + ((Y - cy) / ry) ** 2 + ((Zg - cz) / r) ** 2
    rnd = w.rng.random(d.shape)
    m = (d <= 0.55) | ((d <= 1.0) & (rnd < keep_shell))
    sub = w.b[y0:y1, z0:z1, x0:x1]
    m &= sub == 0
    sub[m] = B(leaf)


def tree_round(w, x, y, z, h=None, log="oak_log", leaf="oak_leaves", r=None):
    rng = w.rng
    h = h or int(rng.integers(5, 9))
    r = r or rng.uniform(2.3, 3.4)
    for i in range(h):
        w.set(x, y + i, z, B(log))
    leaf_blob(w, x, y + h - 0.5, z, r, leaf, ry=r * 0.8)
    if r > 2.8:
        for _ in range(2):
            ox, oz = rng.uniform(-2, 2, 2)
            leaf_blob(w, x + ox, y + h - 2, z + oz, r * 0.7, leaf)


def tree_spruce(w, x, y, z, h=None, log="spruce_log", leaf="spruce_leaves"):
    rng = w.rng
    h = h or int(rng.integers(9, 17))
    for i in range(h):
        w.set(x, y + i, z, B(log))
    base = int(h * 0.3)
    rmax = 1.5 + h * 0.18
    for i in range(base, h + 2):
        t = (i - base) / max(1, (h + 1 - base))
        r = rmax * (1 - t) + 0.4
        if (i - base) % 3 == 2:
            r *= 0.6
        w.cylinder(x, z, y + i, y + i, r, B(leaf), only_air=True)


def tree_cherry(w, x, y, z, h=None):
    rng = w.rng
    h = h or int(rng.integers(5, 8))
    for i in range(h):
        w.set(x, y + i, z, B("cherry_log"))
    nb = int(rng.integers(2, 5))
    for k in range(nb):
        a = rng.uniform(0, 2 * np.pi)
        L = rng.uniform(3, 5.5)
        ex, ez = x + np.cos(a) * L, z + np.sin(a) * L
        ey = y + h + rng.uniform(0, 2)
        w.line((x, y + h - 2, z), (ex, ey, ez), B("cherry_log"))
        leaf_blob(w, ex, ey + 1, ez, rng.uniform(3.0, 4.2), "cherry_leaves", ry=1.8, keep_shell=0.8)
    leaf_blob(w, x, y + h + 1, z, 3.2, "cherry_leaves", ry=1.8)


def tree_big(w, x, y, z, h, trunk_r=2.0, log="oak_log", leaf="oak_leaves", crown=9.0, branches=6,
             roots=True, leaf2=None):
    """Riesenbaum mit dickem Stamm, Ästen und mehreren Laubwolken."""
    rng = w.rng
    for i in range(h):
        t = i / h
        r = trunk_r * (1.0 - 0.45 * t) + (1.4 if (roots and i < 3) else 0) * (1 - i / 3 if i < 3 else 0)
        w.cylinder(x, z, y + i, y + i, r, B(log))
    if roots:
        for k in range(6):
            a = k / 6 * 2 * np.pi + rng.uniform(-0.3, 0.3)
            L = trunk_r + rng.uniform(3, 6)
            w.line((x, y + 3, z), (x + np.cos(a) * L, y - 1, z + np.sin(a) * L), B(log), r=0.9)
    for k in range(branches):
        a = k / branches * 2 * np.pi + rng.uniform(-0.4, 0.4)
        by = y + h * rng.uniform(0.55, 0.85)
        L = crown * rng.uniform(0.7, 1.1)
        ex, ez = x + np.cos(a) * L, z + np.sin(a) * L
        ey = by + rng.uniform(2, 6)
        w.line((x, by, z), (ex, ey, ez), B(log), r=1.0 if trunk_r > 1.5 else 0.5)
        lf = leaf2 if (leaf2 and rng.random() < 0.4) else leaf
        leaf_blob(w, ex, ey + 1, ez, crown * rng.uniform(0.45, 0.6), lf, ry=crown * 0.32)
    leaf_blob(w, x, y + h + 1, z, crown * 0.7, leaf, ry=crown * 0.4)


def tree_jungle(w, x, y, z, h=None):
    rng = w.rng
    h = h or int(rng.integers(14, 24))
    for i in range(h):
        for dx in (0, 1):
            for dz in (0, 1):
                w.set(x + dx, y + i, z + dz, B("jungle_log"))
    for k in range(3):
        a = rng.uniform(0, 2 * np.pi)
        by = y + h * rng.uniform(0.5, 0.85)
        ex, ez = x + np.cos(a) * 5, z + np.sin(a) * 5
        w.line((x, by, z), (ex, by + 3, ez), B("jungle_log"))
        leaf_blob(w, ex, by + 4, ez, 3.2, "jungle_leaves", ry=2)
    leaf_blob(w, x + 0.5, y + h + 1, z + 0.5, 5.0, "jungle_leaves", ry=2.8)


def tree_palm(w, x, y, z, h=None):
    rng = w.rng
    h = h or int(rng.integers(9, 15))
    a = rng.uniform(0, 2 * np.pi)
    lean = rng.uniform(2, 5)
    pts = []
    for i in range(h):
        t = i / h
        px = x + np.cos(a) * lean * t * t
        pz = z + np.sin(a) * lean * t * t
        w.set(px, y + i, pz, B("jungle_log"))
        pts.append((px, y + i, pz))
    tx, ty, tz = pts[-1]
    w.set(tx, ty + 1, tz, B("jungle_leaves"))
    nf = int(rng.integers(6, 9))
    for k in range(nf):
        b = k / nf * 2 * np.pi + rng.uniform(-0.2, 0.2)
        L = rng.uniform(4, 6.5)
        for s in np.linspace(0, 1, int(L * 2)):
            fx = tx + np.cos(b) * L * s
            fz = tz + np.sin(b) * L * s
            fy = ty + 1 + 1.6 * s - 3.2 * s * s
            w.set(fx, fy, fz, B("jungle_leaves"), only_air=True)


def bush(w, x, y, z, leaf="azalea_leaves", r=None):
    r = r or w.rng.uniform(1.2, 2.2)
    leaf_blob(w, x, y + r * 0.4, z, r, leaf, ry=r * 0.7, keep_shell=0.7)


def scatter_points(w, mask, n, min_dist=4, rng=None):
    """Zufällige Punkte (z, x) aus mask mit Mindestabstand (Gitter-Jitter-Verfahren)."""
    rng = rng or w.rng
    zs, xs = np.nonzero(mask)
    if len(zs) == 0:
        return []
    idx = rng.permutation(len(zs))
    pts = []
    cell = max(1, min_dist)
    taken = set()
    for i in idx:
        z, x = int(zs[i]), int(xs[i])
        key = (z // cell, x // cell)
        if key in taken:
            continue
        taken.add(key)
        pts.append((z, x))
        if len(pts) >= n:
            break
    return pts


# --------------------------------------------------------------------------
# Ausbau-Helfer (Räume, Fenster, Brücken)
# --------------------------------------------------------------------------
def carve_room(w, x0, y0, z0, x1, y1, z1, floor="spruce_planks", light="lantern", wall=None, shelf=None,
               round_=True):
    """Hohler Raum im Fels: Luft innen, Boden aus floor, Lichter im Raster."""
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    rx, ry, rz = (x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2
    if round_:
        w.ellipsoid(cx, cy + ry * 0.35, cz, rx + 0.5, ry * 1.35, rz + 0.5, 0, noise=0.12, seed=int(x0 + z0))
        w.box(x0, y0, z0, x1, y1, z1, 0)
    else:
        w.box(x0, y0, z0, x1, y1, z1, 0)
    w.box(x0, y0 - 1, z0, x1, y0 - 1, z1, B(floor))
    if light:
        for lx in range(int(x0) + 3, int(x1) - 1, 6):
            for lz in range(int(z0) + 3, int(z1) - 1, 6):
                w.set(lx, y0, lz, B(light))
    if shelf:
        for lx in range(int(x0), int(x1) + 1):
            for yy in range(y0, y0 + 3):
                w.set(lx, yy, z0, B(shelf))
                w.set(lx, yy, z1, B(shelf))


def bridge(w, p0, p1, sag=4.0, deck="spruce_planks", rail="spruce_fence", width=3):
    """Hängebrücke zwischen zwei Punkten (x,y,z) mit Durchhang."""
    p0 = np.array(p0, float)
    p1 = np.array(p1, float)
    d = p1 - p0
    L = np.hypot(d[0], d[2])
    n = int(L * 2) + 2
    perp = np.array([-d[2], 0, d[0]]) / max(L, 1e-6)
    half = width // 2
    for t in np.linspace(0, 1, n):
        p = p0 + d * t
        p[1] -= sag * 4 * t * (1 - t)
        for k in range(-half, half + 1):
            q = p + perp * k
            w.set(q[0], np.floor(p[1]), q[2], B(deck))
        for k in (-half - 1, half + 1):
            q = p + perp * k
            w.set(q[0], np.floor(p[1]) + 1, q[2], B(rail), only_air=True)
            w.set(q[0], np.floor(p[1]), q[2], B(deck))


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
def _w_str(out, s):
    b = s.encode("utf-8")
    out.write(struct.pack(">H", len(b)))
    out.write(b)


def _w_payload(out, t, v):
    if t == 1:
        out.write(struct.pack(">b", v))
    elif t == 2:
        out.write(struct.pack(">h", v))
    elif t == 3:
        out.write(struct.pack(">i", v))
    elif t == 4:
        out.write(struct.pack(">q", v))
    elif t == 7:
        out.write(struct.pack(">i", len(v)))
        out.write(bytes(v))
    elif t == 8:
        _w_str(out, v)
    elif t == 9:
        et, items = v
        out.write(struct.pack(">bi", et, len(items)))
        for it in items:
            _w_payload(out, et, it)
    elif t == 10:
        for k, (tt, vv) in v.items():
            out.write(struct.pack(">b", tt))
            _w_str(out, k)
            _w_payload(out, tt, vv)
        out.write(b"\x00")
    elif t == 11:
        a = np.asarray(v, ">i4")
        out.write(struct.pack(">i", len(a)))
        out.write(a.tobytes())
    elif t == 12:
        a = np.asarray(v, ">i8")
        out.write(struct.pack(">i", len(a)))
        out.write(a.tobytes())
    else:
        raise ValueError(t)


def write_nbt(path, root_name, compound):
    buf = io.BytesIO()
    buf.write(b"\x0a")
    _w_str(buf, root_name)
    _w_payload(buf, 10, compound)
    with gzip.open(path, "wb", compresslevel=6) as f:
        f.write(buf.getvalue())


def _parse_state(state):
    if "[" in state:
        name, props = state[:-1].split("[", 1)
        p = dict(kv.split("=") for kv in props.split(","))
    else:
        name, p = state, {}
    return name, p


def compact_palette(b):
    used = np.unique(b)
    if used[0] != 0:
        used = np.concatenate([[0], used])
    remap = np.zeros(256, np.uint8)
    remap[used] = np.arange(len(used), dtype=np.uint8)
    return used, remap[b]


def export_schem(w, path, name):
    used, local = compact_palette(w.b)
    assert len(used) < 128
    palette = {BLOCKS[g]["state"]: (3, i) for i, g in enumerate(used)}
    comp = {
        "Version": (3, 2),
        "DataVersion": (3, DATA_VERSION),
        "Width": (2, w.W),
        "Height": (2, w.H),
        "Length": (2, w.D),
        "Offset": (11, [0, 0, 0]),
        "PaletteMax": (3, len(used)),
        "Palette": (10, palette),
        "BlockData": (7, local.tobytes()),
        "BlockEntities": (9, (10, [])),
        "Metadata": (10, {"Name": (8, name), "Author": (8, "Handy-Claude.Projekte")}),
    }
    write_nbt(path, "Schematic", comp)


def export_litematic(w, path, name, desc):
    used, local = compact_palette(w.b)
    n = len(used)
    bits = max(2, (n - 1).bit_length())
    flat = local.reshape(-1)
    N = flat.size
    bitmat = np.unpackbits(flat[:, None], axis=1, bitorder="little")[:, :bits]
    stream = bitmat.reshape(-1)
    pad = (-stream.size) % 64
    if pad:
        stream = np.concatenate([stream, np.zeros(pad, np.uint8)])
    longs = np.packbits(stream, bitorder="little").view("<u8").astype(np.uint64).view(np.int64)
    pal = []
    for g in used:
        nm, props = _parse_state(BLOCKS[g]["state"])
        c = {"Name": (8, nm)}
        if props:
            c["Properties"] = (10, {k: (8, v) for k, v in props.items()})
        pal.append(c)
    now = int(time.time() * 1000)
    total_blocks = int(np.count_nonzero(w.b))
    region = {
        "Position": (10, {"x": (3, 0), "y": (3, 0), "z": (3, 0)}),
        "Size": (10, {"x": (3, w.W), "y": (3, w.H), "z": (3, w.D)}),
        "BlockStatePalette": (9, (10, pal)),
        "BlockStates": (12, longs),
        "TileEntities": (9, (10, [])),
        "Entities": (9, (10, [])),
        "PendingBlockTicks": (9, (10, [])),
        "PendingFluidTicks": (9, (10, [])),
    }
    comp = {
        "MinecraftDataVersion": (3, DATA_VERSION),
        "Version": (3, 6),
        "SubVersion": (3, 1),
        "Metadata": (10, {
            "Name": (8, name),
            "Author": (8, "Handy-Claude.Projekte"),
            "Description": (8, desc),
            "RegionCount": (3, 1),
            "TotalVolume": (3, int(N)),
            "TotalBlocks": (3, total_blocks),
            "TimeCreated": (4, now),
            "TimeModified": (4, now),
            "EnclosingSize": (10, {"x": (3, w.W), "y": (3, w.H), "z": (3, w.D)}),
        }),
        "Regions": (10, {name: (10, region)}),
    }
    write_nbt(path, "", comp)


def material_list(w):
    exp = w.exposed_surface()
    counts = {}
    vis = np.bincount(w.b[exp].ravel(), minlength=256)
    small = ~OCCLUDES[w.b] & (w.b != 0) & (KIND[w.b] != 2)
    sm = np.bincount(w.b[small].ravel(), minlength=256)
    tot = np.bincount(w.b.ravel(), minlength=256)
    for g in range(len(BLOCKS)):
        v = int(vis[g] + sm[g])
        if v and BLOCKS[g]["kind"] != 2:
            counts[BLOCKS[g]["key"]] = dict(sichtbar=v, gesamt=int(tot[g]))
    water = int(tot[ID["water"]])
    return dict(bloecke=counts, wasser=water, gesamt=int(np.count_nonzero(w.b) - water),
                sichtbar=int(sum(c["sichtbar"] for c in counts.values())))


def export_viewer(w, path_txt):
    """Volumen für den Viewer: zlib-komprimiert und Base64-kodiert (als .txt, damit es überall ausgeliefert wird)."""
    import base64
    comp = zlib.compress(w.b.tobytes(), 9)
    with open(path_txt, "w") as f:
        f.write(base64.b64encode(comp).decode("ascii"))
    return len(comp)


def export_palette_json(path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([dict(key=b["key"], state=b["state"], color=b["color"], kind=b["kind"], glow=b["glow"],
                        de=b["de"]) for b in BLOCKS], f, ensure_ascii=False)


# --------------------------------------------------------------------------
# Wege und Linien in der Draufsicht
# --------------------------------------------------------------------------
def polyline_dist(X, Z, pts):
    """Abstand jedes (x,z)-Punkts zum Linienzug pts=[(x,z),...]."""
    best = np.full(X.shape, 1e9)
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        t = np.clip(((X - ax) * dx + (Z - az) * dz) / max(L2, 1e-9), 0, 1)
        px, pz = ax + t * dx, az + t * dz
        best = np.minimum(best, np.hypot(X - px, Z - pz))
    return best


def smooth_polyline(pts, n=8):
    """Catmull-Rom-Glättung eines Linienzugs."""
    p = np.array(pts, float)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return [tuple(q) for q in out]


GROUNDS = None


def paint_path(w, pts, width=1.5, blk="dirt_path", allowed=("grass", "moss", "coarse_dirt", "podzol", "dirt"),
               lanterns=0):
    """Malt einen Weg auf die Oberfläche; optional Laternenpfähle alle `lanterns` Blöcke."""
    dist = polyline_dist(w.X, w.Z, pts)
    top = w.column_top()
    allowed_ids = [B(a) for a in allowed]
    zz, xx = np.nonzero(dist <= width)
    for z, x in zip(zz, xx):
        y = top[z, x]
        if y >= 0 and w.b[y, z, x] in allowed_ids:
            w.b[y, z, x] = B(blk)
    if lanterns:
        sp = smooth_polyline(pts, 12)
        acc = 0.0
        side = 1
        for (ax, az), (bx, bz) in zip(sp[:-1], sp[1:]):
            seg = np.hypot(bx - ax, bz - az)
            acc += seg
            if acc >= lanterns:
                acc = 0.0
                nx, nz = -(bz - az) / max(seg, 1e-6), (bx - ax) / max(seg, 1e-6)
                px, pz = int(round(bx + nx * (width + 1.5) * side)), int(round(bz + nz * (width + 1.5) * side))
                side = -side
                if 0 <= px < w.W and 0 <= pz < w.D:
                    y = top[pz, px]
                    if y > 0 and OCCLUDES[w.b[y, pz, px]]:
                        w.set(px, y + 1, pz, B("spruce_fence"))
                        w.set(px, y + 2, pz, B("spruce_fence"))
                        w.set(px, y + 3, pz, B("lantern"))


def arch(w, p0, p1, height, thick, blk="stone"):
    """Natürlicher Felsbogen zwischen zwei Fußpunkten (x,y,z)."""
    p0 = np.array(p0, float)
    p1 = np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    n = int(L * 1.5) + 4
    for t in np.linspace(0, 1, n):
        c = p0 + (p1 - p0) * t
        c[1] += height * np.sin(np.pi * t)
        r = thick * (1.0 + 0.9 * (1 - np.sin(np.pi * t)) ** 2)
        w.ellipsoid(c[0], c[1], c[2], r, r * 0.8, r, B(blk), noise=0.25, seed=int(t * 100))


def retexture(w, x0, y0, z0, x1, y1, z1, src, mix, rng=None):
    """Mischt in einem Bereich Blöcke src zufällig mit mix=[(block, anteil), ...]."""
    rng = rng or w.rng
    bb = w._bbox(x0, y0, z0, x1, y1, z1)
    if bb is None:
        return
    a0, b0, c0, a1, b1, c1 = bb
    sub = w.b[b0:b1, c0:c1, a0:a1]
    m = np.isin(sub, [B(s) for s in src])
    r = rng.random(sub.shape)
    acc = 0.0
    for blk, p in mix:
        sel = m & (r >= acc) & (r < acc + p)
        sub[sel] = B(blk)
        acc += p


def green_tops(w, mask2d=None, blk="grass", rocks=("stone", "andesite", "tuff", "calcite", "granite", "diorite"),
               p=1.0, max_slope=None):
    """Setzt Gras/Moos auf freiliegende Felsoberseiten (z. B. auf Bögen und Säulen)."""
    rock_ids = np.array([B(r) for r in rocks])
    b = w.b
    is_rock = np.isin(b[:-1], rock_ids)
    above_air = b[1:] == 0
    m = is_rock & above_air
    if mask2d is not None:
        m &= mask2d[None]
    if p < 1.0:
        m &= w.rng.random(m.shape) < p
    b[:-1][m] = B(blk)


# --------------------------------------------------------------------------
# Felsnadeln, schwebende Inseln, Lianen, Durchgänge
# --------------------------------------------------------------------------
def pillar(w, cx, cz, base_y, height, r0, seed=0, rough=0.22, rocks=("stone", "andesite", "stone", "tuff"),
           moss=0.42, taper=0.3, top_soil=True):
    """Hohe Felsnadel mit unregelmäßigem Querschnitt, senkrechten Gesteinsstreifen und Moosbändern.
    Gibt eine Funktion radius(y) (mittlerer Radius) zurück."""
    top_y = base_y + height
    R = r0 * 1.9 + 4
    bb = w._bbox(cx - R, base_y - 8, cz - R, cx + R, top_y + 3, cz + R)
    if bb is None:
        return None
    x0, y0, z0, x1, y1, z1 = bb
    Y, Zg, Xg = np.meshgrid(np.arange(y0, y1, dtype=float), np.arange(z0, z1, dtype=float),
                            np.arange(x0, x1, dtype=float), indexing="ij")
    dx, dz = Xg - cx, Zg - cz
    dist = np.hypot(dx, dz)
    th = np.arctan2(dz, dx)
    t = np.clip((Y - base_y) / height, 0, 1)
    ph = (seed % 97) * 0.37

    def prof(tt, yy):
        return (r0 * (1 - taper * tt + 0.1 * np.sin(tt * np.pi * 2.6 + ph))
                + r0 * 0.7 * np.exp(-np.maximum(yy - base_y, 0) / 7.0))
    rp = prof(t, Y)
    n = fbm3(np.cos(th) * 2.4 + ph, Y / 16.0, np.sin(th) * 2.4 - ph, 1.0, 3, seed)
    rr = rp * (1 + rough * n)
    topn = top_y + noise2(Xg[0] / 9.0, Zg[0] / 9.0, seed + 3)[None] * 2.5 - (dist / np.maximum(rr, 1)) ** 2 * 3
    solid = (dist <= rr) & (Y <= topn)
    stripe = np.floor(th * np.maximum(rp, 1) / 3.2 + n * 2.5).astype(np.int64) % len(rocks)
    ids = np.array([B(r) for r in rocks], np.uint8)
    blk = ids[stripe]
    mn = noise3(Xg / 7.0, Y / 5.0, Zg / 7.0, seed + 11)
    blk = np.where(mn > moss, B("moss"), blk)
    depth_top = topn - Y
    if top_soil:
        blk = np.where(depth_top < 1, B("grass"), np.where(depth_top < 4, B("dirt"), blk))
    sub = w.b[y0:y1, z0:z1, x0:x1]
    sub[solid] = blk[solid]

    def radius_at(y):
        tt = np.clip((y - base_y) / height, 0, 1)
        return float(prof(tt, y))
    return radius_at


def radial_surface(w, cx, cz, y, ang, rmax=80):
    """Erste Luftposition, wenn man von der Achse (cx,cz) in Richtung ang nach außen läuft."""
    c, s = np.cos(ang), np.sin(ang)
    inside = False
    for r in np.arange(0, rmax, 0.5):
        x, z = int(round(cx + c * r)), int(round(cz + s * r))
        if not w.inside(x, y, z):
            return None
        solid = OCCLUDES[w.b[y, z, x]]
        if solid:
            inside = True
        elif inside:
            return (x, z, r)
    return None


def vine_curtain(w, cx, cz, y_top, length, ang, leaf="azalea_leaves", width=2):
    """Lianenvorhang, der an einer Felswand herabhängt."""
    for k in range(width):
        a = ang + k * 0.035
        for y in range(int(y_top), int(y_top - length), -1):
            p = radial_surface(w, cx, cz, y, a)
            if p is None:
                break
            if w.rng.random() < 0.88:
                w.set(p[0], y, p[1], B(leaf), only_air=True)


def float_island(w, cx, cy, cz, rx, rz, depth, seed=0, top="grass", hang=True):
    """Schwebende Insel: flache Oberseite, kegelförmige, zerklüftete Unterseite."""
    bb = w._bbox(cx - rx - 3, cy - depth - 4, cz - rz - 3, cx + rx + 3, cy + 6, cz + rz + 3)
    if bb is None:
        return None
    x0, y0, z0, x1, y1, z1 = bb
    Zg, Xg = np.meshgrid(np.arange(z0, z1, dtype=float), np.arange(x0, x1, dtype=float), indexing="ij")
    e = np.hypot((Xg - cx) / rx, (Zg - cz) / rz) + fbm2(Xg, Zg, 14, 3, seed) * 0.18
    inside = e < 1
    topy = cy + fbm2(Xg, Zg, 20, 3, seed + 1) * 3 + (1 - np.clip(e, 0, 1)) * 2
    k = np.clip(1 - e, 0, 1)
    boty = cy - depth * (k ** 0.75) * (0.75 + 0.5 * (fbm2(Xg, Zg, 6, 2, seed + 2) * 0.5 + 0.5)) - 1
    boty = boty - np.maximum(0, fbm2(Xg, Zg, 3.5, 2, seed + 11)) * depth * 0.45 * k
    for y in range(y0, y1):
        m = inside & (y <= topy) & (y >= boty)
        if not m.any():
            continue
        d = topy - y
        band = (np.floor((y + fbm2(Xg, Zg, 10, 2, seed + 7) * 3) / 3).astype(int)) % 5
        rocks = np.array([B("stone"), B("andesite"), B("stone"), B("tuff"), B("granite") if seed % 2 else B("stone")],
                         np.uint8)
        blk = np.where(d < 1, B(top), np.where(d < 4, B("dirt"), rocks[band]))
        sub = w.b[y, z0:z1, x0:x1]
        sub[m] = blk[m]
    if hang:
        zz, xx = np.nonzero(inside & (k > 0.15))
        sel = w.rng.random(len(zz)) < 0.035
        for z, x in zip(zz[sel], xx[sel]):
            yb = int(np.floor(boty[z, x]))
            L = int(w.rng.integers(2, 9))
            blk = B("hanging_roots") if w.rng.random() < 0.6 else B("mangrove_roots")
            for y in range(yb - 1, yb - 1 - L, -1):
                w.set(x + x0, y, z + z0, blk, only_air=True)
    return (inside, topy, x0, z0)


def tunnel_out(w, start, toward, width=3, height=4, floor="spruce_planks", max_len=60):
    """Gräbt von start (x,y,z) waagerecht Richtung toward (x,z) aus dem Fels heraus.
    Gibt den Austrittspunkt (erster Punkt draußen) zurück."""
    sx, sy, sz = start
    d = np.array([toward[0] - sx, toward[1] - sz], float)
    d /= max(np.linalg.norm(d), 1e-6)
    px, pz = -d[1], d[0]
    outside_run = 0
    last = None
    for s in np.arange(0, max_len, 0.5):
        cx, cz = sx + d[0] * s, sz + d[1] * s
        was_solid = False
        for k in range(-(width // 2), width // 2 + 1):
            x, z = int(round(cx + px * k)), int(round(cz + pz * k))
            for y in range(sy, sy + height):
                if w.inside(x, y, z) and OCCLUDES[w.b[y, z, x]]:
                    was_solid = True
                    w.b[y, z, x] = 0
            if w.inside(x, sy - 1, z) and (OCCLUDES[w.b[sy - 1, z, x]] or s < 3):
                w.b[sy - 1, z, x] = B(floor)
        if not was_solid and s > 2:
            outside_run += 1
            if outside_run >= 2:
                return (cx, sy - 1, cz)
        else:
            outside_run = 0
        last = (cx, sy - 1, cz)
    return last
