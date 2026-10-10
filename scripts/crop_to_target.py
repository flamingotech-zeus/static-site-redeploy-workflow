# -*- coding: utf-8 -*-
"""统一裁剪：去掉底部 AI 水印带 -> 按目标比例中心裁剪 -> 缩放 -> 覆盖目标文件（旧图自动备份）

用法：改 REFINE / TARGETS / TW,TH / BACKUP 后运行。
"""
import os, shutil
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
REFINE = os.path.join(BASE, '精修-final-20260917')          # 精修原图目录（<图位>.png）
SITE = r'D:\跨境电商项目\06-官网建设\02-网站源代码'
BACKUP = os.path.join(BASE, 'img-backup-20260917')
WATERMARK_CUT = 0.055      # 底部水印带比例
TW, TH = 1920, 800         # 目标尺寸（2.4:1 通栏横幅）；案例卡用 1200,900；文章头图 1200,514；og 1200,630
QUALITY = 88

TARGETS = {
    'assets/img/hero/news-main.jpg':        'news-main.png',
    'assets/img/people/collab-workshop.jpg': 'collab-workshop.png',
    # ... 其余图位
}

os.makedirs(BACKUP, exist_ok=True)
for rel, fname in TARGETS.items():
    src = os.path.join(REFINE, fname)
    dst = os.path.join(SITE, *rel.split('/'))
    if os.path.exists(dst):
        shutil.copy2(dst, os.path.join(BACKUP, os.path.basename(rel)))
    im = Image.open(src).convert('RGB')
    w, h = im.size
    im = im.crop((0, 0, w, h - int(h * WATERMARK_CUT)))       # 去水印带
    w2, h2 = im.size
    th = round(w2 / (TW / TH))
    if th <= h2:
        top = (h2 - th) // 2                                  # 主体居中 -> 中心裁剪
        im = im.crop((0, top, w2, top + th))
    else:
        tw = round(h2 * TW / TH)
        left = (w2 - tw) // 2
        im = im.crop((left, 0, left + tw, h2))
    im = im.resize((TW, TH), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
    print(f'{rel}: {im.size} {os.path.getsize(dst)//1024}KB')
print('提示：接着务必更新 HTML 里这些图片引用的 ?v=YYYYMMDD 指纹，再上传。')
