"""Sufan side walk: RigKit Walker (foot-lock IK) configured for Sufan's short legs."""
import sys, os, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sufan_rig_side as S
from rigkit.anim import Walker
import sufan_rig_side as _S
_R = _S.LEG_RAISE / _S.PPU
HIP_Y = -85.13 - _R; LMAX = 40.2 + _R
def ankle(th):   # ankle height above ground for a boot rotated th (toe-down positive): ankle 44.4u above sole, toe 42u ahead, heel 30u behind
    return 44.4 * math.cos(th) + (42.0 * math.sin(th) if th > 0 else 30.0 * math.sin(-th))
GEO = dict(hip_y=HIP_Y, lmax=LMAX, ankle=ankle, hip_dx={'R': 0.0, 'L': 0.0})
def make(rig, d, x0, x1, t0, t_end, **kw):
    p = dict(Ts=0.50, swing=0.40, a=9.0, stand=5.0, lift=7.0, bend=BEND, arm_gain=1.3, arm_bend=16.0); p.update(kw)
    return Walker(rig, d, x0, x1, t0, t_end, geo=GEO, **p)
BEND = 1
