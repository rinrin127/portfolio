#!/usr/bin/env python3
"""
accessories.py — 猫にかぶせる「被り物・小物」を描くライブラリ

写真の猫は被り物をしていないので、こちらで描いて頭に載せる。
すべて4倍で描いてから縮小しているので、フチがなめらかに出る。

  ANCHOR[name] = (どこに置くか, 本体の幅に対する大きさ, 縦のズレ)
    head … 頭のてっぺん（かぶりもの・帽子・耳・冠）
    face … 顔の中心（めがね・ひげ）
    neck … 首もと（リボン・首輪）
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw

SS = 4  # スーパーサンプリング倍率

WHITE = (255, 255, 255, 255)
PINK = (255, 150, 180, 255)
DEEP_PINK = (238, 92, 140, 255)
GREY = (150, 158, 168, 255)
GREY_D = (112, 121, 133, 255)
RED = (226, 74, 78, 255)
GREEN = (104, 172, 96, 255)
BROWN = (176, 138, 106, 255)
CREAM = (245, 226, 190, 255)
GOLD = (247, 200, 78, 255)
INK = (48, 44, 52, 255)


def _canvas(w: int, h: int):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _done(im: Image.Image, w: int, h: int) -> Image.Image:
    return im.resize((w, h), Image.LANCZOS)


# ------------------------------------------------------------------ 被り物
def shark_hood(w: int) -> Image.Image:
    """サメの被り物。ギザギザの歯が顔まわりを囲む。"""
    h = round(w * 0.86)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.ellipse([W * 0.30, -H * 0.10, W * 0.86, H * 0.34], fill=GREY_D)      # 背びれ
    d.polygon([(W * 0.46, H * 0.20), (W * 0.62, -H * 0.02), (W * 0.72, H * 0.22)], fill=GREY_D)
    d.pieslice([0, H * 0.04, W, H * 1.34], 180, 360, fill=GREY)            # フード本体
    d.pieslice([W * 0.10, H * 0.30, W * 0.90, H * 1.30], 180, 360, fill=(0, 0, 0, 55))
    n = 11                                                                  # 歯
    for i in range(n):
        x0 = W * 0.06 + (W * 0.88) * i / n
        x1 = x0 + (W * 0.88) / n
        y = H * (0.62 - 0.30 * math.cos(math.pi * (i + 0.5) / n) ** 2)
        d.polygon([(x0, y), (x1, y), ((x0 + x1) / 2, y + H * 0.17)], fill=WHITE)
    d.ellipse([W * 0.10, H * 0.30, W * 0.24, H * 0.44], fill=WHITE, outline=INK, width=SS)
    d.ellipse([W * 0.76, H * 0.30, W * 0.90, H * 0.44], fill=WHITE, outline=INK, width=SS)
    d.ellipse([W * 0.15, H * 0.34, W * 0.21, H * 0.41], fill=INK)
    d.ellipse([W * 0.79, H * 0.34, W * 0.85, H * 0.41], fill=INK)
    return _done(im, w, h)


def strawberry_hat(w: int) -> Image.Image:
    """いちごの被り物。"""
    h = round(w * 0.82)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.pieslice([0, H * 0.10, W, H * 1.40], 180, 360, fill=(233, 76, 88, 255))
    for i in range(14):                                                     # つぶつぶ
        a = math.pi * (0.10 + 0.80 * (i % 7) / 6)
        r = 0.34 if i < 7 else 0.20
        cx = W / 2 - W * r * math.cos(a)
        cy = H * 0.66 - H * (r * 1.5) * math.sin(a)
        d.ellipse([cx - W * 0.018, cy - W * 0.026, cx + W * 0.018, cy + W * 0.026], fill=(255, 236, 180, 255))
    d.polygon([(W * 0.34, H * 0.20), (W * 0.50, H * 0.02), (W * 0.66, H * 0.20),
               (W * 0.58, H * 0.24), (W * 0.42, H * 0.24)], fill=GREEN)     # へた
    d.rectangle([W * 0.47, -H * 0.06, W * 0.53, H * 0.08], fill=GREEN)
    return _done(im, w, h)


def bear_hood(w: int) -> Image.Image:
    """くまの被り物。"""
    h = round(w * 0.80)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.16, 0.84):                                                 # 耳
        d.ellipse([W * (cx - 0.16), H * 0.02, W * (cx + 0.16), H * 0.42], fill=BROWN)
        d.ellipse([W * (cx - 0.09), H * 0.12, W * (cx + 0.09), H * 0.34], fill=(226, 188, 156, 255))
    d.pieslice([0, H * 0.14, W, H * 1.40], 180, 360, fill=BROWN)
    d.pieslice([W * 0.12, H * 0.42, W * 0.88, H * 1.30], 180, 360, fill=(0, 0, 0, 45))
    return _done(im, w, h)


def bunny_ears(w: int) -> Image.Image:
    """うさ耳のカチューシャ。"""
    h = round(w * 0.92)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx, tilt in ((0.32, -8), (0.68, 8)):
        ear, ed = _canvas(w, h)
        eW, eH = w * SS, h * SS
        ed.ellipse([eW * (cx - 0.11), eH * 0.02, eW * (cx + 0.11), eH * 0.78], fill=WHITE,
                   outline=(232, 216, 220, 255), width=SS * 2)
        ed.ellipse([eW * (cx - 0.055), eH * 0.12, eW * (cx + 0.055), eH * 0.66], fill=PINK)
        im.alpha_composite(ear.rotate(tilt, resample=Image.BICUBIC, center=(eW * cx, eH * 0.78)))
    d.arc([W * 0.14, H * 0.62, W * 0.86, H * 1.10], 200, 340, fill=(238, 226, 230, 255), width=SS * 5)
    return _done(im, w, h)


def cat_ears(w: int) -> Image.Image:
    """ねこ耳＋小さいリボン。"""
    h = round(w * 0.62)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.26, 0.74):
        d.polygon([(W * (cx - 0.24), H * 0.96), (W * cx, H * 0.08), (W * (cx + 0.24), H * 0.96)],
                  fill=(104, 100, 110, 255))
        d.polygon([(W * (cx - 0.13), H * 0.88), (W * cx, H * 0.32), (W * (cx + 0.13), H * 0.88)], fill=PINK)
    b = bow(round(w * 0.40))
    im.alpha_composite(b.resize((b.width * SS, b.height * SS), Image.LANCZOS),
                       (round(W * 0.56), round(H * 0.04)))
    return _done(im, w, h)


def flower_crown(w: int) -> Image.Image:
    """お花の冠。"""
    h = round(w * 0.44)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    cols = [(255, 214, 120, 255), (255, 236, 190, 255), (255, 186, 200, 255)]
    for i in range(5):
        t = i / 4
        cx, cy = W * (0.10 + 0.80 * t), H * (0.72 - 0.42 * math.sin(math.pi * t))
        r = W * 0.075
        col = cols[i % len(cols)]
        for k in range(6):
            a = k * math.pi / 3
            px, py = cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9
            d.ellipse([px - r * 0.62, py - r * 0.62, px + r * 0.62, py + r * 0.62], fill=col)
        d.ellipse([cx - r * 0.42, cy - r * 0.42, cx + r * 0.42, cy + r * 0.42], fill=(255, 250, 235, 255))
    return _done(im, w, h)


def crown(w: int) -> Image.Image:
    """王冠。"""
    h = round(w * 0.56)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.polygon([(W * 0.06, H * 0.92), (W * 0.06, H * 0.30), (W * 0.28, H * 0.58), (W * 0.50, H * 0.12),
               (W * 0.72, H * 0.58), (W * 0.94, H * 0.30), (W * 0.94, H * 0.92)], fill=GOLD,
              outline=(226, 168, 50, 255), width=SS * 2)
    d.rectangle([W * 0.04, H * 0.78, W * 0.96, H * 0.98], fill=(255, 220, 120, 255),
                outline=(226, 168, 50, 255), width=SS * 2)
    for cx, col in ((0.28, DEEP_PINK), (0.50, (120, 196, 236, 255)), (0.72, DEEP_PINK)):
        d.ellipse([W * (cx - 0.05), H * 0.80, W * (cx + 0.05), H * 0.96], fill=col)
    return _done(im, w, h)


def party_hat(w: int) -> Image.Image:
    """とんがり帽子。"""
    h = round(w * 1.15)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.polygon([(W * 0.5, H * 0.06), (W * 0.94, H * 0.90), (W * 0.06, H * 0.90)], fill=(255, 168, 190, 255))
    for i in range(4):
        y = H * (0.30 + 0.16 * i)
        sp = (y - H * 0.06) / (H * 0.84) * 0.44
        d.line([(W * (0.5 - sp), y), (W * (0.5 + sp), y)], fill=(255, 244, 250, 255), width=SS * 4)
    d.ellipse([W * 0.38, -H * 0.04, W * 0.62, H * 0.16], fill=(255, 236, 150, 255))
    d.ellipse([W * 0.04, H * 0.84, W * 0.96, H * 0.98], fill=(255, 214, 228, 255))
    return _done(im, w, h)


def mushroom(w: int) -> Image.Image:
    """きのこ帽子。"""
    h = round(w * 0.66)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.rectangle([W * 0.40, H * 0.52, W * 0.60, H * 0.98], fill=(242, 232, 214, 255))
    d.pieslice([0, H * 0.06, W, H * 1.06], 180, 360, fill=(196, 96, 74, 255))
    for cx, cy, r in ((0.22, 0.42, 0.06), (0.44, 0.28, 0.08), (0.68, 0.38, 0.055), (0.82, 0.50, 0.04)):
        d.ellipse([W * (cx - r), H * (cy - r * 1.5), W * (cx + r), H * (cy + r * 1.5)],
                  fill=(250, 240, 226, 255))
    return _done(im, w, h)


def bao(w: int) -> Image.Image:
    """肉まんの皮っぽい被り物。"""
    h = round(w * 0.78)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.pieslice([0, H * 0.16, W, H * 1.34], 180, 360, fill=CREAM)
    for i in range(7):                                                      # ひだ
        a = math.pi * (0.08 + 0.84 * i / 6)
        x = W / 2 - W * 0.46 * math.cos(a)
        d.line([(W / 2, H * 0.30), (x, H * 0.80)], fill=(226, 202, 160, 255), width=SS * 3)
    d.ellipse([W * 0.40, H * 0.14, W * 0.60, H * 0.34], fill=(252, 238, 208, 255))
    return _done(im, w, h)


# ------------------------------------------------------------------ 顔まわり
def sunglasses(w: int) -> Image.Image:
    h = round(w * 0.34)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for x0 in (0.02, 0.54):
        d.rounded_rectangle([W * x0, H * 0.16, W * (x0 + 0.44), H * 0.90], radius=H * 0.24, fill=INK)
    d.line([(W * 0.44, H * 0.34), (W * 0.56, H * 0.34)], fill=INK, width=SS * 5)
    d.line([(W * 0.08, H * 0.30), (W * 0.20, H * 0.46)], fill=(255, 255, 255, 90), width=SS * 4)
    return _done(im, w, h)


def heart_glasses(w: int) -> Image.Image:
    h = round(w * 0.40)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.24, 0.76):
        s = W * 0.21
        top, bot = H * 0.10, H * 0.96
        d.ellipse([W * cx - s, top, W * cx, top + s * 1.15], fill=PINK)
        d.ellipse([W * cx, top, W * cx + s, top + s * 1.15], fill=PINK)
        d.polygon([(W * cx - s * 0.99, top + s * 0.52), (W * cx + s * 0.99, top + s * 0.52),
                   (W * cx, bot)], fill=PINK)
        d.ellipse([W * cx - s * 0.72, top + s * 0.18, W * cx - s * 0.24, top + s * 0.62],
                  fill=(255, 255, 255, 110))
    d.line([(W * 0.45, H * 0.34), (W * 0.55, H * 0.34)], fill=DEEP_PINK, width=SS * 5)
    return _done(im, w, h)


def round_glasses(w: int) -> Image.Image:
    h = round(w * 0.40)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.23, 0.77):
        d.ellipse([W * (cx - 0.21), H * 0.06, W * (cx + 0.21), H * 0.94], fill=(255, 255, 255, 40),
                  outline=INK, width=SS * 5)
    d.line([(W * 0.44, H * 0.44), (W * 0.56, H * 0.44)], fill=INK, width=SS * 5)
    return _done(im, w, h)


def whiskers(w: int) -> Image.Image:
    """ピンクの描きひげ。参考画像にもある定番の加工。"""
    h = round(w * 0.42)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for s, x0 in ((-1, 0.42), (1, 0.58)):
        for i, (dy0, dy1) in enumerate(((-0.14, -0.22), (0.02, 0.02), (0.18, 0.24))):
            d.line([(W * x0, H * (0.5 + dy0)), (W * (x0 + s * 0.40), H * (0.5 + dy1))],
                   fill=PINK, width=SS * 5)
    return _done(im, w, h)


def blush(w: int) -> Image.Image:
    h = round(w * 0.26)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.16, 0.84):
        d.ellipse([W * (cx - 0.15), H * 0.10, W * (cx + 0.15), H * 0.90], fill=(255, 150, 165, 120))
    return _done(im, w, h)


# ------------------------------------------------------------------ 首もと
def bow(w: int) -> Image.Image:
    h = round(w * 0.72)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.ellipse([0, H * 0.10, W * 0.46, H * 0.92], fill=PINK, outline=WHITE, width=SS * 2)
    d.ellipse([W * 0.54, H * 0.10, W, H * 0.92], fill=PINK, outline=WHITE, width=SS * 2)
    d.ellipse([W * 0.36, H * 0.32, W * 0.64, H * 0.72], fill=DEEP_PINK, outline=WHITE, width=SS * 2)
    return _done(im, w, h)


def ribbon_collar(w: int) -> Image.Image:
    h = round(w * 0.46)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    d.rounded_rectangle([0, H * 0.34, W, H * 0.66], radius=H * 0.16, fill=DEEP_PINK)
    b = bow(round(w * 0.46))
    im.alpha_composite(b.resize((b.width * SS, b.height * SS), Image.LANCZOS),
                       (round(W * 0.27), round(H * 0.16)))
    return _done(im, w, h)


# ------------------------------------------------------------------ 一覧
# name: (アンカー, 本体幅に対する横幅, 縦のズレ（本体高さ比・マイナスで上）)
ANCHOR = {
    # name: (置き場所, 頭幅に対する横幅, 縦のズレ, 横のズレ)
    "shark_hood":     ("head", 1.22, -0.30, 0.00),
    "strawberry_hat": ("head", 1.06, -0.34, 0.00),
    "bear_hood":      ("head", 1.18, -0.28, 0.00),
    "bunny_ears":     ("head", 0.94, -0.40, 0.00),
    "cat_ears":       ("head", 0.92, -0.30, 0.00),
    "flower_crown":   ("head", 0.98, -0.22, 0.00),
    "crown":          ("head", 0.72, -0.22, 0.00),
    "party_hat":      ("head", 0.62, -0.44, 0.10),
    "mushroom":       ("head", 0.92, -0.24, 0.00),
    "bao":            ("head", 1.14, -0.26, 0.00),
    "sunglasses":     ("face", 0.86, 0.00, 0.00),
    "heart_glasses":  ("face", 0.92, 0.00, 0.00),
    "round_glasses":  ("face", 0.86, 0.00, 0.00),
    "whiskers":       ("face", 1.30, 0.06, 0.00),
    "blush":          ("face", 0.94, 0.10, 0.00),
    "bow":            ("head", 0.36, -0.08, 0.22),
    "ribbon_collar":  ("neck", 0.86, 0.00, 0.00),
}

DRAW = {
    "shark_hood": shark_hood, "strawberry_hat": strawberry_hat, "bear_hood": bear_hood,
    "bunny_ears": bunny_ears, "cat_ears": cat_ears, "flower_crown": flower_crown,
    "crown": crown, "party_hat": party_hat, "mushroom": mushroom, "bao": bao,
    "sunglasses": sunglasses, "heart_glasses": heart_glasses, "round_glasses": round_glasses,
    "whiskers": whiskers, "blush": blush, "bow": bow, "ribbon_collar": ribbon_collar,
}


def render(name: str, width: int) -> Image.Image | None:
    fn = DRAW.get(name)
    return fn(max(8, width)) if fn else None
