# -*- coding: utf-8 -*-
"""dHash 配对：把「无图位信息」的并行生成结果与候选原图对应起来。

为什么需要：ImageGen 并行生成的文件名 = 提示词前缀 + 时间戳，并行时同秒完成会同名互相覆盖，
返回顺序也不等于落盘顺序。用感知哈希做全排列最优匹配最可靠。

用法：改 BASE / REFINE / SEL 后运行；匹配成功的文件会被重命名为 <slot>.png。
"""
import os, json, itertools
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
REFINE = os.path.join(BASE, '精修-final')          # 待配对的精修图目录

# slot -> (候选所在目录, 候选编号)
SEL = {
    'collab-workshop':    ('2-collab-workshop', 1),
    'consult-product':    ('3-consult-product', 1),
    'handshake-workshop': ('4-handshake-workshop', 2),
    'mentor-guide':       ('7-mentor-guide', 2),
    'news-main':          ('1-news-main', 1),
    'team-office':        ('5-team-office', 2),
    'tour-warehouse':     ('6-tour-warehouse', 2),
}


def dhash(path, hs=16, vs=16):
    im = Image.open(path).convert('L').resize((hs + 1, vs), Image.LANCZOS)
    px = list(im.getdata())
    return [px[r * (hs + 1) + c] < px[r * (hs + 1) + c + 1]
            for r in range(vs) for c in range(hs)]


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


srcs = {s: (os.path.join(BASE, d, f'{s}-候选{n}.png'), None) for s, (d, n) in SEL.items()}
srcs = {s: (p, dhash(p)) for s, (p, _) in srcs.items()}
refs = sorted(f for f in os.listdir(REFINE) if f.lower().endswith('.png'))
refh = {f: dhash(os.path.join(REFINE, f)) for f in refs}
slots = list(srcs.keys())

best = None
# 支持「精修图数量 < 图位数」（有图丢失）的情况
for subset in itertools.combinations(slots, len(refs)):
    for perm in itertools.permutations(refs, len(subset)):
        cost = sum(hamming(srcs[s][1], refh[f]) for s, f in zip(subset, perm))
        if best is None or cost < best[0]:
            best = (cost, subset, perm)

cost, subset, perm = best
missing = [s for s in slots if s not in subset]
print(f'最优匹配总距离 = {cost} | 丢失未匹配 = {missing}')
mapping = {}
for s, f in zip(subset, perm):
    d = hamming(srcs[s][1], refh[f])
    mapping[s] = f
    print(f'  {s:22s} dist={d:3d}  <- {f}')
    dst = os.path.join(REFINE, s + '.png')
    if os.path.exists(dst):
        os.remove(dst)
    os.rename(os.path.join(REFINE, f), dst)
print('已重命名；距离普遍 <=10 才可信，若某张明显偏大说明可能配对错误或图丢失')
json.dump({'mapping': mapping, 'missing': missing},
          open(os.path.join(BASE, '_refine_map.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
