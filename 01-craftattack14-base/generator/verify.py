"""Liest die exportierten .schem- und .litematic-Dateien zurück und vergleicht sie mit den Viewer-Daten.

Aufruf:  python3 verify.py
"""
import base64
import glob
import gzip
import json
import os
import struct
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class R:
    def __init__(self, b):
        self.b = b
        self.i = 0

    def take(self, n):
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def u(self, fmt):
        n = struct.calcsize(fmt)
        return struct.unpack(fmt, self.take(n))[0]

    def string(self):
        return self.take(self.u(">H")).decode("utf-8")

    def payload(self, t):
        if t == 1:
            return self.u(">b")
        if t == 2:
            return self.u(">h")
        if t == 3:
            return self.u(">i")
        if t == 4:
            return self.u(">q")
        if t == 5:
            return self.u(">f")
        if t == 6:
            return self.u(">d")
        if t == 7:
            return np.frombuffer(self.take(self.u(">i")), np.uint8)
        if t == 8:
            return self.string()
        if t == 9:
            et = self.u(">b")
            n = self.u(">i")
            return [self.payload(et) for _ in range(n)]
        if t == 10:
            out = {}
            while True:
                tt = self.u(">b")
                if tt == 0:
                    return out
                k = self.string()
                out[k] = self.payload(tt)
        if t == 11:
            n = self.u(">i")
            return np.frombuffer(self.take(4 * n), ">i4")
        if t == 12:
            n = self.u(">i")
            return np.frombuffer(self.take(8 * n), ">i8")
        raise ValueError(t)


def read_nbt(path):
    r = R(gzip.open(path).read())
    assert r.u(">b") == 10
    r.string()
    return r.payload(10)


def state_str(name, props):
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]"


def main():
    pal = json.load(open(os.path.join(ROOT, "viewer", "data", "palette.json")))
    ok = True
    for meta_path in sorted(glob.glob(os.path.join(ROOT, "viewer", "data", "*.json"))):
        if meta_path.endswith("palette.json"):
            continue
        meta = json.load(open(meta_path))
        slug = meta["slug"]
        Wd, Hd, Dd = meta["size"]
        vol = np.frombuffer(zlib.decompress(base64.b64decode(open(meta_path[:-5] + ".txt").read())), np.uint8)
        gid = {p["state"]: i for i, p in enumerate(pal)}
        folder = glob.glob(os.path.join(ROOT, "landschaften", f"*-{slug}"))[0]
        # .schem: Palette-Index -> globale ID, dann vergleichen
        s = read_nbt(os.path.join(folder, slug + ".schem"))
        assert (s["Width"], s["Height"], s["Length"]) == (Wd, Hd, Dd), "schem size"
        lut = np.zeros(256, np.uint8)
        for k, v in s["Palette"].items():
            lut[v] = gid[k]
        e1 = int(np.count_nonzero(lut[s["BlockData"]] != vol))
        # .litematic: gepackte Bits blockweise entpacken
        l = read_nbt(os.path.join(folder, slug + ".litematic"))
        reg = list(l["Regions"].values())[0]
        lp = [state_str(c["Name"], c.get("Properties")) for c in reg["BlockStatePalette"]]
        lut2 = np.array([gid[k] for k in lp], np.uint8)
        n = len(lp)
        bits = max(2, (n - 1).bit_length())
        longs = np.concatenate([reg["BlockStates"].astype(np.int64).view(np.uint64), np.zeros(1, np.uint64)])
        N = Wd * Hd * Dd
        e2 = 0
        mask = np.uint64((1 << bits) - 1)
        for a in range(0, N, 1 << 22):
            i = np.arange(a, min(N, a + (1 << 22)), dtype=np.uint64)
            start = i * np.uint64(bits)
            word = (start >> np.uint64(6)).astype(np.int64)
            off = start & np.uint64(63)
            lo = longs[word] >> off
            hi = np.where(off + np.uint64(bits) > np.uint64(64),
                          longs[word + 1] << ((np.uint64(64) - off) & np.uint64(63)), np.uint64(0))
            vals = ((lo | hi) & mask).astype(np.int64)
            e2 += int(np.count_nonzero(lut2[vals] != vol[a:a + len(i)]))
        size = reg["Size"]
        print(f"{slug:24s} {Wd}x{Hd}x{Dd}  schem-Fehler {e1}  litematic-Fehler {e2}  Palette {n}  "
              f"Größe {size['x']}x{size['y']}x{size['z']}")
        ok &= e1 == 0 and e2 == 0
    print("ALLES OK" if ok else "FEHLER")


if __name__ == "__main__":
    main()
