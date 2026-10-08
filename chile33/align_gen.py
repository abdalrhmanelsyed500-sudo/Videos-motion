import re, json, sys, subprocess, functools, imageio_ffmpeg
txtf, wav, outj = sys.argv[1:4]; FF = imageio_ffmpeg.get_ffmpeg_exe()
r = subprocess.run([FF, '-hide_banner', '-i', wav, '-af', 'silencedetect=noise=-30dB:d=0.12', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
dur = float(re.search(r'time=(\d+):(\d+):([\d.]+)', r.split('size=')[-1]).group(1)) * 3600 + float(re.search(r'time=(\d+):(\d+):([\d.]+)', r.split('size=')[-1]).group(2)) * 60 + float(re.search(r'time=(\d+):(\d+):([\d.]+)', r.split('size=')[-1]).group(3))
sil = list(zip(st, en[:len(st)]))
toks = open(txtf, encoding='utf-8').read().replace('\n', ' ').split(); words = []
for t in toks: words.append((t.strip('.،,؟?…'), 1 if re.search(r'[.،,؟?…]', t[-1]) else 0))
segs = []; a = 0.0
for s, e in sil:
    if s - a > 0.05: segs.append((a, s))
    a = e
if dur - a > 0.1: segs.append((a, dur))
N = len(words); K = len(segs); rate = N / sum(e - s for s, e in segs); print(N, 'words', K, 'segs', round(rate, 2), 'w/s dur', dur)
def cost(i, j, k):
    n = j - i; d = segs[k][1] - segs[k][0]; c = (d - n / rate) ** 2 * 3
    if j < N: c -= 0.6 * words[j - 1][1]; c += 0.0 if words[j - 1][1] else 0.5
    return c
@functools.lru_cache(None)
def f(i, k):
    if k == K: return (0 if i == N else 1e18, None)
    best = (1e18, None)
    for j in range(i + 1, N - (K - k - 1) + 1):
        c = f(j, k + 1)[0] + cost(i, j, k)
        if c < best[0]: best = (c, j)
    return best
i = 0; out = []
for k in range(K):
    j = f(i, k)[1]; out.append((segs[k][0], segs[k][1], ' '.join(w[0] for w in words[i:j]))); i = j
for o in out: print('%.2f-%.2f  %s' % o)
json.dump(out, open(outj, 'w'), ensure_ascii=False)
