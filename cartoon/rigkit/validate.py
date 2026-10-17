"""Automatic QA for RigKit.  usage: python -m rigkit.validate [final_video.mp4]  -> writes QA_REPORT.md"""
import sys, os, math, json, subprocess, hashlib, re
import numpy as np, cv2
from . import episode as E, face as F, build, chars, anim
from .rig import Rig
from .render import make_episode, ROOT, FFMPEG

def parts_borders():
    bad = []; n = 0
    for d in sorted(os.listdir(os.path.join(ROOT, 'out', 'rigs'))):
        rg = Rig(os.path.join(ROOT, 'out', 'rigs', d, 'rig.json'))
        for p in rg.parts:
            im = rg.img(p); n += 1
            m = max(im[0, :, 3].max(), im[-1, :, 3].max(), im[:, 0, 3].max(), im[:, -1, 3].max())
            if m > 0.02: bad.append((d, p, float(m)))
    return n, bad

def connectivity(trials=250, seed=1):
    r = np.random.RandomState(seed); res = {}
    for d in sorted(os.listdir(os.path.join(ROOT, 'out', 'rigs'))):
        rg = Rig(os.path.join(ROOT, 'out', 'rigs', d, 'rig.json')); fails = 0; worst = None
        spec = chars.SPECS[rg.d['character']]; dyn = F.face_dyn({}, spec, rg.d['view'])
        for k in range(trials):
            pose = {}
            for b in rg.bones:
                if b['limit'] and b['name'] not in ('root',):
                    lo, hi = b['limit']; pose[b['name']] = {'rot': math.radians(r.uniform(lo * .9, hi * .9))}
            sw = {s['name']: r.choice(['hand_relaxed', 'hand_open', 'hand_fist', 'hand_point']) for s in rg.slots if s['name'].startswith('hand')}
            cv = np.zeros((900, 900, 3), np.float32)
            # draw alpha: render on black then also on white; union mask = alpha via two renders
            a = np.zeros((900, 900, 3), np.float32); b2 = np.ones((900, 900, 3), np.float32)
            rg.draw(a, pose, (1.0, 450, 760), swap=sw, dyn=dyn); rg.draw(b2, pose, (1.0, 450, 760), swap=sw, dyn=dyn)
            alpha = 1 - (b2 - a).mean(2)          # white-bg minus black-bg = 1-alpha
            m = (alpha > 0.05).astype(np.uint8)
            m = cv2.dilate(m, np.ones((3, 3), np.uint8))
            nlab = cv2.connectedComponents(m)[0] - 1
            if nlab != 1:
                fails += 1; worst = worst or (k, nlab)
        res[d] = (trials, fails, worst)
    return res

def episode_checks(ep):
    out = {}; S = E.S
    # limits
    viol = 0; worst = (0, None)
    for A in (ep.z, ep.l):
        for st in A.states:
            rig = A.rigs[st['view']]; v = rig.violations(st['pose'], 1e-4)
            # tuft/pigtails are secondary bones with their own limits
            if v: viol += 1; worst = (max(worst[0], 1), v[0])
    out['limit_violation_frames'] = (viol, worst[1])
    # reach error + foot lock
    slip_side = 0.0; slip_front = 0.0; reach = 0.0; planted_frames = 0
    for A, who, wk in ((ep.z, 'z', ep.zw), (ep.l, 'l', ep.lw)):
        prev = {}
        for i, st in enumerate(A.states):
            t = st['t']; rig = A.rigs[st['view']]; W = rig.world(st['pose'], st['root'])
            for nm in 'LR':
                a = W[f'foot{nm}'][:2, 2]
                if st['view'] == 'side' and 'sx' not in st['root']:
                    x, y, rot, stt, _ = wk.foot(nm, t); reach = max(reach, float(np.hypot(a[0] - x, a[1] - y)))
                    if stt == 'plant':
                        if (nm, 's') in prev and abs(prev[(nm, 's')][1] - x) < 1e-6:
                            slip_side = max(slip_side, abs(a[0] - prev[(nm, 's')][0])); planted_frames += 1
                        prev[(nm, 's')] = (a[0], x)
                    else: prev.pop((nm, 's'), None)
                elif st['view'] == 'front':
                    if not st.get('free') and abs(st['pose'].get('hips', {}).get('ty', 0)) < 80:
                        gx = st['x'] + (36 if nm == 'R' else -36) * st['root'].get('sx', 1.0)
                        slip_front = max(slip_front, float(np.hypot(a[0] - gx, a[1] + 36)))
    out['ik_reach_error_units'] = reach; out['planted_slip_side_px'] = slip_side * S; out['planted_slip_front_px'] = slip_front * S; out['planted_frames'] = planted_frames
    return out

def lip_checks(ep):
    r = {}
    for k, sp in ep.speech.items():
        env = np.asarray(sp['env']); op = np.array([m['open'] for m in sp['mouth']])
        c = float(np.corrcoef(env, op)[0, 1]); loud = env > .35; quiet = env < .05
        r[k] = (c, float((op[loud] > .1).mean()) if loud.any() else 1.0, float((op[quiet] < .05).mean()) if quiet.any() else 1.0, len(op) / 30)
    return r

def video_checks(path):
    import tempfile
    info = subprocess.run([FFMPEG, '-i', path, '-f', 'null', '-'], capture_output=True, text=True).stderr
    fr = int(re.findall(r'frame=\s*(\d+)', info)[-1]); dur = re.findall(r'Duration: (\S+),', info)[0]
    p = subprocess.Popen([FFMPEG, '-loglevel', 'error', '-i', path, '-vf', 'scale=320:180', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    buf = p.stdout.read(); p.wait(); fr_g = np.frombuffer(buf, np.uint8).reshape(-1, 180, 320).astype(np.float32)
    mean = fr_g.mean((1, 2)); diff = np.abs(np.diff(fr_g, axis=0)).mean((1, 2))
    zero_run = 0; mr = 0
    for d in diff:
        zero_run = zero_run + 1 if d < 1e-3 else 0; mr = max(mr, zero_run)
    med = float(np.median(diff))
    return dict(frames=fr, frames_decoded=len(fr_g), duration=dur, min_mean_luma=float(mean.min()), max_diff=float(diff.max()), median_diff=med,
                spike_ratio=float(diff.max() / max(med, 1e-6)), max_zero_diff_run=mr, spike_frame=int(diff.argmax()))

def determinism():
    a = make_episode(); b = make_episode(); h = []
    for ep in (a, b):
        m = hashlib.md5()
        for A in (ep.z, ep.l):
            for st in A.states[::7]: m.update(json.dumps(st['pose'], sort_keys=True, default=float).encode()); m.update(json.dumps(st['root'], sort_keys=True, default=float).encode())
        h.append(m.hexdigest())
    return h

def main():
    vid = sys.argv[1] if len(sys.argv) > 1 else None
    L = ['# QA_REPORT — RigKit demo', '']
    ep = make_episode()
    n, bad = parts_borders(); L += ['## 1. Sprite integrity', f'- {n} part sprites checked, clipped at the image border: **{len(bad)}** {bad[:3] if bad else ""}']
    cn = connectivity(); L += ['', '## 2. Joint continuity (random poses within 90% of joint limits, random hands)', '| rig | poses | disconnected | first failure |', '|---|---|---|---|']
    for d, (t, f, w) in cn.items(): L.append(f'| {d} | {t} | {f} | {w} |')
    ec = episode_checks(ep); L += ['', '## 3. Episode rig checks (every frame of both characters)',
        f"- frames with a joint outside its limit: **{ec['limit_violation_frames'][0]}** {ec['limit_violation_frames'][1] or ''}",
        f"- IK ankle reach error (walk, max): **{ec['ik_reach_error_units']:.2e} units**",
        f"- planted-foot slip, side walk (max, {ec['planted_frames']} planted foot-frames): **{ec['planted_slip_side_px']:.4f} px**",
        f"- planted-foot error, front standing (max): **{ec['planted_slip_front_px']:.4f} px**"]
    lc = lip_checks(ep); L += ['', '## 4. Lip-sync vs audio envelope', '| clip | corr(open, envelope) | open when loud | closed when quiet | length s |', '|---|---|---|---|---|']
    for k, v in lc.items(): L.append(f'| {k} | {v[0]:.2f} | {v[1]*100:.0f}% | {v[2]*100:.0f}% | {v[3]:.2f} |')
    h = determinism(); L += ['', '## 5. Determinism', f'- two independent builds give identical pose hashes: **{h[0] == h[1]}** ({h[0][:12]})']
    if vid and os.path.exists(vid):
        vc = video_checks(vid); L += ['', '## 6. Final video', f"- file: `{os.path.basename(vid)}` duration {vc['duration']}, frames (ffmpeg) {vc['frames']}, decoded {vc['frames_decoded']}, expected {ep.n}",
            f"- minimum mean luminance of any frame: {vc['min_mean_luma']:.1f} (black frame if ≈0)",
            f"- longest run of identical consecutive frames: {vc['max_zero_diff_run']} (freeze if large)",
            f"- frame-diff spike ratio (max/median): {vc['spike_ratio']:.1f} at frame {vc['spike_frame']}"]
        ok = vc['frames_decoded'] == ep.n and vc['min_mean_luma'] > 40 and vc['max_zero_diff_run'] < 3
    else: ok = True
    allok = (len(bad) == 0 and all(f == 0 for (_, f, _) in cn.values()) and ec['limit_violation_frames'][0] == 0 and ec['ik_reach_error_units'] < 1e-3 and ec['planted_slip_side_px'] < 0.5 and h[0] == h[1] and ok)
    L += ['', f'## Verdict: {"PASS" if allok else "FAIL - see items above"}', '']
    open(os.path.join(ROOT, 'QA_REPORT.md'), 'w').write('\n'.join(L)); print('\n'.join(L))

if __name__ == '__main__': main()
