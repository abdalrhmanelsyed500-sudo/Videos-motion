"""Vertical 9:16 YouTube Shorts (1080x1920) cut from the finished long videos: square 720x720 crop of the painted frame (native sharpness) over a blurred, darkened cover of the same frame,
procedural Arabic hook title on top, 'watch the full story' end card at the bottom. Cuts happen only at pauses of the narration. Spoiler-free by construction."""
import subprocess, sys, os, json
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
FF = '/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
SRC = 'build/sh/'; OUT = 'build/sh/out/'; os.makedirs(OUT, exist_ok=True)
FONT = 'assets/Amiri-Bold.ttf'
C1, C2, C3 = 'Chile33_Part1_Hook_AR.mp4', 'Chile33_Part3_Refuge_AR.mp4', 'Chile33_Part4_Hope_AR.mp4'
S1, S2, S3 = 'Prosperi_Lost_in_Sahara_AR.mp4', 'Prosperi_Part2_Marathon_AR.mp4', 'Prosperi_Part3_Storm_AR.mp4'
# segments: (file, start, end, crop-centre-x list [(t_rel, cx)] -> piecewise constant; keep simple: single cx per segment)
SHORTS = {
 'C1': dict(title=['٣٣ رجلًا عالقين', 'تحت الجبل'], segs=[(C1, 0.0, 33.29, 640)]),
 'C2': dict(title=['٣٣ رجلًا… وطعام', 'يكفي يومين فقط'], segs=[(C2, 0.0, 35.05, 640)]),
 'C3': dict(title=['اليوم الثالث تحت الأرض', 'بلا شمس وبلا وقت'], segs=[(C3, 0.0, 33.83, 640)]),
 'S1': dict(title=['رياضي أولمبي', 'في أقسى سباق بالعالم'], segs=[(S1, 0.0, 18.04, 640), (S2, 2.92, 22.21, 640)]),
 'S2': dict(title=['عاصفة واحدة', 'كانت كافية لتغيير حياته'], segs=[(S2, 28.86, 59.95, 640), (S2, 72.66, 80.10, 640)]),
 'S3': dict(title=['جدار أصفر', 'ابتلع كل شيء'], segs=[(S3, 0.0, 38.40, 640)]),
}
if os.path.exists('data/shorts_cx.json'):
    CX = json.load(open('data/shorts_cx.json'))
    for k, v in CX.items():
        for i, c in enumerate(v): SHORTS[k]['segs'][i] = SHORTS[k]['segs'][i][:3] + (c,)

def ar(s): return get_display(arabic_reshaper.reshape(s))
def fit(d, s, size, maxw):
    while True:
        f = ImageFont.truetype(FONT, size)
        if d.textlength(ar(s), font=f) <= maxw or size < 30: return f
        size -= 4
def shadowtext(d, xy, s, f, fill, st=7):
    d.text(xy, ar(s), font=f, fill=fill, anchor='mm', stroke_width=st, stroke_fill=(20, 12, 6, 255))
def overlay_a(lines, path):
    im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 70, 1020, 370), 36, fill=(12, 8, 4, 150), outline=(226, 172, 70, 255), width=5)
    f1 = fit(d, lines[0], 96, 880); f2 = fit(d, lines[1], 76, 880)
    shadowtext(d, (540, 170), lines[0], f1, (255, 226, 130, 255)); shadowtext(d, (540, 285), lines[1], f2, (255, 255, 255, 255), 6)
    f3 = ImageFont.truetype(FONT, 50)
    shadowtext(d, (540, 1610), 'القصة كاملة في الفيديو الطويل', f3, (255, 226, 130, 255), 6)
    im.save(path)
def overlay_b(path):
    im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 1530, 1080, 1920), fill=(10, 6, 3, 255))
    d.rounded_rectangle((110, 1590, 970, 1760), 70, fill=(196, 38, 38, 255), outline=(255, 255, 255, 255), width=6)
    d.polygon([(190, 1640), (190, 1710), (250, 1675)], fill=(255, 255, 255, 255))
    f = ImageFont.truetype(FONT, 78); d.text((600, 1672), ar('شاهد القصة كاملة'), font=f, fill=(255, 255, 255, 255), anchor='mm')
    f2 = ImageFont.truetype(FONT, 46); shadowtext(d, (540, 1830), 'الفيديو الطويل على القناة', f2, (255, 226, 130, 255), 5)
    im.save(path)

def build(key):
    sp = SHORTS[key]; segs = sp['segs']; n = len(segs)
    files = []
    for s in segs:
        if s[0] not in files: files.append(s[0])
    ins = []
    for f in files: ins += ['-i', SRC + f]
    ia = OUT + f'{key}_a.png'; ib = OUT + f'{key}_b.png'; overlay_a(sp['title'], ia); overlay_b(ib)
    ins += ['-loop', '1', '-i', ia, '-loop', '1', '-i', ib]
    na, nb = len(files), len(files) + 1
    total = sum(e - s for _, s, e, _ in segs)
    fc = []
    for i, (f, s, e, cx) in enumerate(segs):
        k = files.index(f); d = e - s; x0 = int(min(max(cx - 360, 0), 560))
        fc.append(f'[{k}:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps=30,split=2[a{i}][b{i}]')
        fc.append(f'[a{i}]crop=406:720:437:0,scale=270:480,gblur=sigma=7,scale=1080:1920,eq=brightness=-0.22:saturation=1.05[bg{i}]')
        fc.append(f'[b{i}]crop=720:720:{x0}:0,scale=1080:1080:flags=lanczos[fg{i}]')
        fc.append(f'[bg{i}][fg{i}]overlay=0:420[v{i}]')
        fc.append(f'[{k}:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,afade=in:d=0.04,afade=out:st={d - 0.04:.3f}:d=0.04[au{i}]')
    fc.append(''.join(f'[v{i}][au{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=1[vc][ac]')
    fc.append(f'[vc]drawbox=x=0:y=416:w=1080:h=4:color=0xE2AC46@1:t=fill,drawbox=x=0:y=1500:w=1080:h=4:color=0xE2AC46@1:t=fill,fade=t=in:d=0.3[vd]')
    fc.append(f'[{na}:v]format=rgba[oa]; [{nb}:v]format=rgba,fade=t=in:st={total - 4.0:.2f}:d=0.5:alpha=1[ob]')
    fc.append('[vd][oa]overlay=0:0:shortest=1[v1]; [v1][ob]overlay=0:0:shortest=1,format=yuv420p[vf]')
    fc.append(f'[ac]afade=t=out:st={total - 0.35:.2f}:d=0.35,volume=1.15,alimiter=limit=0.93[af]')
    out = OUT + f'Short_{key}.mp4'
    cmd = [FF, '-y', '-loglevel', 'error'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[vf]', '-map', '[af]', '-t', f'{total:.2f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-maxrate', '8M', '-bufsize', '12M',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True); print(key, round(total, 2), out)

if __name__ == '__main__':
    for k in (sys.argv[1:] or SHORTS): build(k)
