#!/usr/bin/env python3
"""
make_stamps.py — 切り抜き済みの写真から LINE スタンプ一式を組み立てる

  python3 make_stamps.py --config config.json --out build

やること:
  1. 透過PNG（iPhoneの長押し切り抜き等）を読み込み、余白を自動トリム
  2. ステッカー風の白フチ・リボン・キラキラ・ほっぺ等のデコを合成
  3. セリフを白フチ文字で載せる
  4. ぷるぷる／ジャンプ等のモーションを付けて APNG 化
  5. LINE の規格（サイズ・フレーム数・再生時間・300KB）を満たすまで自動で圧縮
  6. main.png / tab.png を作って ZIP にまとめる
  7. 最後に規格バリデータを通して結果を表で表示

入力画像は「背景が透過済みのPNG」を想定。
（iPhone: 写真の被写体を長押し → コピー、が一番きれいで速い）
"""
from __future__ import annotations

import argparse, json, math, struct, sys, zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageSequence

import accessories as ACC

# ---------------------------------------------------------------- LINE 規格
SPEC = {
    "animation": dict(canvas=(320, 270), min_long_side=270, max_bytes=300_000,
                      min_frames=5, max_frames=20, min_sec=1.0, max_sec=4.0,
                      counts=(8, 16, 24)),
    "static":    dict(canvas=(370, 320), min_long_side=0, max_bytes=1_000_000,
                      counts=(8, 16, 24, 32, 40)),
}
MAIN_SIZE, TAB_SIZE = (240, 240), (96, 74)

# 日本語フォント候補（上から順に探す。Mac / Windows / Linux）
FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
    "/System/Library/Fonts/Hiragino Sans W6.ttc",
    "/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]

PINK, DEEP_PINK, WHITE = (255, 150, 180, 255), (240, 90, 140, 255), (255, 255, 255, 255)


def find_font(explicit: str | None) -> str | None:
    if explicit and explicit != "auto" and Path(explicit).exists():
        return explicit
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


# ---------------------------------------------------------------- 画像の下ごしらえ
def load_cutout(path: Path) -> Image.Image:
    """透過PNGを読み込んで、透明な余白を切り落とす。"""
    img = Image.open(path).convert("RGBA")
    bbox = img.split()[3].getbbox()
    if bbox is None:
        raise SystemExit(f"✗ {path} は中身が全部透明。背景透過に失敗してるかも")
    if img.split()[3].getextrema()[0] == 255:
        print(f"  ! {path.name}: 透過されてない（背景が残ってる）可能性あり")
    return img.crop(bbox)


def sticker_outline(img: Image.Image, width: int = 11, color=WHITE) -> Image.Image:
    """シールらしい白フチを付ける。

    参考画像のフチは、ヒゲのような細い部分を無視して、丸くなめらかに回り込んでいる。
    そこで一度アルファをぼかして角を落とし（＝細い線を輪郭から外し）、それから太らせる。
    ヒゲ自体は写真として上に残るので、フチからはみ出して見える。
    """
    if width <= 0:
        return img
    pad = width + 4
    base = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    base.paste(img, (pad, pad))
    alpha = base.split()[3]
    round_r = max(2.0, width * 0.75)
    shape = alpha.filter(ImageFilter.GaussianBlur(round_r)).point(lambda v: 255 if v > 132 else 0)
    grown = shape.filter(ImageFilter.MaxFilter(width * 2 + 1))
    grown = grown.filter(ImageFilter.GaussianBlur(width * 0.30)).point(lambda v: 255 if v > 96 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(0.8))
    edge = Image.new("RGBA", base.size, color)
    edge.putalpha(ImageChops.lighter(grown, alpha))
    return Image.alpha_composite(edge, base)


def fit_into(img: Image.Image, box: tuple[int, int]) -> Image.Image:
    """縦横比を保ったまま box に収める。"""
    scale = min(box[0] / img.width, box[1] / img.height)
    return img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)


# ---------------------------------------------------------------- デコレーション
def _bow(size: int, color=PINK) -> Image.Image:
    w = h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, h * 0.15, w * 0.46, h * 0.85], fill=color, outline=WHITE, width=max(1, size // 22))
    d.ellipse([w * 0.54, h * 0.15, w, h * 0.85], fill=color, outline=WHITE, width=max(1, size // 22))
    d.ellipse([w * 0.38, h * 0.34, w * 0.62, h * 0.66], fill=DEEP_PINK, outline=WHITE, width=max(1, size // 24))
    return im


def _sparkle(size: int, color=WHITE) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r, t = size / 2, size / 2, size * 0.16
    d.polygon([(c, 0), (c + t, c - t), (size, c), (c + t, c + t),
               (c, size), (c - t, c + t), (0, c), (c - t, c - t)], fill=color)
    return im


def _heart(size: int, color=PINK) -> Image.Image:
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size * 2
    d.ellipse([s * 0.04, s * 0.10, s * 0.54, s * 0.60], fill=color)
    d.ellipse([s * 0.46, s * 0.10, s * 0.96, s * 0.60], fill=color)
    d.polygon([(s * 0.06, s * 0.42), (s * 0.94, s * 0.42), (s * 0.5, s * 0.96)], fill=color)
    return im.resize((size, size), Image.LANCZOS)


def _star(size: int, color=(255, 214, 90, 255)) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts, c = [], size / 2
    for i in range(10):
        r = c if i % 2 == 0 else c * 0.44
        a = math.pi / 2 + i * math.pi / 5
        pts.append((c + r * math.cos(a), c - r * math.sin(a)))
    d.polygon(pts, fill=color, outline=WHITE)
    return im


def _flower(size: int, color=(255, 205, 100, 255)) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, pr = size / 2, size * 0.22
    for i in range(6):
        a = i * math.pi / 3
        px, py = c + math.cos(a) * size * 0.26, c + math.sin(a) * size * 0.26
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=color, outline=WHITE)
    d.ellipse([c - pr * 0.7, c - pr * 0.7, c + pr * 0.7, c + pr * 0.7], fill=(255, 245, 220, 255))
    return im


DECO_SHAPES = {"bow": _bow, "sparkle": _sparkle, "heart": _heart, "star": _star, "flower": _flower}

# 各デコの既定の置き場所（コンテンツ矩形に対する相対座標 0〜1）と大きさ
DECO_LAYOUT = {
    "bow":     [(0.72, -0.04, 0.30)],
    "flower":  [(0.02, -0.06, 0.28), (0.70, -0.06, 0.24)],
    "sparkle": [(-0.08, 0.10, 0.20), (0.92, 0.28, 0.16), (0.02, 0.76, 0.14)],
    "heart":   [(0.88, 0.58, 0.22), (-0.06, 0.30, 0.16)],
    "star":    [(-0.06, 0.02, 0.22), (0.90, 0.10, 0.16)],
}


def paste_deco(canvas: Image.Image, rect: tuple[int, int, int, int], decos: list[str], phase: float) -> None:
    """rect=(x,y,w,h) の周りにデコを置く。phase(0〜1)でキラキラが瞬く。"""
    x, y, w, h = rect
    base = max(w, h)
    for i, name in enumerate(decos):
        shape = DECO_SHAPES.get(name)
        if not shape:
            continue
        for j, (rx, ry, rs) in enumerate(DECO_LAYOUT.get(name, [(0.8, 0.0, 0.25)])):
            size = max(8, round(base * rs))
            img = shape(size)
            if name in ("sparkle", "star", "heart"):     # 瞬き
                tw = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(2 * math.pi * (phase + 0.27 * (i + j))))
                img.putalpha(img.split()[3].point(lambda v: int(v * tw)))
            dx = max(0, min(round(x + rx * w), canvas.width - size))
            dy = max(0, min(round(y + ry * h), canvas.height - size))
            canvas.alpha_composite(img, (dx, dy))


def split_lines(text: str, limit: int = 6) -> list[str]:
    """長いセリフは2行に折る。敬語だと字数が増えるので効いてくる。

    config で "よろしく\\nお願いします" と改行を書けばそこで折る。
    書かなければ、真ん中あたりで切れ目のよさそうな位置を探す。
    """
    if "\n" in text:
        return [ln for ln in text.split("\n") if ln][:2]
    if len(text) <= limit:
        return [text]
    mid = len(text) // 2
    best, best_score = mid, -99
    for i in range(max(1, mid - 3), min(len(text), mid + 4)):
        ch, prev = text[i], text[i - 1]
        score = -abs(i - mid)
        if ch in SMALL_KANA:
            score -= 10                                   # 小さい字の前では切らない
        if ch in "おご":
            score += 4                                    # ご丁寧な接頭辞の前で切る
        if ord(ch) > 0x4E00 and not (0x4E00 <= ord(prev) <= 0x9FFF):
            score += 3                                    # ひらがな→漢字の変わり目
        if score > best_score:
            best, best_score = i, score
    return [text[:best], text[best:]]


def draw_text(canvas: Image.Image, text: str, font_path: str | None, pos: str, margin: int) -> None:
    """白フチ付きのセリフ。フォントが無ければ黙って飛ばす。"""
    if not text or not font_path:
        return
    d = ImageDraw.Draw(canvas)
    lines = split_lines(text)
    maxw = canvas.width - margin * 2
    maxh = canvas.height * (0.34 if len(lines) > 1 else 0.20)
    size = round(canvas.height * 0.18)
    while size > 10:
        font = ImageFont.truetype(font_path, size)
        wide = max(d.textlength(ln, font=font) for ln in lines)
        if wide <= maxw and size * 1.18 * len(lines) <= maxh:
            break
        size -= 2
    font = ImageFont.truetype(font_path, size)
    lh = size * 1.16
    block = lh * len(lines)
    y0 = margin if pos == "top" else canvas.height - margin - block
    for i, ln in enumerate(lines):
        x = (canvas.width - d.textlength(ln, font=font)) / 2
        d.text((x, y0 + i * lh), ln, font=font, fill=(60, 45, 50, 255),
               stroke_width=max(3, size // 8), stroke_fill=WHITE)


# ---------------------------------------------------------------- 写真そのものの加工
SMALL_KANA = set("ぁぃぅぇぉっゃゅょャュョッァィゥェォーん、。！？")


PHOTO_ANCHORS: dict = {}


def load_photo_anchors(root: Path) -> None:
    """photos.json に書いた実測値を読み込む。無ければ自動推定にまかせる。"""
    f = root / "photos.json"
    if f.exists():
        PHOTO_ANCHORS.update({k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items()
                              if not k.startswith("_")})
        print(f"顔の位置: photos.json から {len(PHOTO_ANCHORS)}枚ぶん読み込み")


def find_anchors(img: Image.Image, name: str = "") -> dict:
    """透過の形から、頭のてっぺん・頭の幅・顔の中心・首もとを推定する。"""
    if name in PHOTO_ANCHORS:                    # 実測値があればそれを使う
        m = PHOTO_ANCHORS[name]
        return dict(head_x=m["head_x"], head_y=m["head_top"], head_w=m["head_w"],
                    face_y=m["eye_y"], neck_y=m.get("neck_y", 1.05))
    alpha = img.split()[3]
    sw = 64
    small = alpha.resize((sw, max(2, round(img.height * sw / img.width))), Image.BILINEAR)
    px, sh = small.load(), small.height
    rows = []
    for y in range(sh):
        xs = [x for x in range(sw) if px[x, y] > 60]
        rows.append((min(xs), max(xs)) if xs else None)
    ys = [y for y, r in enumerate(rows) if r]
    if not ys:
        return dict(head_x=0.5, head_y=0.0, head_w=0.6, face_y=0.3, neck_y=0.5)
    top, bottom = ys[0], ys[-1]
    span = bottom - top + 1
    band = [r for r in rows[top:top + max(1, round(span * 0.30))] if r]
    head_x = sum((l + r) / 2 for l, r in band) / len(band) / sw
    head_w = max(r - l + 1 for l, r in band) / sw
    body_w = max(r[1] - r[0] + 1 for r in rows if r) / sw
    head_only = head_w / body_w > 0.85          # 顔アップの切り抜きか、座り姿か
    fy, ny = (0.42, 0.92) if head_only else (0.20, 0.42)
    return dict(head_x=head_x, head_y=top / sh, head_w=head_w,
                face_y=(top + span * fy) / sh, neck_y=(top + span * ny) / sh)


def tidy_alpha(img: Image.Image, feather: float = 0.08) -> Image.Image:
    """切り抜きのギザギザをならし、写真を切った直線的な下端をぼかす。

    白フチを付けるとアラが目立つので、その前に軽く整える。
    ヒゲは細いので消さない程度のぼかしにとどめる。
    """
    a = img.split()[3]
    a = a.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 0 if v < 110 else min(255, round(v * 1.25)))
    a = a.filter(ImageFilter.MinFilter(3))       # 切り抜きに残った白フチを1pxぶん削る
    if feather > 0:                              # 下端が画像の縁で切れていたらぼかす
        w, h = a.size
        band = max(2, round(h * feather))
        row = a.crop((0, h - 2, w, h - 1)).getextrema()
        if row[1] > 40:
            grad = Image.linear_gradient("L").resize((w, band))   # 上が黒→下が白
            grad = grad.point(lambda v: 255 - v)                  # 上が白→下が黒
            region = a.crop((0, h - band, w, h))
            a.paste(ImageChops.multiply(region, grad), (0, h - band))
    out = img.copy()
    out.putalpha(a)
    return out


def zoom_face(img: Image.Image) -> Image.Image:
    """全身の切り抜きから顔まわりだけを切り出す。写真が少なくても絵面を変えられる。"""
    a = find_anchors(img)
    w, h = img.size
    hw = max(a["head_w"] * w, w * 0.35)
    cx, top = a["head_x"] * w, a["head_y"] * h
    box = (max(0, round(cx - hw * 0.78)), max(0, round(top - hw * 0.14)),
           min(w, round(cx + hw * 0.78)), min(h, round(top + hw * 1.30)))
    if box[2] - box[0] < 20 or box[3] - box[1] < 20:
        return img
    return img.crop(box)


def apply_tint(img: Image.Image, kind: str) -> Image.Image:
    """怒り＝あたたかく、哀しみ＝つめたく。写真の印象をほんの少しだけ寄せる。"""
    table = {"warm": ((255, 196, 180), 0.22), "cool": ((186, 206, 255), 0.22),
             "pale": ((255, 255, 255), 0.20)}
    if kind not in table:
        return img
    color, amount = table[kind]
    rgb = Image.merge("RGB", img.split()[:3])
    out = Image.blend(rgb, ImageChops.multiply(rgb, Image.new("RGB", img.size, color)), amount)
    out.putalpha(img.split()[3])
    return out


# ---------------------------------------------------------------- 被り物を着せる
def wear_items(body: Image.Image, wear: list, name: str = "") -> tuple[Image.Image, dict]:
    """猫の切り抜きに被り物・小物・感情エフェクトを合成して1枚にまとめる。

    位置と大きさはすべて「頭の大きさ」を基準にする。顔だけ切り抜いた写真でも
    全身の写真でも、同じ設定で同じ見え方になる。
    """
    a = find_anchors(body, name)
    if not wear:
        return body, dict(head_cx=a["head_x"] * body.width, head_w=a["head_w"] * body.width,
                          head_cy=a["head_y"] * body.height + a["head_w"] * body.width * 0.525)
    padx, padt, padb = round(body.width * 0.40), round(body.height * 0.60), round(body.height * 0.12)
    canvas = Image.new("RGBA", (body.width + padx * 2, body.height + padt + padb), (0, 0, 0, 0))
    canvas.alpha_composite(body, (padx, padt))
    bw, bh = body.width, body.height
    hx = padx + a["head_x"] * bw
    head_w = a["head_w"] * bw                    # 頭の幅（px）
    head_h = head_w * 1.05                       # 頭の高さはだいたい幅と同じ
    head_top = padt + a["head_y"] * bh
    eye_y = padt + a["face_y"] * bh

    for w in wear:
        spec = {"name": w} if isinstance(w, str) else dict(w)
        name = spec.get("name", "")
        meta = ACC.ANCHOR.get(name)
        if not meta:
            print(f"  ! 知らない被り物: {name}")
            continue
        where, rel_w, rel_y, rel_x = meta
        width = max(10, round(head_w * rel_w * float(spec.get("scale", 1.0))))
        img = ACC.render(name, width)
        if img is None:
            continue
        rot = float(spec.get("rot", 0))
        if rot:
            img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
        x = hx - img.width / 2 + (rel_x + float(spec.get("dx", 0))) * head_w
        if where == "hood":                       # 顔の穴が顔に重なるように置く
            y = eye_y - img.height * ACC.HOLE_CY + rel_y * head_h
        elif where == "head":
            y = head_top + rel_y * head_h
        elif where == "face":
            y = eye_y - img.height / 2 + rel_y * head_h
        else:
            y = padt + a["neck_y"] * bh - img.height / 2 + rel_y * head_h
        y += float(spec.get("dy", 0)) * head_h
        canvas.alpha_composite(img, (round(x), round(y)))

    box = canvas.split()[3].getbbox()
    return canvas.crop(box), dict(head_cx=hx - box[0], head_w=head_w,
                                  head_cy=head_top + head_h * 0.5 - box[1])


# ---------------------------------------------------------------- モーション
def motion_at(motion: str, t: float) -> tuple[float, float, float, float]:
    """t(0〜1)における (dx, dy, 拡大率, 回転角)。"""
    two = 2 * math.pi
    return {
        "bounce":  (0.0, -0.10 * abs(math.sin(math.pi * t * 2)), 1.0, 0.0),
        "jump":    (0.0, -0.16 * max(0.0, math.sin(math.pi * t * 2)), 1.0, 0.0),
        "shake":   (0.03 * math.sin(two * t * 2), 0.0, 1.0, 4.0 * math.sin(two * t * 2)),
        "pop":     (0.0, 0.0, 1.0 + 0.09 * math.sin(two * t), 0.0),
        "breathe": (0.0, 0.0, 1.0 + 0.04 * math.sin(two * t), 0.0),
        "tilt":    (0.0, 0.0, 1.0, 9.0 * math.sin(two * t)),
        "wiggle":  (0.02 * math.sin(two * t * 2), -0.03 * abs(math.sin(math.pi * t * 2)), 1.0,
                    6.0 * math.sin(two * t * 2)),
        "none":    (0.0, 0.0, 1.0, 0.0),
    }.get(motion, (0.0, -0.10 * abs(math.sin(math.pi * t * 2)), 1.0, 0.0))


# ---------------------------------------------------------------- 1スタンプの組み立て
@dataclass
class Item:
    src: Path
    text: str = ""
    motion: str = "bounce"
    deco: tuple[str, ...] = ()
    text_pos: str = "bottom"
    wear: tuple = ()
    emo: tuple = ()
    flip: bool = False
    zoom: str = ""
    tint: str = ""


_BODY_CACHE: dict = {}


def prepare_body(item: Item, cfg: dict) -> tuple[Image.Image, dict]:
    """写真を読んで加工し、被り物を着せて白フチを付けるまで。

    容量調整でフレーム数を変えながら何度も呼ばれるので、結果を覚えておく
    （この工程がいちばん重い）。
    """
    key = (str(item.src), item.flip, item.zoom, item.tint, cfg.get("outline_ratio", 0.030),
           repr(item.wear), repr(item.emo))
    if key in _BODY_CACHE:
        return _BODY_CACHE[key]
    body = load_cutout(item.src)
    body = tidy_alpha(body, cfg.get("feather", 0.08))
    if item.flip:
        body = ImageOps.mirror(body)
    if item.zoom == "face":
        body = zoom_face(body)
    if item.tint:
        body = apply_tint(body, item.tint)
    body, meta = wear_items(body, list(item.wear) + list(item.emo), item.src.name)
    # フチの太さは写真の大きさに比例させる。固定pxだと縮小後に細く見えてしまう
    ow = max(5, round(body.width * cfg.get("outline_ratio", 0.030)))
    pad = ow + 4
    body = sticker_outline(body, ow)
    meta = dict(meta, head_cx=meta["head_cx"] + pad, head_cy=meta["head_cy"] + pad)
    _BODY_CACHE[key] = (body, meta)
    return _BODY_CACHE[key]


def render_frames(item: Item, cfg: dict, font_path: str | None, n_frames: int, scale: float = 1.0):
    canvas_w, canvas_h = cfg["canvas"]
    margin = cfg["margin"]
    head = 0.08                                  # 動きぶんに残す余白
    body, meta = prepare_body(item, cfg)

    # どの写真でも顔が同じくらいの大きさに見えるよう、頭の幅を基準に倍率を決める。
    # 被り物が大きいときは、はみ出さないほうを優先する。
    boxw = (canvas_w - margin * 2) * (1 - head) * scale
    boxh = (canvas_h - margin * 2) * (1 - head) * scale
    by_head = canvas_w * cfg.get("head_ratio", 0.56) / max(1.0, meta["head_w"])
    by_fit = min(boxw / body.width, boxh / body.height)
    k = min(by_head, by_fit)
    body = body.resize((max(1, round(body.width * k)), max(1, round(body.height * k))), Image.LANCZOS)
    head_cx, head_cy = meta["head_cx"] * k, meta["head_cy"] * k

    frames = []
    for i in range(n_frames):
        t = i / n_frames
        dx, dy, sc, ang = motion_at(item.motion, t)
        layer = body
        if abs(sc - 1.0) > 1e-3:
            layer = layer.resize((max(1, round(layer.width * sc)), max(1, round(layer.height * sc))), Image.LANCZOS)
        if abs(ang) > 1e-3:
            layer = layer.rotate(ang, resample=Image.BICUBIC, expand=True)

        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        gx, gy = (layer.width - body.width) / 2, (layer.height - body.height) / 2
        px = round(canvas_w * 0.50 - (head_cx + gx) * sc + dx * canvas_w)
        py = round(canvas_h * 0.44 - (head_cy + gy) * sc + dy * canvas_h)
        px = max(min(px, margin), min(0, canvas_w - margin - layer.width)) if layer.width > canvas_w - margin * 2 \
            else max(margin, min(px, canvas_w - margin - layer.width))
        py = max(min(py, margin), min(0, canvas_h - margin - layer.height)) if layer.height > canvas_h - margin * 2 \
            else max(margin, min(py, canvas_h - margin - layer.height))
        canvas.alpha_composite(layer, (px, py))
        paste_deco(canvas, (px, py, layer.width, layer.height), list(item.deco), t)
        draw_text(canvas, item.text, font_path, item.text_pos, margin)
        frames.append(canvas)
    return frames


def frame_durations(total_ms: int, n: int) -> list[int]:
    """1ループがきっかり total_ms になるよう、各フレームの表示時間を整数で配る。

    単純に割ると端数で4秒をわずかに超え、LINEの規格に引っかかる。
    """
    base, rem = divmod(total_ms, n)
    return [base + (1 if i < rem else 0) for i in range(n)]


def encode(frames, duration_ms, loop: int, colors: int = 0) -> bytes:
    """colors>0 なら減色してから書き出す（アルファは8bitのまま保つ）。"""
    if colors:
        out = []
        for f in frames:
            r, g, b, a = f.split()
            q = Image.merge("RGB", (r, g, b)).quantize(colors=colors, method=Image.FASTOCTREE).convert("RGB")
            q.putalpha(a)
            out.append(q)
        frames = out
    buf = BytesIO()
    kw = dict(format="PNG", optimize=True)
    if len(frames) > 1:
        kw.update(save_all=True, append_images=frames[1:], duration=duration_ms,
                  loop=loop, disposal=1, blend=0)
    frames[0].save(buf, **kw)
    return buf.getvalue()


def build_one(item: Item, cfg: dict, font_path: str | None) -> bytes:
    """300KB に収まるまで、フレーム数→減色→縮小 の順で自動的に落とす。"""
    animated = cfg["type"] == "animation"
    budget = cfg["max_bytes"]
    if not animated:
        for colors in (0, 256, 128):
            data = encode(render_frames(item, cfg, font_path, 1), 0, 1, colors)
            if len(data) <= budget:
                return data
        return data
    f0 = cfg["frames"]
    plan = [(f0, 0, 1.0), (f0, 256, 1.0), (f0, 128, 1.0), (8, 128, 1.0),
            (8, 96, 1.0), (6, 96, 1.0), (6, 64, 0.95), (5, 64, 0.92), (5, 32, 0.85)]
    last = b""
    for n, colors, scale in plan:
        if n < SPEC["animation"]["min_frames"]:
            break
        frames = render_frames(item, cfg, font_path, n, scale)
        last = encode(frames, frame_durations(cfg["loop_ms"], n), cfg["loop"], colors)
        if len(last) <= budget:
            return last
    print(f"  ! {item.src.name}: 300KBに収まらなかった（{len(last)//1024}KB）。写真をもっとシンプルに")
    return last


# ---------------------------------------------------------------- バリデータ
def read_png_info(data: bytes) -> dict:
    """PNG/APNGのチャンクを読んで、フレーム数・再生時間・ループ回数を取り出す。"""
    info = dict(width=0, height=0, frames=1, plays=None, seconds=0.0, apng=False)
    pos, n = 8, len(data)
    while pos + 8 <= n:
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            info["width"], info["height"] = struct.unpack(">II", body[:8])
        elif typ == b"acTL":
            info["apng"] = True
            frames, plays = struct.unpack(">II", body[:8])
            info["frames"], info["plays"] = frames, plays
        elif typ == b"fcTL":
            num, den = struct.unpack(">HH", body[20:24])
            info["seconds"] += num / (den or 100)
        pos += 12 + ln
    return info


def validate(data: bytes, cfg: dict, label: str) -> list[str]:
    s, errs = SPEC[cfg["type"]], []
    i = read_png_info(data)
    cw, ch = s["canvas"]
    if i["width"] > cw or i["height"] > ch:
        errs.append(f"サイズ超過 {i['width']}x{i['height']} > {cw}x{ch}")
    if i["width"] % 2 or i["height"] % 2:
        errs.append("縦横は偶数にする必要あり")
    if max(i["width"], i["height"]) < s["min_long_side"]:
        errs.append(f"長辺が{s['min_long_side']}px未満")
    if len(data) > s["max_bytes"]:
        errs.append(f"容量超過 {len(data)//1024}KB > {s['max_bytes']//1024}KB")
    if cfg["type"] == "animation":
        if not i["apng"]:
            errs.append("APNGになっていない")
        if not (s["min_frames"] <= i["frames"] <= s["max_frames"]):
            errs.append(f"フレーム数 {i['frames']} が5〜20の外")
        if not (s["min_sec"] - 1e-3 <= i["seconds"] <= s["max_sec"] + 1e-3):
            errs.append(f"1ループ {i['seconds']:.1f}秒 が1〜4秒の外")
        if i["plays"] is not None and not (1 <= i["plays"] <= 4):
            errs.append(f"ループ回数 {i['plays']} が1〜4の外")
        if i["plays"] and i["seconds"] * i["plays"] > 4.001:
            errs.append(f"総再生 {i['seconds']*i['plays']:.1f}秒 > 4秒")
    return errs


# ---------------------------------------------------------------- 出力まとめ
def contact_sheet(images: list[Image.Image], cols: int = 6) -> Image.Image:
    tw, th = images[0].size
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGBA", (cols * tw, rows * th), (235, 235, 238, 255))
    for i, im in enumerate(images):
        sheet.alpha_composite(im, ((i % cols) * tw, (i // cols) * th))
    return sheet


def motion_preview(paths: list[Path], out: Path, cols: int = 4, limit: int = 8) -> None:
    """Discord承認用に、動きが分かるGIFを1枚作る（明るい背景に合成）。"""
    seqs = []
    for p in paths[:limit]:
        im = Image.open(p)
        seqs.append([f.convert("RGBA") for f in ImageSequence.Iterator(im)])
    if not seqs:
        return
    tw, th = seqs[0][0].size
    rows = math.ceil(len(seqs) / cols)
    n = max(len(s) for s in seqs)
    frames = []
    for k in range(n):
        sheet = Image.new("RGBA", (cols * tw, rows * th), (245, 245, 247, 255))
        for i, seq in enumerate(seqs):
            sheet.alpha_composite(seq[k % len(seq)], ((i % cols) * tw, (i // cols) * th))
        frames.append(sheet.convert("P", palette=Image.ADAPTIVE, colors=128))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--out", default="build")
    ap.add_argument("--font", default=None)
    args = ap.parse_args()

    root = Path(args.config).resolve().parent
    raw = json.loads(Path(args.config).read_text(encoding="utf-8"))
    stype = raw.get("type", "animation")
    spec = SPEC[stype]
    cfg = dict(type=stype, canvas=tuple(raw.get("canvas", spec["canvas"])),
               margin=raw.get("margin", 10), outline_ratio=raw.get("outline_ratio", 0.030),
               frames=raw.get("frames", 10), loop_ms=raw.get("loop_ms", 1000),
               loop=raw.get("loop", 4), max_bytes=raw.get("max_bytes", spec["max_bytes"]),
               feather=raw.get("feather", 0.08))

    load_photo_anchors(root)
    font_path = find_font(args.font or raw.get("font"))
    print(f"フォント: {font_path or '見つからず（セリフはスキップ）'}")

    items = [Item(src=root / it["src"], text=it.get("text", ""), motion=it.get("motion", "bounce"),
                  deco=tuple(it.get("deco", [])), text_pos=it.get("text_pos", "bottom"),
                  wear=tuple(it.get("wear", [])), emo=tuple(it.get("emo", [])),
                  flip=bool(it.get("flip", False)), zoom=it.get("zoom", ""),
                  tint=it.get("tint", ""))
             for it in raw["items"]]
    if len(items) not in spec["counts"]:
        print(f"! 個数 {len(items)} は販売できない数。{spec['counts']} のいずれかにする")

    out = (root / args.out)
    out.mkdir(parents=True, exist_ok=True)
    results, previews = [], []

    for idx, item in enumerate(items, 1):
        data = build_one(item, cfg, font_path)
        name = f"{idx:02d}.png"
        (out / name).write_bytes(data)
        errs = validate(data, cfg, name)
        info = read_png_info(data)
        results.append((name, len(data), info, errs))
        previews.append(Image.open(BytesIO(data)).convert("RGBA"))
        print(f"  {name}  {len(data)//1024:>3}KB  {info['frames']}f  "
              f"{'OK' if not errs else '／'.join(errs)}")

    # メイン画像・タブ画像
    main_src = raw.get("main", raw["items"][0])
    m_item = Item(src=root / main_src["src"], text=main_src.get("text", ""),
                  motion=main_src.get("motion", "pop"), deco=tuple(main_src.get("deco", [])),
                  wear=tuple(main_src.get("wear", [])))
    m_cfg = dict(cfg, canvas=MAIN_SIZE)
    (out / "main.png").write_bytes(build_one(m_item, m_cfg, font_path))
    t_cfg = dict(cfg, canvas=TAB_SIZE, type="static", outline_ratio=0.022, max_bytes=1_000_000)
    (out / "tab.png").write_bytes(build_one(Item(src=m_item.src, motion="none", wear=m_item.wear),
                                            t_cfg, font_path))

    # プレビュー & ZIP
    contact_sheet(previews).convert("RGB").save(out / "_preview.jpg", quality=88)
    motion_preview(sorted(out.glob("[0-9][0-9].png")), out / "_motion.gif")
    zpath = out / f"{raw.get('title','stamps')}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.glob("[0-9][0-9].png")) + [out / "main.png", out / "tab.png"]:
            z.write(p, p.name)

    ng = [r for r in results if r[3]]
    total = zpath.stat().st_size
    print(f"\nZIP: {zpath}  {total/1024/1024:.2f}MB（上限60MB）")
    print(f"プレビュー: {out/'_preview.jpg'} / {out/'_motion.gif'}")
    print("判定: " + ("全部OK。このZIPをそのままLINEに申請できる"
                      if not ng else f"{len(ng)}件が規格NG。上のログを見て直す"))
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
