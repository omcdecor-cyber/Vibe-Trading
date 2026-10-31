import base64
import numpy as np
from render3d import View
from model import *

OUT = '/tmp/drawer/out'
FONT = "'WenQuanYi Zen Hei','Noto Sans CJK SC','PingFang SC','Microsoft YaHei',sans-serif"
INK = '#26262b'
GRAY = '#6b6b72'
BLUE = '#2f6db5'
RED = '#c0392b'


def b64(path):
    return 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Svg:
    def __init__(self, w=1700, h=1100):
        self.w, self.h = w, h
        self.el = []

    def add(self, s):
        self.el.append(s)

    def text(self, x, y, s, size=13, anchor='start', weight='normal', fill=INK, lh=1.35, bg=False):
        lines = s.split('\n') if isinstance(s, str) else s
        if bg:
            wmax = max(self.tw(l, size) for l in lines)
            x0 = x - (wmax if anchor == 'end' else wmax / 2 if anchor == 'middle' else 0)
            self.add(f'<rect x="{x0 - 4:.1f}" y="{y - size:.1f}" width="{wmax + 8:.1f}" '
                     f'height="{size * lh * (len(lines) - 1) + size * 1.35:.1f}" fill="#fff" fill-opacity="0.88" rx="3"/>')
        for i, ln in enumerate(lines):
            w, sz, col = weight, size, fill
            if ln.startswith('~'):          # secondary (English) line
                ln, sz, col = ln[1:], size - 1, GRAY
            if ln.startswith('*'):
                ln, w = ln[1:], 'bold'
            self.add(f'<text x="{x:.1f}" y="{y + i * size * lh:.1f}" font-size="{sz}" text-anchor="{anchor}" '
                     f'font-weight="{w}" fill="{col}">{esc(ln)}</text>')

    @staticmethod
    def tw(s, size):
        s = s.lstrip('~*')
        return sum(size if ord(c) > 0x2E80 else size * 0.56 for c in s)

    def line(self, x1, y1, x2, y2, w=1.2, col=INK, dash=None, marker=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        m = f' marker-end="url(#{marker})"' if marker else ''
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" '
                 f'stroke-width="{w}"{d}{m} fill="none"/>')

    def poly(self, pts, w=1.2, col=INK, fill='none', dash=None, close=False, op=1.0):
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        tag = 'polygon' if close else 'polyline'
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<{tag} points="{p}" stroke="{col}" stroke-width="{w}" fill="{fill}" fill-opacity="{op}"{d}/>')

    def rect(self, x, y, w, h, sw=1.2, col=INK, fill='none', dash=None, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" stroke="{col}" '
                 f'stroke-width="{sw}" fill="{fill}"{d}/>')

    def circle(self, x, y, r, sw=1.2, col=INK, fill='#fff'):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" stroke="{col}" stroke-width="{sw}" fill="{fill}"/>')

    def image(self, x, y, w, h, href):
        self.add(f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" href="{href}"/>')

    def balloon(self, x, y, n, r=13):
        self.circle(x, y, r, 1.6)
        self.add(f'<text x="{x:.1f}" y="{y + 5:.1f}" font-size="15" font-weight="bold" text-anchor="middle" '
                 f'fill="{INK}">{n}</text>')

    def leader(self, pts, dot=True, col=INK):
        self.poly(pts, 1.0, col)
        if dot:
            x, y = pts[-1]
            self.circle(x, y, 2.6, 0, col, col)

    def arrow(self, x1, y1, x2, y2, col=BLUE, w=1.8, dash='7 4'):
        self.line(x1, y1, x2, y2, w, col, dash, 'arrB')

    def dim(self, x1, y1, x2, y2, label, off=0, side=1, size=12, tick=True, lpos=None, anchor='middle'):
        """Linear dim between two points (horizontal or vertical) drawn with arrowheads."""
        self.line(x1, y1, x2, y2, 1.0, INK, None, 'arrD')
        self.line(x2, y2, x1, y1, 1.0, INK, None, 'arrD')
        if lpos:
            self.text(lpos[0], lpos[1], label, size, anchor)

    def svg(self):
        defs = f'''<defs>
<marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker>
<marker id="arrD" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,1.5 L10,5 L0,8.5 z" fill="{INK}"/></marker>
<marker id="arrK" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>
<pattern id="pb" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="7" height="7" fill="#e6d3ad"/><line x1="0" y1="0" x2="0" y2="7" stroke="#a88a55" stroke-width="1"/></pattern>
<pattern id="oakp" width="40" height="9" patternUnits="userSpaceOnUse">
<rect width="40" height="9" fill="#d6a86c"/><path d="M0,4.5 Q10,1.5 20,4.5 T40,4.5" stroke="#a8743c" stroke-width="0.9" fill="none"/></pattern>
</defs>'''
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" class="page" '
                f'font-family="{FONT}">{defs}<rect width="{self.w}" height="{self.h}" fill="#fff"/>'
                + '\n'.join(self.el) + '</svg>')


def title_block(s, page, npages, title_cn, title_en):
    y = 1032
    s.line(20, y, 1680, y, 1.6)
    cells = [(20, '图名 Title', f'{title_cn}  {title_en}', 620),
             (640, '依据 Basis', '现场照片 4 张（结构为推断）  4 site photos (inferred)', 420),
             (1060, '比例 Scale', 'NTS 不按比例', 150),
             (1210, '日期 Date', '2026-10-31', 140),
             (1350, '版次 Rev', 'A', 90),
             (1440, '页 Sheet', f'{page} / {npages}', 240)]
    for x, k, v, w in cells:
        if x > 20:
            s.line(x, y, x, 1085, 1.0)
        s.text(x + 8, y + 18, k, 11, fill=GRAY)
        s.text(x + 8, y + 42, v, 15 if x == 20 else 14, weight='bold' if x == 20 else 'normal')
    s.rect(20, y, 1660, 53, 1.6)


# ----------------------------------------------------------------------------------------------
P = parts()
OFF = {'side_l': (-6, 0, 0), 'side_r': (6, 0, 0), 'back': (0, 7, 0), 'front': (0, -8, 0),
       'bottom': (0, 0, 0), 'oak': (0, -15, 0)}
LOCK_OFF = (0, 0, -3)


def page1():
    scene = [P[k].moved(v) for k, v in OFF.items()] + [p.moved(LOCK_OFF) for p in P['lock_r']]
    v = View(35, 45, 48, ss=2)
    wh = v.render(scene, f'{OUT}/main.png')
    sc = min(1000 / wh[0], 930 / wh[1])
    IX, IY = 25, 95

    def q(p):
        a = v.proj(np.array(p, float)) * sc
        return (IX + a[0], IY + a[1])

    def d(x, y):  # display coords (relative to image) -> page
        return (IX + x, IY + y)

    s = Svg()
    s.text(25, 52, '*抽屉盒爆炸图  DRAWER BOX — EXPLODED VIEW', 28)
    s.text(25, 78, '~按 4 张现场照片推断的做法：CNC 开料三聚氰胺颗粒板盒 + 止口定位打钉 + Blum 底装滑轨 + 外贴橡木面板。外形尺寸为示意。'
           , 14)
    s.image(IX, IY, wh[0] * sc, wh[1] * sc, b64(f'{OUT}/main.png'))

    # phantom: where the bottom sits on the left side's inner face
    xs = TS - 6
    band = [q((xs, 0, REC)), q((xs, D, REC)), q((xs, D, ZB)), q((xs, 0, ZB))]
    s.poly(band, 1.1, BLUE, '#2f6db5', '5 3', True, 0.18)

    # assembly arrows
    def arr(p1, p2):
        a, b = q(p1), q(p2)
        s.arrow(a[0], a[1], b[0], b[1])
    arr((TS - 6 + 0.4, 10.5, 4.6), (TS - 1.3, 10.5, 4.6))
    arr((W + 6 - TS - 0.4, 6.5, 6.0), (W - TS + 1.3, 6.5, 6.0))
    arr((W * 0.62, D - TB + 7 - 0.4, 5.0), (W * 0.62, D + 1.2, 5.0))
    arr((W - TS - 0.5, 1.0, REC - 3 + 0.3), (W - TS - 0.5, 1.0, REC - 0.6))

    # 1 side (left) + label
    bx, by = d(14, 40)
    s.leader([(bx + 200, by + 66), q((TS - 6, 8.5, 6.2))])
    s.balloon(bx, by, 1)
    s.text(bx + 20, by + 5, ['*侧板 Side  ×2', '5/8" (16) 白色三聚氰胺颗粒板', '~white melamine particleboard',
                             '~raw edges (no edge banding) 不封边'], 14)
    # 1 side (right): second balloon
    bx2, by2 = 1018, 520
    s.leader([(bx2 - 10, by2 + 8), q((W + 6, D * 0.78, 4.6))])
    s.balloon(bx2, by2, 1)

    # rabbet callout
    t = d(392, 22)
    s.leader([(t[0] - 4, t[1] + 6), q((LIP - 6 + RAB / 2, D - TB, 6.0))])
    s.text(t[0], t[1], ['*止口（两头不铣通）→ 详图 A', '~stopped rabbet → detail A'], 13)
    # notch / tab callout
    t = d(392, 120)
    s.leader([(t[0] + 172, t[1] + 2), q((LIP + 0.08, D - TB + 7, RZ0 - 0.2))])
    s.text(t[0], t[1], ['*后板凸舌 + 缺角 → A、B', '~back: tab + corner notch'], 13)

    # 2 back
    bx, by = d(700, 14)
    s.leader([(bx + 150, by + 48), q((W * 0.66, D - TB + 7, 5.6))])
    s.balloon(bx, by, 2)
    s.text(bx + 20, by + 5, ['*后板 Back', '5/8" (16) · 坐在底板上 sits on bottom', '~tabs into side rabbets, glue + brads'], 14)

    # 4 bottom (label on the panel)
    bx, by = d(470, 398)
    s.leader([(bx + 10, by + 9), q((W * 0.47, D * 0.42, ZB))])
    s.balloon(bx, by, 4)
    s.text(bx + 20, by + 5, ['*底板 Bottom 1/2" (12.7)', '离侧板下沿 1/2"（Blum 13mm）→ 剖面 C',
                             '~recessed 1/2" from side bottom edge'], 13, bg=True)

    # phantom label
    t = d(4, 210)
    s.leader([(t[0] + 92, t[1] + 50), q((xs, 4.0, (REC + ZB) / 2))], col=BLUE)
    s.text(t[0], t[1], ['*底板位置', '离下沿 1/2"', '~bottom sits', '~1/2" up', '→ 剖面 C'], 13, fill=BLUE)

    # 5 oak front
    bx, by = d(12, 452)
    s.leader([(bx + 40, by + 96), q((W * 0.12, -15.75, 4.8))])
    s.balloon(bx, by, 5)
    s.text(bx + 18, by + 5, ['*面板', '~Drawer front', '橡木 oak 3/4"', '外贴，从里面', '打螺丝固定'], 13)

    # 3 sub-front
    bx, by = d(452, 802)
    s.leader([(bx - 2, by - 13), q((W * 0.88, -8, 2.2))])
    s.balloon(bx, by, 3)
    s.text(bx + 20, by + 5, ['*盒子前板 Sub-front', '5/8"，推测同后板 VERIFY', '~assumed same as back (hidden)'], 13)

    # 6 lock
    bx, by = d(744, 802)
    s.leader([(bx - 8, by - 11), q((W - TS - 0.5, 0.8, REC - 3 - 0.2))])
    s.balloon(bx, by, 6)
    s.text(bx + 20, by + 5, ['*Blum 锁扣 ×2（左右各一）', '拧在底板底面前端两角', '~locking devices, under bottom'], 13)

    # legend for arrows / phantom

    # ---- right column: parts list
    X0, Y0 = 1040, 95
    s.text(X0, Y0 + 8, '*零件表 PARTS LIST', 18)
    s.text(X0 + 190, Y0 + 8, '~W×D×H = 抽屉盒外形 box outside size', 13)
    cols = [(0, 30, '#'), (30, 150, '零件 Part'), (180, 46, '数量'), (226, 150, '下料 Cut size'), (376, 264, '加工 / 备注 Notes')]
    rows = [
        ('1', ['*侧板 Side', '~5/8" 白三聚氰胺'], '2', ['D × H'], ['两头内侧铣止口 3/8"×5/8"', '上端留 1/2"，下端从 1 1/2" 起']),
        ('2', ['*后板 Back', '~5/8" 白三聚氰胺'], '1', ['(W − 1/2") ×', '(H − 1")'], ['四角缺 3/8"×1/2"', '坐在底板上；胶 + 钉进侧板']),
        ('3', ['*盒子前板', '~Sub-front 5/8"'], '1', ['同 #2'], ['推测同后板（被面板挡住）', 'VERIFY 待确认']),
        ('4', ['*底板 Bottom', '~1/2" 白三聚氰胺'], '1', ['(W − 1 1/4") × D'], ['离侧板下沿 1/2"；从下往上', '打钉进前、后板。侧边固定 VERIFY']),
        ('5', ['*面板 Front', '~橡木 oak 3/4"'], '1', ['按门表', '~per door list'], ['外贴；从盒子里面打螺丝', '#8 × 1" 约 4 颗（建议）']),
        ('6', ['*锁扣', '~Blum locking dev.'], '1 对', ['—'], ['拧在底板底面前端两角', '~L / R']),
        ('7', ['*底装滑轨', '~Blum undermount'], '1 对', ['按抽屉深'], ['侧板 ≤ 5/8" (16)', '底板上缩 1/2" (13)']),
        ('8', ['*钉 Brads', '~18ga × 1 1/4"（建议）'], '≈28', ['—'], ['前/后板→侧板 每角约 4 颗', '底板→前/后板 每边约 6 颗']),
    ]
    ty = Y0 + 26
    rh = 46
    s.rect(X0, ty, 640, 26, 1.2, INK, '#efefec')
    for cx, cw, ct in cols:
        s.text(X0 + cx + 6, ty + 18, ct, 12, weight='bold')
    y = ty + 26
    for r in rows:
        s.line(X0, y, X0 + 640, y, 0.8, '#9a9aa0')
        s.text(X0 + 10, y + 19, r[0], 13, weight='bold')
        s.text(X0 + 36, y + 19, r[1], 13)
        s.text(X0 + 186, y + 19, r[2], 13)
        s.text(X0 + 232, y + 19, r[3], 13)
        s.text(X0 + 382, y + 19, r[4], 12.5)
        y += rh
    s.rect(X0, ty, 640, y - ty, 1.4)
    for cx, cw, ct in cols[1:]:
        s.line(X0 + cx, ty, X0 + cx, y, 0.8, '#9a9aa0')
    s.text(X0, y + 20, ['~尺寸公式按 5/8" 侧板、1/2" 底板、照片估的止口推算，下单前请量实物核对。',
                        '~Formulas assume 5/8" sides, 1/2" bottom and the rabbet sizes estimated from photos.'], 12)

    # ---- notes
    ny = y + 70
    s.text(X0, ny, '*说明 NOTES', 18)
    notes = [
        '1. 侧板通长，前后板夹在两侧板中间；侧板两头内侧铣止口，前后板两端凸舌插进去。',
        '~Sides run full length; back & sub-front have tabs that sit in stopped rabbets.',
        '2. 止口上下不铣通，所以前后板四个角缺一块；上胶后从后板外面打钉进侧板。',
        '~Rabbets are stopped, so the panel corners are notched. Glue + brads from outside.',
        '3. 底板离侧板下沿 1/2"，下面留给 Blum 滑轨和锁扣；前后板都坐在底板上。',
        '~Bottom 1/2" up for Blum runners & locking devices; end panels sit on it.',
        '4. 待确认 VERIFY：底板和侧板怎么固定（开槽 or 侧板外打钉）、盒子前板做法。',
        '~VERIFY: bottom-to-side joint (dado or brads) and the sub-front (hidden in photos).',
    ]
    s.text(X0, ny + 26, notes, 13, lh=1.42)
    ly = ny + 26 + 13 * 1.42 * len(notes) + 14
    s.line(X0, ly, X0 + 40, ly, 1.8, BLUE, '7 4', 'arrB')
    s.text(X0 + 48, ly + 4, '装配方向 assembly direction', 12, fill=BLUE)
    s.poly([(X0 + 260, ly - 7), (X0 + 292, ly - 7), (X0 + 292, ly + 6), (X0 + 260, ly + 6)], 1.1, BLUE, BLUE, '5 3', True, 0.18)
    s.text(X0 + 300, ly + 4, '底板装好后的位置 bottom position', 12, fill=BLUE)
    def stand(p):  # drawer stood on its front like photo 1: (x, y, z) -> (x, z, y)
        sw = lambda b: (b[0], b[1], b[4], b[5], b[2], b[3])
        t = {0: 0, 1: 2, 2: 1}.get(p.thick_axis, p.thick_axis) if p.thick_axis is not None else None
        return Part(p.pid, [sw(b) for b in p.adds], [sw(b) for b in p.subs], p.mat, t, name=p.name)
    asm = [stand(P[k]) for k in OFF] + [stand(p) for p in P['lock_l'] + P['lock_r']]
    vT = View(24, 38, 20, ss=2)
    whT = vT.render(asm, f'{OUT}/assembled_photo1.png')
    scT = min(300 / whT[0], 205 / whT[1])
    TX, TY = 1370, ly + 22
    s.image(TX, TY, whT[0] * scT, whT[1] * scT, b64(f'{OUT}/assembled_photo1.png'))

    def qt(p):
        a = vT.proj(np.array(p, float)) * scT
        return (TX + a[0], TY + a[1])
    for i in range(6):
        hx, hy = qt((TS + (W - 2 * TS) * (i + 0.5) / 6, REC, D - TB / 2))
        s.circle(hx, hy, 1.8, 0, '#4a3c28', '#4a3c28')
    s.text(X0, TY + 22, ['*装好后立起来看底面', '~assembled, standing on its front', '跟照片 1 一样的角度：',
                         '· 底板夹在两侧板之间，缩进 1/2"', '· 橙色锁扣在前端两角', '· 底板靠后边一排钉眼',
                         '~(nails up into the back)'], 13)
    title_block(s, 1, 2, '抽屉盒爆炸图', 'Drawer box — exploded view')
    return s.svg()


def page2():
    s = Svg()
    s.text(25, 52, '*节点详图 + 剖面  JOINT DETAILS & SECTION', 28)
    s.text(25, 78, '~后板和侧板怎么接、底板为什么往上缩 —— 对应现场照片 2、4。图上字母见旁边说明。', 14)

    def mark(x, y, ch, t):
        s.line(x, y, t[0], t[1], 1.0, INK)
        s.circle(t[0], t[1], 2.4, 0, INK, INK)
        s.circle(x, y, 10, 1.4, INK, '#fff3c4')
        s.add(f'<text x="{x:.1f}" y="{y + 4.6:.1f}" font-size="13" font-weight="bold" text-anchor="middle" '
              f'fill="{INK}">{ch}</text>')

    def key(x, y, items):
        for ch, cn, en in items:
            s.circle(x + 10, y - 4.5, 10, 1.4, INK, '#fff3c4')
            s.add(f'<text x="{x + 10:.1f}" y="{y:.1f}" font-size="13" font-weight="bold" text-anchor="middle" '
                  f'fill="{INK}">{ch}</text>')
            lines = cn.split('\n')
            s.text(x + 27, y, lines + ['~' + l for l in en.split('\n')], 13, lh=1.32)
            y += (len(lines) + len(en.split('\n'))) * 13 * 1.32 + 12
        return y

    C = 3.2
    side = P['side_l'].clipped((-1, 99, D - C, 99, -1, 99))
    bot = P['bottom'].clipped((-1, 3.2, D - C, 99, -1, 99))
    back = P['back'].clipped((-1, 3.4, -1, 99, -1, 99))

    # ---------------- Detail A: inside view, pulled apart
    pull = (0, 2.0, 0)
    nails, xc, zs = nails_back_to_side(True, offset=pull)
    vA = View(42, 30, 110, ss=2)
    whA = vA.render([side, bot, back.moved(pull)] + nails, f'{OUT}/detA.png')
    scA = min(330 / whA[0], 545 / whA[1])
    AX, AY = 30, 160
    s.image(AX, AY, whA[0] * scA, whA[1] * scA, b64(f'{OUT}/detA.png'))

    def qa(p):
        a = vA.proj(np.array(p, float)) * scA
        return (AX + a[0], AY + a[1])

    s.text(25, 112, '*A  止口节点（拆开，从里面看）', 17)
    s.text(25, 134, '~stopped rabbet joint, pulled apart, inside view', 13)
    # where the back sits on the bottom
    fp = [qa((TS, D - TB, ZB)), qa((3.2, D - TB, ZB)), qa((3.2, D, ZB)), qa((TS, D, ZB))]
    s.poly(fp, 1.1, BLUE, BLUE, '5 3', True, 0.18)
    a1, a2 = qa((2.6, D + 2.0 - TB - 0.1, H + 0.35)), qa((2.6, D - TB + 0.25, H + 0.35))
    s.arrow(a1[0], a1[1], a2[0], a2[1])
    MA = {
        'a': qa((LIP + 0.01, D - TB / 2, 4.6)),
        'b': qa((TS, D - TB / 2, RZ1 + STOP / 2)),
        'c': qa((LIP + RAB / 2, D - TB / 2, RZ0)),
        'd': qa((LIP + RAB / 2, D - TB + 2.0, 3.0)),
        'e': qa((TS - 0.02, D - TB + 2.0, RZ1 + 0.22)),
        'f': qa((xc, D + 2.0 - TB - 0.32, zs[2])),
        'g': qa((1.9, D - TB * 0.5, ZB)),
    }
    s.__dict__['MA'] = MA
    off = {'a': (-62, 30), 'b': (-58, -40), 'c': (-60, 36), 'd': (52, 40), 'e': (58, -30), 'f': (-6, 52), 'g': (60, 40)}
    for ch, t in MA.items():
        mark(t[0] + off[ch][0], t[1] + off[ch][1], ch, t)
    key(370, 172, [
        ('a', '侧板止口：深 3/8"、宽 5/8"', '~9 × 16 mm rabbet'),
        ('b', '上端留 1/2" 不铣通', 'stopped 1/2" from top'),
        ('c', '下端：底板面上 1/2" 才开始', 'starts 1/2" above bottom'),
        ('d', '后板凸舌，伸进止口 3/8"', 'tab on the back'),
        ('e', '缺角 3/8" × 1/2"\n（让开止口两头）', 'corner notch'),
        ('f', '胶 + 钉，从后板外面打\n每角约 4 颗', 'glue + brads from outside'),
        ('g', '底板 1/2"，后板坐在上面\n（蓝框 = 后板位置）', 'back sits on the bottom'),
    ])

    # ---------------- Detail B: outside view, assembled (photos 2 & 4)
    vB = View(215, 28, 120, ss=2)
    whB = vB.render([side, bot, back], f'{OUT}/detB.png')
    scB = min(300 / whB[0], 520 / whB[1])
    BX, BY = 640, 170
    s.image(BX, BY, whB[0] * scB, whB[1] * scB, b64(f'{OUT}/detB.png'))

    def qb(p):
        a = vB.proj(np.array(p, float)) * scB
        return (BX + a[0], BY + a[1])

    s.text(620, 112, '*B  后角装好后（从外面看）', 17)
    s.text(620, 134, '~back corner assembled, outside view — 对应照片 2、4', 13)
    for z in zs:
        hx, hy = qb((xc, D, z))
        s.add(f'<ellipse cx="{hx:.1f}" cy="{hy:.1f}" rx="3.8" ry="3.1" fill="#5a4a32" stroke="#cdb88e" stroke-width="1.3"/>')
    for zc, up in ((RZ1, 1), (RZ0, -1)):
        vx, vy = qb((TS, D, zc))
        s.add(f'<path d="M{vx - 3.5:.1f},{vy:.1f} q3,{-4 * up:.1f} 7,0 q-2,{5 * up:.1f} -7,0 z" fill="#2b2620"/>')
    MB = {
        'a': qb((LIP / 2, D, 4.4)),
        'b': qb((TS / 2, D, H - STOP / 2)),
        'c': qb((xc, D, zs[1])),
        'd': qb((TS, D, RZ1)),
        'e': qb((2.2, D, (REC + ZB) / 2)),
        'f': qb((TS / 2, D, REC / 2)),
    }
    offb = {'a': (60, 18), 'b': (58, -26), 'c': (-60, 10), 'd': (60, 20), 'e': (-40, 46), 'f': (56, 30)}
    for ch, t in MB.items():
        mark(t[0] + offb[ch][0], t[1] + offb[ch][1], ch, t)
    key(960, 172, [
        ('a', '侧板端头只露 1/4" 窄边', 'only the 1/4" lip shows'),
        ('b', '止口两头不通，\n这里露出整块 5/8"', 'full 5/8" where it stops'),
        ('c', '钉眼（照片里崩皮的小坑）', 'brad holes'),
        ('d', '小黑洞 = 铣刀圆弧\n留下的空隙，不是坏了', 'router-radius void'),
        ('e', '底板后边 1/2"，在后板下面', 'bottom edge under back'),
        ('f', '侧板比底板再往下 1/2"\n（滑轨的空间）', 'side skirt = runner space'),
    ])

    # ---------------- Section C
    CX = 1215
    s.text(CX, 112, '*C  剖面（从侧面剖开看）', 17)
    s.text(CX, 134, '~section, middle of drawer cut away', 13)
    k = 33.0
    Y0 = 575.0

    def zz(z):
        return Y0 - z * k
    SEG = 3.0
    XF = CX + 70 + OAK_T * k
    XB = XF + SEG * k + 34

    def yy(y):
        return XF + y * k if y <= SEG else XB + (y - (D - SEG)) * k

    def rect_yz(y0, y1, z0, z1, **kw):
        s.rect(yy(y0), zz(z1), yy(y1) - yy(y0), zz(z0) - zz(z1), **kw)

    for (y0, y1) in [(0, SEG), (D - SEG, D)]:
        rect_yz(y0, y1, 0, H, sw=1.0, col='#8a8a90', fill='#f3f3f0')
    # recess zone highlight
    for (y0, y1) in [(TB, SEG), (D - SEG, D - TB)]:
        rect_yz(y0, y1, 0, REC, sw=0, col='none', fill='#f6d7d3')
    rect_yz(0, SEG, REC, ZB, sw=1.6, fill='url(#pb)')
    rect_yz(D - SEG, D, REC, ZB, sw=1.6, fill='url(#pb)')
    rect_yz(D - TB, D, ZB, H, sw=1.6, fill='url(#pb)')
    rect_yz(0, TB, ZB, H, sw=1.6, fill='url(#pb)')
    rect_yz(-OAK_T, 0, -0.75, H + 0.5, sw=1.6, fill='url(#oakp)')
    xa, xb = yy(SEG), XB
    s.add(f'<rect x="{xa + 5:.1f}" y="{zz(H + 0.4):.1f}" width="{xb - xa - 10:.1f}" '
          f'height="{zz(-0.4) - zz(H + 0.4):.1f}" fill="#fff"/>')
    for xb_, sg in ((xa, 1), (xb, -1)):
        pts = [(xb_ + sg * (4 if i % 2 else -1), zz(z)) for i, z in enumerate(np.linspace(-0.25, H + 0.25, 15))]
        s.poly(pts, 1.0, '#8a8a90')
    rect_yz(0.12, 1.75, 0.06, REC - 0.02, sw=1.0, fill='#f37c1e')
    rect_yz(1.75, 2.15, 0.20, REC - 0.02, sw=1.0, fill='#f37c1e')
    rect_yz(2.15, 2.75, REC - 0.12, REC - 0.02, sw=0.8, fill='#b2b7be')
    for yb in (D - TB / 2, TB / 2):
        s.line(yy(yb), zz(REC - 0.02), yy(yb), zz(ZB + 0.75), 2.2, '#3c3c42')
        s.line(yy(yb) - 4, zz(REC - 0.02), yy(yb) + 4, zz(REC - 0.02), 2.2, '#3c3c42')
    zs_ = 5.5
    s.line(yy(TB + 0.02), zz(zs_), yy(-0.55), zz(zs_), 2.4, '#3c3c42')
    s.line(yy(TB + 0.02), zz(zs_) - 5, yy(TB + 0.02), zz(zs_) + 5, 2.6, '#3c3c42')
    # dims (right side)
    xd = yy(D) + 22
    for z in (0, REC, ZB, H):
        s.line(yy(D) + 4, zz(z), xd + 6, zz(z), 0.7, GRAY)
    s.line(xd, zz(REC) - 20, xd, zz(REC), 1.0, INK, None, 'arrD')
    s.line(xd, zz(0) + 20, xd, zz(0), 1.0, INK, None, 'arrD')
    s.line(xd, zz(ZB) - 18, xd, zz(ZB), 1.0, INK, None, 'arrD')
    s.line(xd, zz(H), xd, zz(ZB), 1.0, INK, None, 'arrD')
    s.line(xd, zz(ZB), xd, zz(H), 1.0, INK, None, 'arrD')
    s.text(xd + 9, zz(0) + 24, ['*1/2" (13)', '*底板上缩', '~recess'], 13, fill=RED)
    s.text(xd + 9, zz(ZB) - 26, ['*1/2" 底板', '~bottom'], 13)
    s.text(xd + 9, zz((ZB + H) / 2), ['*H − 1"', '~back'], 13)
    yt = zz(H) - 16
    s.line(yy(D - TB), zz(H) - 4, yy(D - TB), yt - 6, 0.7, GRAY)
    s.line(yy(D), zz(H) - 4, yy(D), yt - 6, 0.7, GRAY)
    s.line(yy(D - TB) - 20, yt, yy(D - TB), yt, 1.0, INK, None, 'arrD')
    s.line(yy(D) + 20, yt, yy(D), yt, 1.0, INK, None, 'arrD')
    s.text(yy(D - TB) - 24, yt + 4, '5/8"', 13, anchor='end')
    # labels
    s.text(yy(D - SEG) + 8, zz(H) + 24, ['*后板', '~back'], 13)
    s.text(yy(TB) + 8, zz(H) + 24, ['*盒子前板', '~sub-front'], 13)
    s.text(yy(TB) + 8, zz(4.6), ['侧板', '（后面那块，', '没剖到）', '~side beyond'], 12, fill=GRAY)
    s.text(yy(D - SEG) + 6, zz(4.2), ['*钉：底板', '从下往上', '打进后板', '~brads up'], 12.5)
    s.leader([(yy(D - SEG) + 40, zz(4.2) + 54), (yy(D - TB / 2) - 2, zz(ZB + 0.4))])
    s.text(CX, zz(H + 0.5) + 4, ['*面板', '~oak front'], 13)
    s.text(CX, zz(2.6), ['*螺丝从', '里面打', '~screws', '~from inside'], 12.5)
    s.leader([(CX + 46, zz(2.6) - 30), (yy(-0.3), zz(zs_))])
    s.text(XF, zz(-0.75) + 26, ['*红色区域 = 底板下面 1/2" 空间', '放 Blum 滑轨和锁扣（橙色）',
                                 '~1/2" space under the bottom for runners + locking devices'], 13)

    # ---------------- notes band
    NY = 800
    s.line(20, NY - 32, 1680, NY - 32, 0.8, '#b5b5ba')
    colx = [25, 590, 1155]
    blocks = [
        ['*A  止口节点', '· 侧板两头内侧各铣一道止口：深 3/8"、宽 5/8"（=后板厚）。',
         '· 上端留 1/2" 不铣通，下端从底板面以上 1/2" 才开始。',
         '· 后板两端凸舌插进止口，四角缺 3/8"×1/2" 让开。',
         '· 上胶后从后板外面打钉进侧板，每角约 4 颗。',
         '· 好处：后板一插就定位，盒子自然方正，不用夹具。',
         '~Stopped rabbet 3/8"×5/8", tabs on the back, glue + brads;',
         '~self-locating, so the box comes out square.'],
        ['*B  外面看到的样子', '· 侧板端头只露 1/4" 窄边，缺角处露出整块 5/8"。',
         '· 后板两边那排崩皮小坑 = 钉眼。',
         '· 角上小黑洞是 CNC 铣刀圆弧留下的空隙，不是坏了。',
         '· 照片 3 那个角的黑缺口也在这个位置，只是多崩了一点。',
         '~Lip, brad holes and router-radius voids, as in photos 2 & 4.'],
        ['*C  底板为什么往上缩', '· 底板 1/2"，离侧板下沿 1/2"（Blum 要求 13mm）。',
         '· 前后板坐在底板上，底板从下往上打钉固定。',
         '· 后板不落到底，所以不用开 Blum 那个 35×13mm 后角缺口。',
         '· 待确认 VERIFY：底板和侧板怎么固定（照片看不到）；',
         '  盒子前板被面板挡住，图中按后板做法画。',
         '~Bottom 1/2" up for runners & locks; end panels sit on it.',
         '~VERIFY bottom-to-side joint and the sub-front.'],
    ]
    for x, b in zip(colx, blocks):
        s.text(x, NY, b, 13.5, lh=1.6)
    title_block(s, 2, 2, '抽屉盒节点详图', 'Joint details & section')
    return s.svg()


if __name__ == '__main__':
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            '@page{size:17in 11in;margin:0} body{margin:0;background:#fff}'
            '.page{display:block;width:17in;height:11in;page-break-after:always}'
            '</style></head><body>' + page1() + page2() + '</body></html>')
    open(f'{OUT}/sheet.html', 'w').write(html)
    print('ok')
