# Tiny z-buffer renderer for parts made of axis-aligned boxes (union of adds minus subs).
# Technical-illustration look: flat shaded faces, white melamine skins, tan particleboard core,
# outlines from part / plane id discontinuities (no seam lines across coplanar cells).
import numpy as np
from PIL import Image

LINE = np.array([38, 38, 44], np.float32)

BASE = {
    'mel': (247, 247, 244),
    'core': (214, 190, 148),
    'oak': (204, 156, 98),
    'oak_edge': (186, 136, 82),
    'metal': (178, 183, 190),
    'orange': (243, 124, 30),
    'nail': (92, 92, 98),
    'dark': (60, 60, 64),
}
SHADE = {(2, 1): 1.00, (2, -1): 0.74, (1, -1): 0.92, (1, 1): 0.90, (0, 1): 0.84, (0, -1): 0.86}


class Part:
    def __init__(self, pid, adds, subs=(), mat='mel', thick_axis=None, offset=(0, 0, 0), name=''):
        self.pid = pid
        self.adds = [tuple(float(v) for v in b) for b in adds]
        self.subs = [tuple(float(v) for v in b) for b in subs]
        self.mat = mat
        self.thick_axis = thick_axis
        self.offset = np.array(offset, float)
        self.name = name
        a = np.array(self.adds)
        self.bbox = np.array([a[:, 0].min(), a[:, 1].max(), a[:, 2].min(),
                              a[:, 3].max(), a[:, 4].min(), a[:, 5].max()])
        self._faces = None

    def moved(self, offset):
        return Part(self.pid, self.adds, self.subs, self.mat, self.thick_axis, offset, self.name)

    def clipped(self, box):
        """Keep only the part inside box (x0,x1,y0,y1,z0,z1) in local coords (for detail views)."""
        adds = []
        for b in self.adds:
            c = (max(b[0], box[0]), min(b[1], box[1]), max(b[2], box[2]),
                 min(b[3], box[3]), max(b[4], box[4]), min(b[5], box[5]))
            if c[0] < c[1] and c[2] < c[3] and c[4] < c[5]:
                adds.append(c)
        p = Part(self.pid, adds, self.subs, self.mat, self.thick_axis, self.offset, self.name)
        p.bbox = self.bbox  # skins stay where the real panel skins are
        return p

    def faces(self):
        if self._faces is not None:
            return self._faces
        boxes = self.adds + self.subs
        g = [np.array(sorted(set([b[2 * a] for b in boxes] + [b[2 * a + 1] for b in boxes])))
             for a in range(3)]
        cx = [(v[:-1] + v[1:]) / 2 for v in g]
        X, Y, Z = np.meshgrid(cx[0], cx[1], cx[2], indexing='ij')

        def inside(b):
            return (X > b[0]) & (X < b[1]) & (Y > b[2]) & (Y < b[3]) & (Z > b[4]) & (Z < b[5])

        fill = np.zeros(X.shape, bool)
        for b in self.adds:
            fill |= inside(b)
        for b in self.subs:
            fill &= ~inside(b)
        out = []
        for (i, j, k) in np.argwhere(fill):
            ijk = [i, j, k]
            for a in range(3):
                for s in (-1, 1):
                    n = list(ijk)
                    n[a] += s
                    if 0 <= n[a] < fill.shape[a] and fill[tuple(n)]:
                        continue
                    coord = g[a][ijk[a] + (1 if s > 0 else 0)]
                    o = [b for b in range(3) if b != a]
                    r0 = (g[o[0]][ijk[o[0]]], g[o[0]][ijk[o[0]] + 1])
                    r1 = (g[o[1]][ijk[o[1]]], g[o[1]][ijk[o[1]] + 1])
                    out.append((a, s, coord, o, r0, r1))
        self._faces = out
        return out

    def face_mat(self, a, coord):
        if self.mat in ('mel', 'oak'):
            t = self.thick_axis
            skin = a == t and (abs(coord - self.bbox[2 * t]) < 1e-6 or abs(coord - self.bbox[2 * t + 1]) < 1e-6)
            if self.mat == 'mel':
                return 'mel' if skin else 'core'
            return 'oak' if skin else 'oak_edge'
        return self.mat


def _mark(lab):
    e = np.zeros(lab.shape, bool)
    e[:, 1:] |= lab[:, 1:] != lab[:, :-1]
    e[1:, :] |= lab[1:, :] != lab[:-1, :]
    return e


def _dilate(m, r):
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o[1:, :] |= out[:-1, :]
        o[:-1, :] |= out[1:, :]
        o[:, 1:] |= out[:, :-1]
        o[:, :-1] |= out[:, 1:]
        out = o
    return out


class View:
    def __init__(self, az, el, px_per_unit, ss=2, pad=24):
        az, el = np.radians(az), np.radians(el)
        self.c = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])
        r = np.cross(-self.c, np.array([0, 0, 1.0]))
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, -self.c)
        self.k = px_per_unit
        self.ss = ss
        self.pad = pad
        self.x0 = self.y0 = 0.0

    def _raw(self, P):
        P = np.asarray(P, float)
        return np.stack([P @ self.r, -(P @ self.u)], -1) * self.k

    def proj(self, P):
        """3D point (world, inches) -> final image pixel (x, y)."""
        q = self._raw(P)
        return q - np.array([self.x0, self.y0])

    def render(self, parts, path, extra=()):
        F, pts = [], []
        for p in parts:
            for (a, s, coord, o, r0, r1) in p.faces():
                n = np.zeros(3)
                n[a] = s
                if n @ self.c <= 1e-9:
                    continue

                def P(v0, v1):
                    q = np.zeros(3)
                    q[a] = coord
                    q[o[0]] = v0
                    q[o[1]] = v1
                    return q + p.offset

                P0, P1, P3, P2 = P(r0[0], r1[0]), P(r0[1], r1[0]), P(r0[0], r1[1]), P(r0[1], r1[1])
                F.append((p, a, s, coord, P0, P1, P3))
                pts += [P0, P1, P2, P3]
        q = self._raw(np.array(pts + [np.asarray(e, float) for e in extra]))
        mn = q.min(0) - self.pad
        mx = q.max(0) + self.pad
        self.x0, self.y0 = mn
        Wf, Hf = int(np.ceil(mx[0] - mn[0])), int(np.ceil(mx[1] - mn[1]))
        ss = self.ss
        Ws, Hs = Wf * ss, Hf * ss
        zb = np.full((Hs, Ws), -np.inf, np.float32)
        plane = np.full((Hs, Ws), -1, np.int32)
        pidb = np.full((Hs, Ws), -1, np.int32)
        col = np.full((Hs, Ws, 3), 255, np.float32)
        rng = np.random.default_rng(7)
        noise = rng.normal(0, 1, (Hs, Ws)).astype(np.float32)
        plane_ids = {}
        for (p, a, s, coord, P0, P1, P3) in F:
            key = (p.pid, a, s, round(float(coord + p.offset[a]), 5))
            pl = plane_ids.setdefault(key, len(plane_ids))
            S = (self._raw(np.array([P0, P1, P3])) - np.array([self.x0, self.y0])) * ss
            s0, e1, e2 = S[0], S[1] - S[0], S[2] - S[0]
            det = e1[0] * e2[1] - e1[1] * e2[0]
            if abs(det) < 1e-6:
                continue
            l1, l2 = max(np.hypot(*e1), 1e-6), max(np.hypot(*e2), 1e-6)
            ta, tb = 0.55 / l1, 0.55 / l2
            d0, d1, d3 = P0 @ self.c, P1 @ self.c, P3 @ self.c
            cs = np.array([S[0], S[1], S[2], S[1] + e2])
            xa = int(max(np.floor(cs[:, 0].min()) - 1, 0))
            xb = int(min(np.ceil(cs[:, 0].max()) + 1, Ws))
            ya = int(max(np.floor(cs[:, 1].min()) - 1, 0))
            yb = int(min(np.ceil(cs[:, 1].max()) + 1, Hs))
            if xa >= xb or ya >= yb:
                continue
            mat = p.face_mat(a, coord)
            base = np.array(BASE[mat], np.float32) * SHADE[(a, s)]
            xs = np.arange(xa, xb, dtype=np.float32) + 0.5
            for y0 in range(ya, yb, 384):
                y1 = min(y0 + 384, yb)
                ys = np.arange(y0, y1, dtype=np.float32) + 0.5
                X, Y = np.meshgrid(xs, ys)
                dx, dy = X - s0[0], Y - s0[1]
                A = (dx * e2[1] - dy * e2[0]) / det
                B = (-dx * e1[1] + dy * e1[0]) / det
                inside = (A >= -ta) & (A <= 1 + ta) & (B >= -tb) & (B <= 1 + tb)
                if not inside.any():
                    continue
                dep = d0 + A * (d1 - d0) + B * (d3 - d0)
                zs = zb[y0:y1, xa:xb]
                m = inside & (dep > zs + 1e-5)
                if not m.any():
                    continue
                zs[m] = dep[m]
                plane[y0:y1, xa:xb][m] = pl
                pidb[y0:y1, xa:xb][m] = p.pid
                c = np.broadcast_to(base, m.shape + (3,)).copy()
                nz = noise[y0:y1, xa:xb]
                if mat == 'core':
                    c *= (1 + 0.07 * nz)[..., None]
                elif mat in ('oak', 'oak_edge'):
                    W = P0[None, None, :] + A[..., None] * (P1 - P0) + B[..., None] * (P3 - P0)
                    g = np.sin(2 * np.pi * (W[..., 2] / 0.21 + 0.8 * np.sin(2 * np.pi * W[..., 0] / 11.0)
                                            + 0.25 * np.sin(2 * np.pi * W[..., 0] / 2.7)))
                    c *= (1 + 0.05 * g + 0.02 * nz)[..., None]
                col[y0:y1, xa:xb][m] = c[m]
        sil = _dilate(_mark(pidb), 2)
        cre = _dilate(_mark(plane), 1) & ~sil
        col[cre] = LINE
        col[sil] = LINE
        img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), 'RGB')
        img = img.resize((Wf, Hf), Image.Resampling.BOX)
        img.save(path)
        return Wf, Hf
