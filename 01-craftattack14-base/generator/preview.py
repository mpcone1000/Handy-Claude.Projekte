"""Schnelle 2D-Vorschauen (Draufsicht mit Schattierung, Querschnitte) zum Prüfen der Generatoren."""
import numpy as np
from PIL import Image

from mclib import BLOCKS, KIND

COL = np.array([[int(b["color"][i:i + 2], 16) for i in (1, 3, 5)] for b in BLOCKS], np.float64)


def topdown(w, path, scale=2):
    b = w.b
    H = b.shape[0]
    nonair = (b != 0)
    top = H - 1 - np.argmax(nonair[::-1], axis=0)
    zz, xx = np.indices(top.shape)
    blk = b[top, zz, xx]
    col = COL[blk].copy()
    # Wasser: Untergrund durchscheinen lassen
    water = KIND[blk] == 2
    solid = (KIND[b] != 2) & nonair
    stop = H - 1 - np.argmax(solid[::-1], axis=0)
    under = COL[b[stop, zz, xx]]
    depth = np.clip((top - stop) / 12.0, 0, 1)[..., None]
    wc = np.array([60, 140, 200], float)
    col = np.where(water[..., None], under * (1 - depth) * 0.6 + wc * (0.4 + 0.6 * depth), col)
    h = top.astype(float)
    gx = np.gradient(h, axis=1)
    gz = np.gradient(h, axis=0)
    shade = np.clip(1.0 + (-gx - gz) * 0.12, 0.45, 1.35)
    hfac = 0.75 + 0.35 * (h / H)
    col = col * shade[..., None] * hfac[..., None]
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(path)


def section(w, path, x=None, z=None, scale=2):
    b = w.b
    if x is not None:
        sl = b[:, :, x]  # [y, z]
    else:
        sl = b[:, z, :]  # [y, x]
    col = COL[sl].copy()
    col[sl == 0] = [235, 240, 245]
    img = Image.fromarray(np.clip(col[::-1], 0, 255).astype(np.uint8))
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(path)
