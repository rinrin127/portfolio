#!/usr/bin/env python3
"""写真が用意できるまでの動作確認用に、ダミーの猫の切り抜き画像を作る。"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "input"
FUR = [(226, 200, 170, 255), (200, 205, 210, 255), (240, 225, 205, 255)]


def cat(i: int) -> Image.Image:
    im = Image.new("RGBA", (600, 640), (0, 0, 0, 0))
    d, fur = ImageDraw.Draw(im), FUR[i % len(FUR)]
    d.ellipse([150, 300, 450, 620], fill=fur)                       # からだ
    d.polygon([(190, 210), (250, 90), (300, 210)], fill=fur)        # みみ
    d.polygon([(300, 210), (350, 90), (410, 210)], fill=fur)
    d.ellipse([140, 120, 460, 420], fill=fur)                       # あたま
    for x in (232, 368):                                            # め
        d.ellipse([x - 34, 216, x + 34, 292], fill=(40, 35, 40, 255))
        d.ellipse([x - 12, 232, x + 6, 254], fill=(255, 255, 255, 255))
    d.polygon([(288, 306), (312, 306), (300, 322)], fill=(240, 150, 165, 255))
    d.arc([264, 318, 300, 348], 0, 180, fill=(70, 60, 60, 255), width=5)
    d.arc([300, 318, 336, 348], 0, 180, fill=(70, 60, 60, 255), width=5)
    for s in (-1, 1):                                               # ほっぺ
        d.ellipse([300 + s * 150 - 34, 300, 300 + s * 150 + 34, 340], fill=(255, 180, 190, 110))
    return im


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for i in range(1, 25):
        cat(i).save(OUT / f"{i:02d}.png")
    print(f"ダミー画像24枚を {OUT} に作成")
