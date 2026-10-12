"""Split the long Chile video into numbered vertical 9:16 Shorts (1080x1920), each 1.5-2 min, cut only at sentence pauses / part boundaries.
Top: 'الجزء N' badge; bottom: 'باقي الأجزاء على القناة'; last 4 s: end card 'تابع الجزء N+1 على القناة'."""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
FF = '/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
SRC = 'build/sh/'; OUT = 'build/sh/split/'; os.makedirs(OUT, exist_ok=True)
FONT = 'assets/Amiri-Bold.ttf'
PROJ = os.environ.get('PROJ', 'chile')
END = 1e4  # until end of file
ORD = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس']
if PROJ == 'chile':
    SUBTITLE = '٣٣ رجلًا تحت الأرض'; PREFIX = 'Chile33_Short_Part'; NPART = 6
    P = {1: 'Chile33_Part1_Hook_AR.mp4', 2: 'Chile33_Part2_Mine_AR_NoMusic.mp4', 3: 'Chile33_Part3_Refuge_AR.mp4', 4: 'Chile33_Part4_Hope_AR.mp4', 5: 'Chile33_Part5_Trapped_AR.mp4',
         6: 'Chile33_Part6_Needs_AR.mp4', 7: 'Chile33_Part7_Rescue_AR.mp4', 8: 'Chile33_Part8_Aftermath_AR.mp4', 9: 'Chile33_Part9_Finale_AR.mp4'}
    # (part file, start, end) -- cut points are mid-gaps between narrated sentences
    SPLIT = {
     1: [(1, 0, END), (2, 0, END)],
     2: [(3, 0, END), (4, 0, 50.22)],
     3: [(4, 50.22, END), (5, 0, 45.8)],
     4: [(5, 45.8, END), (6, 0, END), (7, 0, 27.75)],
     5: [(7, 27.75, END), (8, 0, 7.7)],
     6: [(8, 7.7, END), (9, 0, END)],
    }
else:
    SUBTITLE = 'ماورو… ضائع في الصحراء'; PREFIX = 'Prosperi_Short_Part'; NPART = 6
    P = {1: 'Prosperi_Lost_in_Sahara_AR.mp4', 2: 'Prosperi_Part2_Marathon_AR.mp4', 3: 'Prosperi_Part3_Storm_AR.mp4', 4: 'Prosperi_Part4_Helicopter_AR.mp4', 5: 'Prosperi_Part5_LastChance_AR.mp4',
         6: 'Prosperi_Part6_Rescue_AR.mp4', 7: 'Prosperi_Part7_Algeria_AR.mp4', 8: 'Prosperi_Part8_Lesson_AR.mp4'}
    SPLIT = {
     1: [(1, 0, END), (2, 0, END)],
     2: [(3, 0, END), (4, 0, 18.45)],
     3: [(4, 18.45, END), (5, 0, 54.35)],
     4: [(5, 54.35, END), (6, 0, 52.6)],
     5: [(6, 52.6, END), (7, 0, 53.1)],
     6: [(7, 53.1, END), (8, 0, END)],
    }
DUR = {}
def dur(f):
    if f not in DUR:
        r = subprocess.run([FF, '-i', SRC + P[f]], capture_output=True, text=True).stderr
        h, m, s = r.split('Duration: ')[1].split(',')[0].split(':'); DUR[f] = int(h) * 3600 + int(m) * 60 + float(s)
    return DUR[f]
def ar(s): return get_display(arabic_reshaper.reshape(s))
def st(d, xy, s, f, fill, w=7): d.text(xy, ar(s), font=f, fill=fill, anchor='mm', stroke_width=w, stroke_fill=(20, 12, 6, 255))
def overlay_a(n, path):
    im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 70, 1020, 370), 36, fill=(12, 8, 4, 160), outline=(226, 172, 70, 255), width=5)
    st(d, (540, 165), f'الجزء {ORD[n - 1]}', ImageFont.truetype(FONT, 120), (255, 226, 130, 255), 8)
    st(d, (540, 290), SUBTITLE, ImageFont.truetype(FONT, 66), (255, 255, 255, 255), 6)
    st(d, (540, 1610), 'باقي الأجزاء على القناة', ImageFont.truetype(FONT, 56), (255, 226, 130, 255), 6)
    im.save(path)
def overlay_b(n, last, path):
    im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 1530, 1080, 1920), fill=(10, 6, 3, 255))
    d.rounded_rectangle((60, 1585, 1020, 1765), 80, fill=(196, 38, 38, 255), outline=(255, 255, 255, 255), width=6)
    d.polygon([(130, 1640), (130, 1710), (192, 1675)], fill=(255, 255, 255, 255))
    t = 'كل الأجزاء على القناة' if last else f'تابع الجزء {ORD[n]} على القناة'
    f = ImageFont.truetype(FONT, 80)
    while d.textlength(ar(t), font=f) > 740: f = ImageFont.truetype(FONT, f.size - 4)
    d.text((630, 1678), ar(t), font=f, fill=(255, 255, 255, 255), anchor='mm')
    st(d, (540, 1850), 'باقي الأجزاء على القناة' if not last else 'شكرًا لمشاهدتك', ImageFont.truetype(FONT, 48), (255, 226, 130, 255), 5)
    im.save(path)

def build(n):
    segs = [(f, s, min(e, dur(f))) for f, s, e in SPLIT[n]]
    files = []
    for f, _, _ in segs:
        if f not in files: files.append(f)
    ins = []
    for f in files: ins += ['-i', SRC + P[f]]
    ia, ib = OUT + f'{n}_a.png', OUT + f'{n}_b.png'; overlay_a(n, ia); overlay_b(n, n == NPART, ib)
    ins += ['-loop', '1', '-i', ia, '-loop', '1', '-i', ib]
    na, nb = len(files), len(files) + 1; k = len(segs); total = sum(e - s for _, s, e in segs)
    fc = []
    for i, (f, s, e) in enumerate(segs):
        j = files.index(f); d = e - s
        fc.append(f'[{j}:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps=30,split=2[a{i}][b{i}]')
        fc.append(f'[a{i}]crop=406:720:437:0,scale=270:480,gblur=sigma=7,scale=1080:1920,eq=brightness=-0.22:saturation=1.05[bg{i}]')
        fc.append(f'[b{i}]crop=720:720:280:0,scale=1080:1080:flags=lanczos[fg{i}]')
        fc.append(f'[bg{i}][fg{i}]overlay=0:420[v{i}]')
        fc.append(f'[{j}:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,afade=in:d=0.04,afade=out:st={d - 0.04:.3f}:d=0.04[au{i}]')
    fc.append(''.join(f'[v{i}][au{i}]' for i in range(k)) + f'concat=n={k}:v=1:a=1[vc][ac]')
    fc.append('[vc]drawbox=x=0:y=416:w=1080:h=4:color=0xE2AC46@1:t=fill,drawbox=x=0:y=1500:w=1080:h=4:color=0xE2AC46@1:t=fill[vd]')
    fc.append(f'[{na}:v]format=rgba[oa]; [{nb}:v]format=rgba,fade=t=in:st={total - 4.0:.2f}:d=0.5:alpha=1[ob]')
    fc.append('[vd][oa]overlay=0:0:shortest=1[v1]; [v1][ob]overlay=0:0:shortest=1,format=yuv420p[vf]')
    fc.append(f'[ac]afade=t=out:st={total - 0.35:.2f}:d=0.35,volume=1.12,alimiter=limit=0.93[af]')
    out = OUT + f'{PREFIX}{n}_AR.mp4'
    subprocess.run([FF, '-y', '-loglevel', 'error'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[vf]', '-map', '[af]', '-t', f'{total:.2f}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
                   '-maxrate', '5M', '-bufsize', '9M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
    print(n, round(total, 2), out, flush=True)
if __name__ == '__main__':
    if sys.argv[1:] == ['durs']:
        for n in SPLIT: print(n, round(sum(min(e, dur(f)) - s for f, s, e in SPLIT[n]), 1))
    else:
        for n in sys.argv[1:]: build(int(n))
