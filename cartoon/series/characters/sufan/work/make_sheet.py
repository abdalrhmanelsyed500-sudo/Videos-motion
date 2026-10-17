import sys
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
FONT='/home/user/Videos-motion/cartoon/fonts/Amiri-Bold.ttf'
def ar(s): return get_display(arabic_reshaper.reshape(s))
def F(sz): return ImageFont.truetype(FONT, sz)
W,H=2600,1900
sh=Image.new('RGB',(W,H),(250,244,232)); d=ImageDraw.Draw(sh)
d.rectangle((0,0,W,110),fill=(70,56,44))
d.text((W-40,55),ar('صوفان — ورقة الشخصية (مسودة 1 للاعتماد) — رحلة صوف'),font=F(54),fill=(255,240,214),anchor='rm')
d.text((40,55),'SUFAN — Character Model Sheet · Draft 1',font=F(46),fill=(255,240,214),anchor='lm')
def card(im,x,y,w,h,title_ar,title_en):
    d.rounded_rectangle((x,y,x+w,y+h),24,fill=(236,236,236),outline=(190,175,150),width=3)
    r=im.convert('RGB'); k=min((w-30)/r.width,(h-120)/r.height); r=r.resize((int(r.width*k),int(r.height*k)),Image.LANCZOS)
    sh.paste(r,(x+(w-r.width)//2,y+10))
    d.text((x+w//2,y+h-70),ar(title_ar),font=F(40),fill=(70,56,44),anchor='mm')
    d.text((x+w//2,y+h-28),title_en,font=F(30),fill=(120,100,80),anchor='mm')
V=[('master_front','أمامي','Front'),('master_34','ثلاثة أرباع','3/4'),('master_side','جانبي','Side'),('master_back','خلفي','Back')]
cw=620; x=40
for n,a,e in V:
    card(Image.open(n+'.png'),x,140,cw,860,a,e); x+=cw+25
# palette
px,py=40,1030
d.text((px+10,py+10),ar('لوحة الألوان المعتمدة'),font=F(40),fill=(70,56,44))
P=[('#FEEAD3','الصوف','Wool'),('#F4D1B8','ظل الصوف والوجه','Wool shade'),('#D88487','باطن الأذن','Ear inner'),('#F2BAA5','الجلد (يد/ساق)','Skin'),
   ('#A07B58','القبعة','Hat'),('#563725','شريط القبعة / الحذاء','Hat band / boots'),('#73713B','الصدرية','Vest'),('#575A31','ظل الصدرية','Vest shade'),
   ('#AE8E52','بطانة الصدرية','Under-vest'),('#D7AF56','القميص','Shirt'),('#030202','النظارة والعيون','Glasses / pupils')]
for i,(hx,a,e) in enumerate(P):
    cx=px+(i%6)*185; cy=py+70+(i//6)*195
    d.rounded_rectangle((cx,cy,cx+165,cy+110),16,fill=hx,outline=(120,100,80),width=2)
    d.text((cx+82,cy+128),hx,font=F(28),fill=(60,50,40),anchor='mm')
    d.text((cx+82,cy+158),ar(a),font=F(26),fill=(60,50,40),anchor='mm')
# expressions
ex=[('exp_laugh','ضحك','Laugh'),('exp_surprise','دهشة','Surprise'),('exp_worried','قلق','Worried')]
ex_x=1180; d.text((ex_x+10,py+10),ar('تعبيرات الوجه (3 من 6 — الباقي في الدفعة التالية)'),font=F(40),fill=(70,56,44))
for i,(n,a,e) in enumerate(ex):
    im=Image.open(n+'.png').crop((0,0,925,900))
    card(im,ex_x+i*270,py+70,255,420,a,e)
# props
pr_x=2010; d.text((pr_x+10,py+10),ar('الأغراض'),font=F(40),fill=(70,56,44))
for i,(n,a,e) in enumerate([('prop_backpack2','حقيبة الظهر','Backpack'),('prop_stick2','العصا','Stick')]):
    card(Image.open(n+'.png'),pr_x+i*290,py+70,275,420,a,e)
# notes
ny=1560
d.text((W-40,ny),ar('الملف الشخصي: خبير عملي، صبور لكنه عنيد، يثق بخبرته أكثر من اللازم، لا يسأل عن الطريق، وبينه وبين الأحفاد حب حقيقي.'),font=F(34),fill=(70,56,44),anchor='ra')
d.text((W-40,ny+55),ar('النسب (تقدير بالعين على الأمامي): الرأس بالصوف دون القبعة حوالي 2.5 رأس للجسم كاملًا، وبالقبعة واللحية حوالي 1.9؛ الجسم كروي، ساقان قصيرتان، حذاء بُنّي.'),font=F(34),fill=(70,56,44),anchor='ra')
d.text((W-40,ny+110),ar('ما لا يجوز تغييره: القبعة البنية بشريطها، النظارة الدائرية السوداء، لحية الصوف السحابية، الصدرية الخضراء فوق قميص خردلي، الأذنان الورديتان، الحذاء البني.'),font=F(34),fill=(70,56,44),anchor='ra')
d.text((W-40,ny+165),ar('ملاحظة جودة: أحجام الرأس تختلف قليلًا بين صور التعبيرات (اختلاف ناتج عن التوليد)، وسأعالجه بتثبيت الرأس الأساسي وتركيب العيون والفم كطبقات منفصلة.'),font=F(34),fill=(160,60,40),anchor='ra')
d.text((40,H-40),'Status: DRAFT for approval — not final. Proportions are estimates measured by eye.',font=F(30),fill=(120,100,80),anchor='lm')
sh.save('../sufan_model_sheet_v1.png')
print('ok')
