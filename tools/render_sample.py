#!/usr/bin/env python3
"""Render a 30-second visual style test for the time-history narration.

The audio is intentionally kept outside the repo; the renderer receives it as an
argument so the GitHub-uploaded source does not need to be duplicated here.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
from pathlib import Path

import av
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

W, H = 1280, 720
FPS = 24
DURATION = 31.5
DARK = (35, 33, 30, 255)
CREAM = (241, 218, 177, 255)
PAPER = (245, 231, 201, 255)
RED = (187, 43, 36, 255)
BLUE = (39, 92, 112, 255)
YELLOW = (240, 180, 61, 255)

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def ar(text: str) -> str:
    """Shape Arabic for Pillow's left-to-right bitmap renderer."""
    return get_display(arabic_reshaper.reshape(text))


def draw_ar(draw: ImageDraw.ImageDraw, xy, text, size, fill=DARK, bold=False,
            anchor="mm", stroke=0, stroke_fill=None):
    f = font(size, bold)
    draw.text(xy, ar(text), font=f, fill=fill, anchor=anchor,
              stroke_width=stroke, stroke_fill=stroke_fill or fill)


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def clamp01(x):
    return max(0.0, min(1.0, x))


def alpha_over(base: Image.Image, layer: Image.Image) -> Image.Image:
    return Image.alpha_composite(base.convert("RGBA"), layer.convert("RGBA"))


def crop_bg(img: Image.Image, t: float, drift_x=0.0, drift_y=0.0) -> Image.Image:
    """Cover 16:9 canvas with a gentle documentary-camera drift."""
    im = img.resize((W + 40, H + 24), Image.Resampling.LANCZOS)
    x = int(20 + drift_x * math.sin(t * 0.21))
    y = int(12 + drift_y * math.sin(t * 0.17 + 0.4))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def rounded(draw, box, radius, fill, outline=DARK, width=5):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paper_card(img: Image.Image, center, size, text, color=PAPER, angle=0,
               text_size=30, accent=None):
    cw, ch = size
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    # Slightly uneven paper edge.
    pts = [(5, 7), (cw - 6, 2), (cw - 2, ch - 9), (8, ch - 3)]
    d.polygon(pts, fill=color, outline=DARK)
    if accent:
        d.line((16, ch - 14, cw - 16, ch - 14), fill=accent, width=7)
    draw_ar(d, (cw // 2, ch // 2 - (5 if accent else 0)), text,
            text_size, fill=DARK, bold=True)
    card = card.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    img.alpha_composite(card, (int(center[0] - card.width / 2), int(center[1] - card.height / 2)))


def draw_sun(draw, center, radius, alpha=255):
    x, y = center
    col = (255, 210, 80, alpha)
    for i in range(16):
        a = i * math.pi / 8
        r1, r2 = radius + 10, radius + 32
        draw.line((x + math.cos(a) * r1, y + math.sin(a) * r1,
                   x + math.cos(a) * r2, y + math.sin(a) * r2), fill=col, width=5)
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=col, outline=(80, 57, 37, alpha), width=4)


def draw_clock(draw, center, r, hand_angle, color=PAPER, label=None):
    x, y = center
    draw.ellipse((x-r, y-r, x+r, y+r), fill=color, outline=DARK, width=7)
    for i in range(12):
        a = i * math.pi / 6
        x1, y1 = x + math.cos(a) * (r - 14), y + math.sin(a) * (r - 14)
        x2, y2 = x + math.cos(a) * (r - 4), y + math.sin(a) * (r - 4)
        draw.line((x1, y1, x2, y2), fill=DARK, width=3)
    a = hand_angle
    draw.line((x, y, x + math.cos(a) * r * .54, y + math.sin(a) * r * .54), fill=RED, width=6)
    draw.line((x, y, x + math.cos(a + 1.3) * r * .36, y + math.sin(a + 1.3) * r * .36), fill=DARK, width=7)
    draw.ellipse((x-7, y-7, x+7, y+7), fill=RED)
    if label:
        draw_ar(draw, (x, y + r + 28), label, 22, bold=True)


def draw_x(draw, center, size, color=RED, width=10):
    x, y = center
    draw.line((x-size, y-size, x+size, y+size), fill=color, width=width)
    draw.line((x+size, y-size, x-size, y+size), fill=color, width=width)


def draw_question(draw, x, y, scale=1.0, alpha=255):
    f = font(int(112 * scale), True)
    col = (RED[0], RED[1], RED[2], alpha)
    draw.text((x, y), "?", font=f, fill=col, anchor="mm", stroke_width=4, stroke_fill=DARK)


def draw_character(img: Image.Image, center, scale=1.0, t=0.0, pose="confused",
                   mouth=0.0, flip=False, alpha=255):
    """A reusable puppet drawn in the supplied reference's thick-ink collage style."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = center
    s = scale
    bob = math.sin(t * 7.0) * 3.5 * s
    cy += bob
    outline = (28, 27, 24, alpha)
    skin = (224, 190, 145, alpha)
    shirt = (36, 36, 33, alpha)
    white = (247, 239, 216, alpha)
    # Ground shadow.
    d.ellipse((cx - 92*s, cy + 130*s, cx + 92*s, cy + 155*s), fill=(20, 17, 14, int(alpha*.28)))
    # Body and limbs.
    body_y = cy + 62*s
    d.rounded_rectangle((cx-70*s, body_y, cx+70*s, body_y+116*s), radius=int(35*s), fill=shirt, outline=outline, width=max(2,int(7*s)))
    if pose in ("point", "panic"):
        arm_ang = -0.78 if pose == "point" else -2.1
        ax = cx + math.cos(arm_ang) * 115*s
        ay = body_y + math.sin(arm_ang) * 90*s
        d.line((cx-42*s, body_y+35*s, ax, ay), fill=outline, width=max(6,int(17*s)))
        d.ellipse((ax-13*s, ay-13*s, ax+13*s, ay+13*s), fill=skin, outline=outline, width=max(2,int(5*s)))
        if pose == "point":
            d.line((ax, ay, ax+38*s, ay-8*s), fill=skin, width=max(5,int(11*s)))
    else:
        d.line((cx-40*s, body_y+28*s, cx-95*s, body_y+105*s), fill=outline, width=max(6,int(17*s)))
        d.line((cx+40*s, body_y+28*s, cx+95*s, body_y+105*s), fill=outline, width=max(6,int(17*s)))
    # Head + ears.
    hy = cy - 20*s
    d.ellipse((cx-25*s-28*s, hy-15*s, cx-25*s+8*s, hy+22*s), fill=skin, outline=outline, width=max(2,int(5*s)))
    d.ellipse((cx+17*s, hy-15*s, cx+17*s+36*s, hy+22*s), fill=skin, outline=outline, width=max(2,int(5*s)))
    d.ellipse((cx-82*s, hy-78*s, cx+82*s, hy+82*s), fill=skin, outline=outline, width=max(2,int(7*s)))
    # Hair cap with slightly angular fringe.
    hair = [(cx-76*s, hy-38*s), (cx-61*s, hy-88*s), (cx+22*s, hy-103*s),
            (cx+72*s, hy-72*s), (cx+66*s, hy-41*s), (cx+27*s, hy-57*s),
            (cx-7*s, hy-47*s), (cx-38*s, hy-39*s)]
    d.polygon(hair, fill=shirt, outline=outline)
    d.line((cx-52*s, hy-69*s, cx+21*s, hy-75*s), fill=(82, 78, 66, alpha), width=max(1,int(3*s)))
    # Eyebrows and eyes, with mild deadpan asymmetry.
    look = math.sin(t*1.15) * 5*s
    brow_y = hy - 4*s
    d.line((cx-51*s, brow_y-9*s, cx-20*s, brow_y-14*s), fill=outline, width=max(2,int(7*s)))
    d.line((cx+18*s, brow_y-12*s, cx+49*s, brow_y-4*s), fill=outline, width=max(2,int(7*s)))
    for ex in (cx-35*s, cx+35*s):
        d.ellipse((ex-18*s, hy+4*s, ex+18*s, hy+27*s), fill=white, outline=outline, width=max(1,int(3*s)))
        px = ex + (look if ex < cx else -look*.55)
        py = hy + 16*s
        if int(t*3.2) % 19 == 0:
            # A quick blink every few seconds.
            d.line((ex-13*s, hy+16*s, ex+13*s, hy+16*s), fill=outline, width=max(2,int(4*s)))
        else:
            d.ellipse((px-6*s, py-6*s, px+6*s, py+6*s), fill=outline)
    # Nose and expressive mouth.
    d.line((cx+2*s, hy+25*s, cx-3*s, hy+43*s, cx+10*s, hy+44*s), fill=outline, width=max(1,int(3*s)))
    m = max(0.0, min(1.0, mouth))
    if pose == "panic":
        d.ellipse((cx-16*s, hy+51*s-18*m*s, cx+21*s, hy+51*s+23*m*s), fill=outline)
        d.ellipse((cx-9*s, hy+51*s-7*m*s, cx+14*s, hy+51*s+14*m*s), fill=(221, 94, 77, alpha))
    else:
        d.arc((cx-28*s, hy+37*s, cx+28*s, hy+68*s + 16*m*s), start=12, end=168, fill=outline, width=max(2,int(5*s)))
        if m > .38:
            d.ellipse((cx-17*s, hy+49*s, cx+18*s, hy+54*s+19*m*s), fill=outline)
    # Small comic motion lines.
    if pose == "point":
        d.line((cx+104*s, body_y+10*s, cx+125*s, body_y-4*s), fill=RED, width=max(2,int(5*s)))
        d.line((cx+108*s, body_y+28*s, cx+137*s, body_y+24*s), fill=RED, width=max(2,int(5*s)))
    if pose == "panic":
        for a in (-2.5, -1.9, -1.3, -0.7):
            x1 = cx + math.cos(a)*100*s; y1 = hy + math.sin(a)*100*s
            x2 = cx + math.cos(a)*125*s; y2 = hy + math.sin(a)*125*s
            d.line((x1,y1,x2,y2), fill=YELLOW, width=max(2,int(4*s)))
    # Flip only after drawing (not used for the first sample, kept for puppet reuse).
    if flip:
        lay = lay.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if alpha < 255:
        lay.putalpha(lay.getchannel("A"))
    img.alpha_composite(lay)


def draw_speech_bubble(img, center, text, t, scale=1.0):
    # pop-in scale gives the card a hand-animated feel
    sc = ease(clamp01(t * 7.0))
    if sc <= 0: return
    w, h = int(320*scale*sc), int(130*scale*sc)
    x, y = int(center[0]), int(center[1])
    layer = Image.new("RGBA", img.size, (0,0,0,0)); d=ImageDraw.Draw(layer)
    d.rounded_rectangle((x-w//2, y-h//2, x+w//2, y+h//2), radius=int(28*scale), fill=CREAM, outline=DARK, width=max(3,int(6*scale)))
    d.polygon([(x-w//4,y+h//2),(x-w//7,y+h//2+46),(x,y+h//2)], fill=CREAM, outline=DARK)
    draw_ar(d,(x,y-3),text,int(29*scale),bold=True)
    img.alpha_composite(layer)


def load_audio_envelope(path: str, duration: float):
    c = av.open(path)
    st = c.streams.audio[0]
    chunks=[]
    for fr in c.decode(st):
        arr = fr.to_ndarray()
        if arr.ndim == 2: arr = arr.mean(axis=0)
        chunks.append(arr.astype(np.float32))
    a=np.concatenate(chunks)
    if np.max(np.abs(a)) > 2: a=a/32768.0
    sr=st.rate
    n=int(duration*FPS)+2
    env=[]
    for i in range(n):
        lo=int(i/FPS*sr); hi=min(int((i+1)/FPS*sr),len(a))
        x=a[lo:hi] if hi>lo else a[:1]
        env.append(float(np.sqrt(np.mean(x*x))))
    env=np.array(env)
    # Normalize voice dynamics but keep quiet moments quiet.
    lo, hi=np.percentile(env,[10,98])
    return np.clip((env-lo)/max(1e-6,hi-lo),0,1)


def draw_overlay_title(img, t):
    layer=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(layer)
    draw_ar(d,(W//2,82),"كيف عرفنا الوقت؟",48,fill=PAPER,bold=True,stroke=2,stroke_fill=DARK)
    d.line((W//2-225,123,W//2+225,123),fill=YELLOW,width=7)
    img.alpha_composite(layer)


def frame_at(t, env, bgs):
    # Choose/crossfade realistic plates.
    if t < 8.7:
        bg=crop_bg(bgs[0],t,drift_x=9,drift_y=4)
    elif t < 12.4:
        p=ease((t-8.2)/1.0)
        a=crop_bg(bgs[0],t,drift_x=9,drift_y=4)
        b=crop_bg(bgs[1],t,drift_x=14,drift_y=6)
        bg=Image.blend(a,b,p)
    elif t < 21.4:
        bg=crop_bg(bgs[1],t,drift_x=18,drift_y=8)
    else:
        p=ease((t-20.8)/1.0)
        a=crop_bg(bgs[1],t,drift_x=14,drift_y=6)
        b=crop_bg(bgs[2],t,drift_x=11,drift_y=5)
        bg=Image.blend(a,b,p)
    img=bg.convert("RGBA")
    d=ImageDraw.Draw(img)
    # Warm vignette / paper-film treatment.
    vign=Image.new("RGBA",(W,H),(0,0,0,0)); vd=ImageDraw.Draw(vign)
    vd.rectangle((0,0,W,H),fill=(22,18,14,18))
    img=alpha_over(img,vign)
    d=ImageDraw.Draw(img)

    # Background-specific animated sun and simple collage marks.
    if 7.8 <= t < 21.2:
        sun_x=1020 + 35*math.sin(t*.8)
        sun_y=115 + 26*math.sin(t*.55)
        draw_sun(d,(int(sun_x),int(sun_y)),42,235)
    if t >= 21.0:
        # Moon / carved marks to bridge from day to ancient timekeeping.
        moonx, moony=1040,132
        d.ellipse((moonx-42,moony-42,moonx+42,moony+42),fill=(230,223,191,235),outline=DARK,width=5)
        d.ellipse((moonx-20,moony-45,moonx+42,moony+30),fill=(53,62,69,210))
        for i in range(4):
            d.line((175+i*35,585,195+i*35,572),fill=(49,39,28,180),width=4)

    # Opening hook: character wakes from the real photograph.
    if t < 8.7:
        pop=ease((t-.15)/.65)
        x=545 + 44*math.sin(t*1.8)
        y=493 - 80*pop
        pose="panic" if 3.0<t<5.2 else "confused"
        draw_character(img,(x,y),scale=1.04,t=t,pose=pose,mouth=env[int(t*FPS)] if int(t*FPS)<len(env) else .2)
        # Physical props with red crosses.
        if t>=2.35:
            rounded(d,(90,148,225,250),24,(37,40,43,255),outline=DARK,width=6)
            d.ellipse((105,164,210,235),fill=(80,83,84,255))
            draw_x(d,(157,200),29,RED,9)
        if t>=2.75:
            draw_clock(d,(330,193),55,hand_angle=t*.2,label="")
            draw_x(d,(330,193),38,RED,9)
        if t>=3.1:
            # Alarm bell/silhouette
            d.rectangle((395,163,472,235),fill=(82,75,66,255),outline=DARK,width=6)
            d.ellipse((386,143,429,180),fill=(82,75,66,255),outline=DARK,width=5)
            d.ellipse((438,143,481,180),fill=(82,75,66,255),outline=DARK,width=5)
            draw_x(d,(435,201),34,RED,9)
        if t < 2.8:
            paper_card(img,(990,88),(405,96),"صحيت… بس الساعة فين؟",angle=-2,text_size=28,accent=RED)
        elif t < 8.7:
            paper_card(img,(965,93),(355,92),"سبعة الصبح؟ ولا تلاتة العصر؟",angle=2,text_size=24,accent=YELLOW)
        if 4.0 < t < 8.7:
            # floating question marks with a little sway
            draw_question(d, 750+20*math.sin(t*3), 180, .7)
            draw_question(d, 880+14*math.sin(t*2.2), 275, .45)
    elif t < 12.8:
        # Real sunrise + character tries to read the sun like a clock.
        x=470+50*math.sin(t*2.4); y=487
        draw_character(img,(x,y),scale=1.0,t=t,pose="point",mouth=env[min(int(t*FPS),len(env)-1)])
        paper_card(img,(190,110),(260,86),"بتطلع الشمس…",angle=-3,text_size=29,accent=YELLOW)
        if t>9.2:
            draw_ar(d,(1032,260),"؟",84,fill=RED,bold=True,stroke=2,stroke_fill=DARK)
        # Guessing dial.
        d.ellipse((765,420,960,615),fill=(242,228,194,224),outline=DARK,width=6)
        for i in range(12):
            a=i*math.pi/6
            d.line((862+math.cos(a)*72,517+math.sin(a)*72,862+math.cos(a)*87,517+math.sin(a)*87),fill=DARK,width=4)
        ang=(t-8.7)*3.4
        d.line((862,517,862+math.cos(ang)*70,517+math.sin(ang)*70),fill=RED,width=9)
        draw_ar(d,(862,558),"تخمين وبس",25,bold=True)
    elif t < 21.4:
        # The visual punchline: the world keeps moving, but the character has no reference.
        p=ease((t-12.8)/.8)
        x=570+45*math.sin(t*1.5); y=486-18*p
        pose="panic" if 16.2<t<18.8 else "confused"
        draw_character(img,(x,y),scale=1.12,t=t,pose=pose,mouth=env[min(int(t*FPS),len(env)-1)])
        paper_card(img,(980,110),(330,100),"اليوم موجود…",angle=-2,text_size=34,accent=BLUE)
        paper_card(img,(960,220),(380,104),"بس الوقت؟",angle=2,text_size=38,accent=RED)
        # Giant invisible clock outline / orbit to show abstract concept.
        d.ellipse((730,278,1120,668),outline=(245,230,190,140),width=5)
        for i in range(8):
            a=i*math.pi/4 + t*.4
            d.line((925+math.cos(a)*165,473+math.sin(a)*165,925+math.cos(a)*190,473+math.sin(a)*190),fill=(240,220,174,150),width=4)
        if 16.0<t<20.0:
            draw_speech_bubble(img,(315,172),"طيب… الساعة كام؟",t-16.0,scale=.92)
        if 18.7<t<21.4:
            # arrow into the historical explanation
            d.line((150,600,400,600),fill=RED,width=8)
            d.polygon([(400,600),(365,580),(365,620)],fill=RED)
            draw_ar(d,(270,650),"نرجع للبداية",28,fill=PAPER,bold=True,stroke=2,stroke_fill=DARK)
    else:
        # History montage: moon marks / ancient sun / a hand-drawn ruler.
        x=460+80*math.sin(t*1.8); y=474
        draw_character(img,(x,y),scale=1.02,t=t,pose="point",mouth=env[min(int(t*FPS),len(env)-1)])
        if 21.0<t<25.8:
            paper_card(img,(180,100),(300,88),"من القمر…",angle=-4,text_size=31,accent=BLUE)
            draw_clock(d,(980,475),92,hand_angle=(t-21)*.85,color=(240,224,179,245),label="")
            d.line((760,535,1150,535),fill=YELLOW,width=8)
            for i in range(8):
                xx=780+i*48
                d.line((xx,535,xx,520 if i%2==0 else 510),fill=DARK,width=4)
            draw_ar(d,(955,640),"إلى قياس الوقت",30,fill=PAPER,bold=True,stroke=2,stroke_fill=DARK)
        elif t < 28.3:
            paper_card(img,(185,102),(355,94),"اخترعنا طريقة نقيسه",angle=2,text_size=28,accent=RED)
            # comic measuring tape
            d.line((160,570,840,570),fill=PAPER,width=30)
            for i in range(12):
                xx=180+i*58
                d.line((xx,555,xx,585),fill=DARK,width=4)
            draw_ar(d,(535,615),"مش اخترعنا الوقت نفسه",26,fill=PAPER,bold=True,stroke=2,stroke_fill=DARK)
        else:
            draw_overlay_title(img,t)
            paper_card(img,(980,590),(380,92),"العينة الأولى",angle=-3,text_size=30,accent=YELLOW)
            draw_clock(d,(875,280),125,hand_angle=(t-28.3)*2.8,color=(240,224,179,245),label="")
            draw_ar(d,(875,280),"60",57,fill=DARK,bold=True)

    # Captions are deliberately short and cleaned from the noisy ASR transcript.
    captions=[
        (0.0,2.8,"خير إنك صحيت اليوم؟"),
        (2.8,4.9,"ما في تلفون… ولا ساعة… ولا منبّه"),
        (4.9,8.7,"ما في حتى رقم يقولك: سبعة الصبح ولا تلاتة العصر"),
        (8.7,12.7,"بتطلع الشمس… وبتحاول التخمين وبس"),
        (12.7,16.4,"الغريب إن اليوم موجود… بس الوقت مش واضح"),
        (16.4,20.1,"فكيف عرف البشر الوقت؟"),
        (20.1,26.1,"ما اخترعنا الوقت… اخترعنا طريقة نقيسه"),
        (26.1,31.5,"من القمر… إلى الساعات"),
    ]
    active=None
    for a,b,txt in captions:
        if a<=t<b: active=txt; break
    if active:
        # Subtle translucent caption plate, always readable over photo.
        plate=Image.new("RGBA",(W,90),(25,23,20,0)); pd=ImageDraw.Draw(plate)
        pd.rounded_rectangle((90,8,W-90,82),radius=22,fill=(25,23,20,195),outline=(243,221,178,210),width=2)
        draw_ar(pd,(W//2,45),active,27,fill=(250,236,204,255),bold=True)
        img.alpha_composite(plate,(0,H-108))
    # A small grain layer helps the vector puppet belong to the photos.
    rng=np.random.default_rng(int(t*FPS)+91)
    noise=rng.normal(0,2.2,(H,W,1)).astype(np.int16)
    arr=np.asarray(img.convert("RGB"),dtype=np.int16)
    arr=np.clip(arr+noise,0,255).astype(np.uint8)
    return Image.fromarray(arr,"RGB")


def render(audio: str, output: str):
    bgs=[Image.open(ASSET/n).convert("RGB") for n in ("scene-bedroom-realistic.jpg","scene-sunrise-city.jpg","scene-ancient-desert.jpg")]
    env=load_audio_envelope(audio,DURATION)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(Path(output).parent,exist_ok=True)
    cmd=[ffmpeg,"-y","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-i",audio,"-t",str(DURATION),"-c:v","libx264","-preset","medium",
         "-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
         "-movflags","+faststart","-shortest",output]
    print("Rendering", output)
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(int(DURATION*FPS)):
            t=i/FPS
            fr=frame_at(t,env,bgs)
            proc.stdin.write(np.asarray(fr).tobytes())
            if i%24==0: print(f"{t:5.1f}s / {DURATION:.1f}s",flush=True)
    finally:
        proc.stdin.close()
        code=proc.wait()
    if code:
        raise SystemExit(code)
    print("Done",output)


if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--audio",required=True)
    ap.add_argument("--output",default=str(ROOT/"renders/time-origin-sample.mp4"))
    args=ap.parse_args()
    render(args.audio,args.output)
