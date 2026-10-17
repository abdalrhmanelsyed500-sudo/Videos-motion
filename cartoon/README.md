# برنامج كرتوني — RigKit (نظام Rig ثنائي الأبعاد للرسوم المتحركة)

نظام حركة (Rig) برمجي دقيق لبرنامج أطفال: شخصيتان (**زاكي** و**لولو**)، كل شخصية بنسختين (أمامي + جانبي)، عظام (bones) وتسلسل هرمي،
IK للأطراف، وجه إجرائي (عيون/حواجب/فم + 14 شكل نطق)، حركة ثانوية بالنوابض (الخصلة/الضفائر)، مشي جانبي مع تثبيت القدم على الأرض،
مزامنة شفاه من الصوت، ومجموعة فحوصات جودة آلية.

English: a code-driven, data-driven 2D character rig + animation toolkit for a kids' cartoon (bones, IK, procedural face/visemes,
spring secondary motion, foot-locked walk cycle, audio lip-sync, automatic QA).

## الملفات
| المسار | المحتوى |
|---|---|
| `rigkit/vec.py` | رسّام متجهات (supersampling) لرسم الأجزاء بلا حواف مكسورة |
| `rigkit/chars.py` | تصميم الشخصيتين وكل الأجزاء المنفصلة (رأس، جذع، حوض، ذراع، ساعد، 4 أيدي، فخذ، ساق، حذاء، خصلة/ضفيرة) |
| `rigkit/build.py` | يبني `rig.json` + صور الأجزاء لكل (شخصية × منظور) |
| `rigkit/rig.py` | محرك الـRig: FK، IK ثنائي العظام تحليلي، حدود المفاصل، ترتيب الطبقات، تبديل الأيدي، رسم |
| `rigkit/face.py` | الوجه الإجرائي: العين (نظر، رمش، تحديق، ميل الجفن)، الحاجب، الفم (visemes) |
| `rigkit/anim.py` | الإيزينغ، المفاتيح، دمج الأوضاع، الرمش، النوابض، مزامنة الشفاه، **Walker** (المشي) |
| `rigkit/episode.py` | مخرج الحلقة التجريبية (إيماءات، قفزة squash/stretch، استدارة، كاميرا) |
| `rigkit/bg.py` | خلفية الحديقة بطبقات Parallax |
| `rigkit/audio.py` | مكسر الصوت: الصوت + مؤثرات (خطوات متزامنة مع هبوط القدم) بدون موسيقى |
| `rigkit/validate.py` | فحوصات الجودة → `QA_REPORT.md` |
| `rigkit/sheets.py` | لوحة الأجزاء + مخطط العظام |
| `out/rigs/<char>_<view>/` | ملفات `rig.json` وصور الأجزاء PNG (شفافة) |
| `RIG_SPEC.md`, `ANIMATION_GUIDE.md` | مواصفات الـRig ودليل التحريك |

## التشغيل
```
pip install numpy opencv-python-headless scipy imageio-ffmpeg pillow arabic-reshaper python-bidi
python build_all.py          # يبني الـRig، الصوت، الفيديو، الفحص، اللوحات
```
