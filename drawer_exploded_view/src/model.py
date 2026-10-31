# Drawer box model, inferred from the site photos. Inches.
# x = width (left->right, seen from the front), y = depth (front->back), z = height.
from render3d import Part

W, D, H = 19.0, 16.0, 8.5          # overall box size: illustrative only
TS = 0.625                         # side / back / sub-front 5/8"
TB = 0.625
TBOT = 0.5                         # bottom 1/2"
REC = 0.5                          # bottom recess 1/2" (Blum 13 mm)
LIP = 0.25                         # side lip left outside the rabbet
RAB = TS - LIP                     # rabbet depth into side 3/8"
STOP = 0.5                         # rabbet stopped 1/2" from top and 1/2" above bottom
ZB = REC + TBOT                    # top of bottom = underside of back / sub-front
RZ0, RZ1 = ZB + STOP, H - STOP     # rabbet / tab height range

OAK_T = 0.75


def parts():
    P = {}
    P['side_l'] = Part(1, [(0, TS, 0, D, 0, H)],
                       [(LIP, TS, D - TB, D, RZ0, RZ1), (LIP, TS, 0, TB, RZ0, RZ1)],
                       'mel', 0, name='side_l')
    P['side_r'] = Part(2, [(W - TS, W, 0, D, 0, H)],
                       [(W - TS, W - LIP, D - TB, D, RZ0, RZ1), (W - TS, W - LIP, 0, TB, RZ0, RZ1)],
                       'mel', 0, name='side_r')

    def end_panel(pid, y0, name):
        y1 = y0 + TB
        return Part(pid, [(TS, W - TS, y0, y1, ZB, H),
                          (LIP, TS, y0, y1, RZ0, RZ1),
                          (W - TS, W - LIP, y0, y1, RZ0, RZ1)], (), 'mel', 1, name=name)

    P['back'] = end_panel(3, D - TB, 'back')
    P['front'] = end_panel(4, 0, 'front')
    P['bottom'] = Part(5, [(TS, W - TS, 0, D, REC, ZB)], (), 'mel', 2, name='bottom')
    P['oak'] = Part(6, [(-0.5, W + 0.5, -OAK_T, 0, -0.75, H + 0.5)], (), 'oak', 1, name='oak')

    def lock(pid, x0, x1, name):
        return [Part(pid, [(x0, x1, 0.12, 1.75, 0.06, REC - 0.02),
                           (x0 + 0.15, x1 - 0.15, 1.75, 2.15, 0.20, REC - 0.02)], (), 'orange', name=name),
                Part(pid + 10, [(x0 - 0.05, x1 + 0.05, 2.15, 2.75, REC - 0.12, REC - 0.02)], (), 'metal',
                     name=name + '_plate')]

    P['lock_l'] = lock(7, TS + 0.06, TS + 0.96, 'lock_l')
    P['lock_r'] = lock(8, W - TS - 0.96, W - TS - 0.06, 'lock_r')
    return P


def nails_back_to_side(left=True, n=4, length=1.25, dia=0.07, offset=(0, 0, 0), pid0=40):
    """Brads shot through the back face into the side (axis = y). Positions in assembled coords."""
    xc = LIP + RAB / 2 if left else W - LIP - RAB / 2
    zs = [RZ0 + (RZ1 - RZ0) * (i + 0.5) / n for i in range(n)]
    out = []
    for i, z in enumerate(zs):
        out.append(Part(pid0 + i, [(xc - dia / 2, xc + dia / 2, D - length, D, z - dia / 2, z + dia / 2)],
                        (), 'nail', offset=offset))
    return out, xc, zs
