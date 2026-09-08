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


# ================================================================== 感情エフェクト
# 写真が数枚しかなくても喜怒哀楽を出すための、マンガ的な記号。
def anger(w: int) -> Image.Image:
    """怒りマーク（いわゆる 💢）。ヘの字を4方向に並べる。"""
    h = w
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    col = (232, 70, 88, 255)
    t = round(W * 0.11)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        cx, cy = W / 2 + math.cos(a) * W * 0.24, H / 2 + math.sin(a) * H * 0.24
        ux, uy = math.cos(a), math.sin(a)          # 外向き
        px, py = -uy, ux                            # 直交
        L, D = W * 0.17, W * 0.13
        d.line([(cx + px * L - ux * D, cy + py * L - uy * D), (cx + ux * D, cy + uy * D),
                (cx - px * L - ux * D, cy - py * L - uy * D)], fill=col, width=t, joint="curve")
    return _done(im, w, h)


def sweat(w: int) -> Image.Image:
    """あせ（一粒）。"""
    h = round(w * 1.30)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    col = (120, 196, 240, 255)
    d.polygon([(W * 0.5, 0), (W * 0.94, H * 0.62), (W * 0.06, H * 0.62)], fill=col)
    d.ellipse([W * 0.04, H * 0.34, W * 0.96, H * 0.99], fill=col)
    d.ellipse([W * 0.24, H * 0.56, W * 0.44, H * 0.78], fill=(226, 246, 255, 220))
    return _done(im, w, h)


def tears(w: int) -> Image.Image:
    """なみだ（両目の下）。"""
    h = round(w * 0.60)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    col = (110, 190, 240, 235)
    for cx in (0.22, 0.78):
        d.polygon([(W * cx, H * 0.02), (W * (cx + 0.075), H * 0.52), (W * (cx - 0.075), H * 0.52)], fill=col)
        d.ellipse([W * (cx - 0.085), H * 0.34, W * (cx + 0.085), H * 0.98], fill=col)
        d.ellipse([W * (cx - 0.045), H * 0.56, W * (cx - 0.005), H * 0.74], fill=(235, 250, 255, 230))
    return _done(im, w, h)


def zzz(w: int) -> Image.Image:
    """すやすや。"""
    h = round(w * 0.92)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    col = (128, 158, 214, 255)
    for i, (cx, cy, s) in enumerate(((0.10, 0.62, 0.30), (0.40, 0.34, 0.38), (0.74, 0.04, 0.48))):
        x, y, k = W * cx, H * cy, W * s
        t = max(SS * 2, round(k * 0.16))
        d.line([(x, y), (x + k * 0.7, y)], fill=col, width=t)
        d.line([(x + k * 0.7, y), (x, y + k * 0.62)], fill=col, width=t)
        d.line([(x, y + k * 0.62), (x + k * 0.7, y + k * 0.62)], fill=col, width=t)
    return _done(im, w, h)


def note(w: int) -> Image.Image:
    """音符。"""
    h = round(w * 1.10)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    col = (255, 158, 100, 255)
    d.ellipse([0, H * 0.62, W * 0.52, H * 0.98], fill=col)
    d.rectangle([W * 0.44, H * 0.06, W * 0.56, H * 0.82], fill=col)
    d.polygon([(W * 0.56, H * 0.06), (W, H * 0.20), (W, H * 0.40), (W * 0.56, H * 0.26)], fill=col)
    return _done(im, w, h)


def question(w: int) -> Image.Image:
    return _mark(w, "?", (128, 158, 214, 255))


def exclaim(w: int) -> Image.Image:
    return _mark(w, "!", (255, 176, 70, 255))


def _mark(w: int, ch: str, col) -> Image.Image:
    """?! を曲線で描く（フォントに依存させない）。"""
    h = round(w * 1.50)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    t = round(W * 0.24)
    if ch == "?":
        cx, cy, r = W * 0.50, H * 0.28, W * 0.30
        pts = []
        for i in range(40):                       # 上のフックを描く
            a = math.radians(190 - 250 * i / 39)
            pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
        pts.append((cx, H * 0.66))
        d.line(pts, fill=col, width=t, joint="curve")
    else:
        d.line([(W * 0.50, H * 0.04), (W * 0.50, H * 0.64)], fill=col, width=t)
    d.ellipse([W * 0.50 - t * 0.60, H * 0.82, W * 0.50 + t * 0.60, H * 0.82 + t * 1.20], fill=col)
    return _done(im, w, h)


def shock(w: int) -> Image.Image:
    """ガーン（青い縦線）。"""
    h = round(w * 0.70)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for i in range(9):
        x = W * (0.04 + 0.92 * i / 8)
        a = 130 if i % 2 else 90
        d.line([(x, 0), (x, H * (0.55 + 0.35 * (i % 3) / 2))], fill=(120, 140, 200, a),
               width=round(W * 0.022))
    return _done(im, w, h)


def heart_eyes(w: int) -> Image.Image:
    """目がハート。"""
    h = round(w * 0.44)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.24, 0.76):
        s = W * 0.17
        top = H * 0.10
        d.ellipse([W * cx - s, top, W * cx, top + s * 1.15], fill=DEEP_PINK)
        d.ellipse([W * cx, top, W * cx + s, top + s * 1.15], fill=DEEP_PINK)
        d.polygon([(W * cx - s * 0.99, top + s * 0.52), (W * cx + s * 0.99, top + s * 0.52),
                   (W * cx, H * 0.96)], fill=DEEP_PINK)
        d.ellipse([W * cx - s * 0.66, top + s * 0.16, W * cx - s * 0.22, top + s * 0.58],
                  fill=(255, 255, 255, 150))
    return _done(im, w, h)


def spiral_eyes(w: int) -> Image.Image:
    """ぐるぐる目（こまった・混乱）。"""
    h = round(w * 0.42)
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for cx in (0.24, 0.76):
        cx_, cy_ = W * cx, H * 0.50
        pts = []
        for i in range(64):
            t = i / 63
            r = W * 0.16 * t
            a = t * math.pi * 4
            pts.append((cx_ + r * math.cos(a), cy_ + r * math.sin(a)))
        d.line(pts, fill=INK, width=round(W * 0.038), joint="curve")
    return _done(im, w, h)


def sparkle_burst(w: int) -> Image.Image:
    """キラッ（ひらめき・喜び）。"""
    h = w
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    for i in range(8):
        a = i * math.pi / 4
        r0, r1 = W * 0.18, W * (0.46 if i % 2 == 0 else 0.34)
        d.line([(W / 2 + r0 * math.cos(a), H / 2 + r0 * math.sin(a)),
                (W / 2 + r1 * math.cos(a), H / 2 + r1 * math.sin(a))],
               fill=(255, 214, 90, 255), width=round(W * 0.055))
    d.ellipse([W * 0.34, H * 0.34, W * 0.66, H * 0.66], fill=(255, 244, 190, 255))
    return _done(im, w, h)


EMOTION_ANCHOR = {
    "anger":         ("head", 0.34, -0.06, 0.34),
    "sweat":         ("head", 0.20, 0.02, 0.36),
    "tears":         ("face", 0.80, 0.16, 0.00),
    "zzz":           ("head", 0.52, -0.34, 0.34),
    "note":          ("head", 0.24, -0.14, -0.34),
    "question":      ("head", 0.28, -0.32, 0.26),
    "exclaim":       ("head", 0.24, -0.34, 0.24),
    "shock":         ("head", 0.90, -0.10, 0.00),
    "heart_eyes":    ("face", 0.88, 0.00, 0.00),
    "spiral_eyes":   ("face", 0.86, 0.00, 0.00),
    "sparkle_burst": ("head", 0.40, -0.26, -0.32),
}

ANCHOR.update(EMOTION_ANCHOR)
DRAW.update({"anger": anger, "sweat": sweat, "tears": tears, "zzz": zzz, "note": note,
             "question": question, "exclaim": exclaim, "shock": shock,
             "heart_eyes": heart_eyes, "spiral_eyes": spiral_eyes, "sparkle_burst": sparkle_burst})
