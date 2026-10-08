import re, json
txt = open('data/hook_text.txt', encoding='utf-8').read().replace('\n', ' ')
toks = txt.split(); words = []
for t in toks:
    p = 1 if re.search(r'[.،,؟?…]', t[-1]) else 0
    big = 1 if re.search(r'[.؟?…]', t[-1]) else 0
    words.append((t.strip('.،,؟?…'), p, big))
sil = [(2.521723,2.642676),(4.817755,5.384059),(7.481882,7.784422),(8.346871,8.717868),(9.602313,10.2678),(11.949229,12.263469),(13.586803,13.864966),(15.869501,16.209229),(17.310862,17.767778),(18.291837,18.535964),(20.628934,21.434558),(22.467846,22.75229),(23.691066,23.961587),(25.618912,25.992494),(26.613016,26.778571),(28.468776,29.050748),(30.041338,30.358662),(33.068005,33.50746),(34.037506,34.381542),(35.328617,35.673265),(36.664467,37.083628),(38.372676,38.644558),(41.359796,41.69424),(43.695964,44.062086),(46.356984,46.694739),(48.350522,48.686032),(51.472358,51.710816)]
segs = []; a = 0.0
for s, e in sil: segs.append((a, s)); a = e
segs.append((a, 53.65))
N = len(words); K = len(segs); tot = sum(e - s for s, e in segs); rate = N / tot
print(N, 'words', K, 'segs', 'rate', round(rate, 2))
# DP: words -> segments (each seg >=1 word)
import functools
INF = 1e18
def cost(i, j, k):  # words i..j-1 in seg k
    n = j - i; d = segs[k][1] - segs[k][0]
    c = (d - n / rate) ** 2 * 3
    if j < N: c -= 0.6 * (words[j - 1][1]) ; c += 0.0 if words[j-1][1] else 0.5
    return c
@functools.lru_cache(None)
def f(i, k):
    if k == K: return (0 if i == N else INF, None)
    best = (INF, None)
    for j in range(i + 1, N - (K - k - 1) + 1):
        c, _ = f(j, k + 1)
        c += cost(i, j, k)
        if c < best[0]: best = (c, j)
    return best
i = 0; out = []
for k in range(K):
    _, j = f(i, k); out.append((segs[k][0], segs[k][1], ' '.join(w[0] for w in words[i:j]))); i = j
for o in out: print('%.2f-%.2f  %s' % o)
json.dump(out, open('data/hook_align.json', 'w'), ensure_ascii=False)
