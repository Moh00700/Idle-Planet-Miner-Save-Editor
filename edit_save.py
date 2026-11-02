#!/usr/bin/env python3
"""
Idle Planet Miner save editor  (playerInfo.dat, .NET BinaryFormatter)

Usage:
    python3 edit_save.py playerInfo.dat                 -> writes playerInfo_modded.dat
    python3 edit_save.py in.dat out.dat                 -> writes out.dat
    python3 edit_save.py in.dat --dump                  -> prints every field and its value
    python3 edit_save.py in.dat --export cfg.json       -> writes CURRENT values of all editable fields
    python3 edit_save.py in.dat out.dat --config cfg.json -> applies your edited cfg.json (instead of SETTINGS)

Array values (ARRAYS / "arrays" in the JSON) can be given three ways:
    'resourceCount': 1e12                       every slot gets this value
    'resourceCount': {0: 500, 5: 1e9}           only slots 0 and 5 change (JSON keys: "0", "5")
    'planetUnlocked': [True, True, False, ...]  one value per slot (None = leave that slot alone)
Slot numbers start at 0.  Resources: slot = resource id (ores/alloys/items share one list of 120).
Planets: 79 slots.  Use --export to see exactly what each list holds right now.

Edit the SETTINGS block below, then run.  ALWAYS back up your original save first.
Edits are done in place (same file size), so the file structure stays valid.
Set any value to None to skip that edit.
"""
import struct, sys, os

# ============================== SETTINGS ====================================
SCALARS = {
    # --- currencies ---
    'cash': 1e25,                  # double
    'credits': 1e12,               # double
    'darkMatter': 1_000_000,
    'energyCell': 100_000,
    'holoBolts': 100_000,
    'prestigeCurrency': 100_000,
    'tokens': 100_000,
    'drillFragments': 100_000,
    'transportFragments': 100_000,
    'synthFragments': 100_000,
    'remoteFragments': 100_000,
    'moduleRerollCurrency': 100_000,
    # --- progression ---
    'bestPlanetUnlockedEver': 78,
    'smeltersUnlocked': 10,
    'craftersUnlocked': 10,
    'maxSlots': 6,                 # manager slots
    # --- ads ---
    'disableAdsUnlockedBool': True,
    # --- tutorials ---
    'tutorialCompleteBool1': True, 'tutorialCompleteBool2': True,
    'tutorialCompleteBool3': True, 'tutorialCompleteBool4': True,
    'tutorialCompleteBool5': True, 'tutorialCompleteBool6': True,
    'tutorialCompleteBool7': True,
    'spaceStationTutorialComplete': True,
    'moduleSystemTutorialComplete': True,
    'moduleSystemProjectUnlockRewardTutorialComplete': True,
}

# Every element of these arrays is set to the given value.
ARRAYS = {
    # planets (79 slots)
    'planetUnlocked': True,
    'miningSpeedLevel': 100,
    'speedLevel': 100,
    'cargoLevel': 100,
    # resources (120 slots)
    'resourceDiscovered': True,
    'resourceCount': 1e12,         # float32. Per-resource example: {0: 5e6, 1: 1e3, 30: 250}
    # projects
    'projectAvailableBool': True,
    'projectUnlockedBool': True,
    # smelting / crafting / shipments
    'recipeUnlocked': True,
    'alternateSmeltRecipeUnlocked': True,
    'craftRecipeUnlocked': True,
    'alternateCraftRecipeUnlocked': True,
    'shipmentUnlocked': True,
    # tutorial dialogues
    'dialogueShownSavebool': True,
}
# ============================================================================

PR = {1: ('?', 1), 2: ('B', 1), 3: ('H', 2), 6: ('d', 8), 7: ('h', 2), 8: ('i', 4),
      9: ('q', 8), 10: ('b', 1), 11: ('f', 4), 12: ('q', 8), 13: ('q', 8),
      14: ('H', 2), 15: ('I', 4), 16: ('Q', 8)}


class Parser:
    def __init__(self, data):
        self.d, self.p, self.classes = data, 0, {}
        self.fields, self.arrays = {}, {}

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v

    def i32(self):
        v = struct.unpack_from('<i', self.d, self.p)[0]; self.p += 4; return v

    def lps(self):
        n = s = 0
        while True:
            b = self.u8(); n |= (b & 0x7f) << s; s += 7
            if not b & 0x80: break
        v = self.d[self.p:self.p + n].decode(); self.p += n; return v

    def prim(self, t):
        if t in (5, 18): return ('s', self.lps(), self.p)
        f, sz = PR[t]; off = self.p
        v = struct.unpack_from('<' + f, self.d, off)[0]; self.p += sz
        return (f, v, off)

    def meta(self):
        c = self.i32()
        names = [self.lps() for _ in range(c)]
        types = [self.u8() for _ in range(c)]
        info = []
        for t in types:
            if t in (0, 7): info.append(self.u8())
            elif t == 3: info.append(self.lps())
            elif t == 4: info.append((self.lps(), self.i32()))
            else: info.append(None)
        return names, types, info

    def members(self, names, types, info):
        out = []
        for n, t, i in zip(names, types, info):
            if t == 0:
                f, v, off = self.prim(i)
                out.append((n, dict(k='prim', f=f, v=v, off=off)))
            else:
                out.append((n, self.record()))
        return out

    def record(self):
        r = self.u8(); d = self.d
        if r == 0x0f:
            oid = self.i32(); ln = self.i32(); pt = self.u8(); f, sz = PR[pt]
            a = dict(k='parr', id=oid, len=ln, f=f, sz=sz, data=self.p,
                     vals=list(struct.unpack_from('<%d%s' % (ln, f), d, self.p)))
            self.p += ln * sz; return a
        if r == 0x09: return dict(k='ref', id=self.i32())
        if r == 0x0a: return dict(k='null', n=1)
        if r == 0x0d: return dict(k='nulls', n=self.u8())
        if r == 0x0e: return dict(k='nulls', n=self.i32())
        if r == 0x06: self.i32(); return dict(k='str', v=self.lps())
        if r in (0x10, 0x11):
            self.i32(); ln = self.i32(); k = 0
            while k < ln:
                it = self.record(); k += it['n'] if it['k'] == 'nulls' else 1
            return dict(k='oarr')
        if r == 0x07:
            self.i32(); at = self.u8(); rank = self.i32()
            lens = [self.i32() for _ in range(rank)]
            if at >= 3: [self.i32() for _ in range(rank)]
            t = self.u8()
            ai = self.u8() if t in (0, 7) else self.lps() if t == 3 else \
                 (self.lps(), self.i32()) if t == 4 else None
            tot = 1
            for l in lens: tot *= l
            if t == 0:
                f, sz = PR[ai]; s0 = self.p
                a = dict(k='parr', len=tot, f=f, sz=sz, data=s0,
                         vals=list(struct.unpack_from('<%d%s' % (tot, f), d, s0)))
                self.p += tot * sz; return a
            k = 0
            while k < tot:
                it = self.record(); k += it['n'] if it['k'] == 'nulls' else 1
            return dict(k='barr')
        if r in (0x04, 0x05):
            oid = self.i32(); name = self.lps(); m = self.meta()
            if r == 0x05: self.i32()
            self.classes[oid] = m
            return dict(k='obj', id=oid, vals=self.members(*m))
        if r == 0x01:
            oid = self.i32(); ref = self.i32(); self.classes[oid] = self.classes[ref]
            return dict(k='obj', id=oid, vals=self.members(*self.classes[ref]))
        raise ValueError('unsupported record 0x%x at %d' % (r, self.p - 1))

    def parse(self):
        assert self.u8() == 0
        for _ in range(4): self.i32()
        while self.d[self.p] == 0x0c: self.p += 1; self.i32(); self.lps()
        assert self.u8() == 5, 'not a class record'
        self.i32(); self.cls = self.lps(); m = self.meta(); self.i32()
        self.fields = dict(self.members(*m))
        while self.p < len(self.d) and self.d[self.p] != 0x0b:
            oid = struct.unpack_from('<i', self.d, self.p + 1)[0]
            rec = self.record(); self.arrays[oid] = rec


def pick(val, i, cur):
    """Resolve the value for slot i from a scalar, list, or {index: value} dict."""
    if isinstance(val, dict):
        return val.get(i, val.get(str(i), cur))
    if isinstance(val, (list, tuple)):
        return val[i] if i < len(val) and val[i] is not None else cur
    return val


def main():
    skip = {sys.argv.index(f) + 1 for f in ('--export', '--config') if f in sys.argv}
    args = [a for i, a in enumerate(sys.argv) if i > 0 and not a.startswith('--') and i not in skip]
    if not args:
        print(__doc__); sys.exit(1)
    src = args[0]
    dst = args[1] if len(args) > 1 else os.path.splitext(src)[0] + '_modded.dat'
    data = bytearray(open(src, 'rb').read())
    P = Parser(bytes(data)); P.parse()
    print('Parsed %s: %d fields, %d array records' % (P.cls, len(P.fields), len(P.arrays)))

    if '--dump' in sys.argv:
        for n, r in P.fields.items():
            if r['k'] == 'prim': print(n, '=', r['v'])
            elif r['k'] == 'ref' and r['id'] in P.arrays and P.arrays[r['id']]['k'] == 'parr':
                a = P.arrays[r['id']]; print(n, '[%d] =' % a['len'], a['vals'][:10])
        return

    global SCALARS, ARRAYS
    if '--export' in sys.argv:
        import json
        out = sys.argv[sys.argv.index('--export') + 1]
        cfg = {'scalars': {}, 'arrays': {}}
        for n in SCALARS:
            r = P.fields.get(n)
            if r and r['k'] == 'prim': cfg['scalars'][n] = r['v']
        for n in ARRAYS:
            r = P.fields.get(n)
            a = P.arrays.get(r['id']) if r and r['k'] == 'ref' else None
            if a and a['k'] == 'parr': cfg['arrays'][n] = a['vals']
        json.dump(cfg, open(out, 'w'), indent=1)
        print('Wrote current values to', out); return
    if '--config' in sys.argv:
        import json
        cfg = json.load(open(sys.argv[sys.argv.index('--config') + 1]))
        SCALARS, ARRAYS = cfg.get('scalars', {}), cfg.get('arrays', {})

    n_done = 0
    for name, val in SCALARS.items():
        if val is None: continue
        r = P.fields.get(name)
        if not r or r['k'] != 'prim' or r['f'] == 's':
            print('  skip (not found):', name); continue
        struct.pack_into('<' + r['f'], data, r['off'], val); n_done += 1
    for name, val in ARRAYS.items():
        if val is None: continue
        r = P.fields.get(name)
        a = P.arrays.get(r['id']) if r and r['k'] == 'ref' else None
        if not a or a['k'] != 'parr':
            print('  skip (not found):', name); continue
        for i in range(a['len']):
            v = pick(val, i, a['vals'][i])
            if a['f'] == '?': v = bool(v)
            elif a['f'] not in 'fd': v = int(v)
            struct.pack_into('<' + a['f'], data, a['data'] + i * a['sz'], v)
        n_done += 1
    assert len(data) == os.path.getsize(src)
    open(dst, 'wb').write(data)
    print('Applied %d edits -> %s' % (n_done, dst))


if __name__ == '__main__':
    main()
