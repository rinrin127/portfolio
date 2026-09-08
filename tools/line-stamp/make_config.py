#!/usr/bin/env python3
"""
make_config.py — セリフ一式（タメ口版／敬語版）の config を作る

  python3 make_config.py --set casual --photos 4
  python3 make_config.py --set keigo  --photos 4

写真が数枚しかなくても絵面が単調にならないよう、
1枚の写真を「顔アップ」「全身」「左右反転」で回して使い分ける。
喜怒哀楽は 感情エフェクト＋被り物＋動き＋色味 の4点セットで出す。
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

# (セリフ, 動き, 感情エフェクト, 被り物, 色味, 顔アップ)
CASUAL = [
    ("おはよ",        "bounce",  [],                ["bunny_ears"],      "",     ""),
    ("おやすみ",      "breathe", ["zzz"],           ["bao"],             "cool", ""),
    ("おつかれ",      "breathe", ["sweat"],         [],                  "",     ""),
    ("ありがとう",    "bounce",  ["sparkle_burst"], ["bow"],             "",     ""),
    ("うれしい",      "jump",    ["note"],          ["flower_crown"],    "",     ""),
    ("やったー",      "jump",    ["sparkle_burst"], ["crown"],           "",     ""),
    ("すき",          "pop",     ["heart_eyes"],    [],                  "",     ""),
    ("おめでとう",    "jump",    ["note"],          ["party_hat"],       "",     ""),
    ("むり",          "shake",   ["shock"],         [],                  "cool", ""),
    ("なんでよ",      "shake",   ["anger"],         [],                  "warm", ""),
    ("おこ",          "shake",   ["anger"],         ["bow"],             "warm", ""),
    ("ちょっと！",    "shake",   ["exclaim"],       [],                  "warm", ""),
    ("ごめん",        "tilt",    ["sweat"],         [],                  "",     ""),
    ("かなしい",      "tilt",    ["tears"],         [],                  "cool", ""),
    ("さみしい",      "breathe", ["tears"],         [],                  "cool", ""),
    ("つらい",        "tilt",    ["shock"],         [],                  "cool", ""),
    ("いってきます",  "jump",    [],                ["shark_hood"],      "",     ""),
    ("おかえり",      "bounce",  ["note"],          ["bear_hood"],       "",     ""),
    ("りょ",          "shake",   [],                ["sunglasses"],      "",     ""),
    ("おっけー",      "pop",     ["sparkle_burst"], ["heart_glasses"],   "",     ""),
    ("ねむい",        "breathe", ["zzz"],           [],                  "",     ""),
    ("おなかすいた",  "wiggle",  ["sweat"],         ["mushroom"],        "",     ""),
    ("まってる",      "breathe", ["question"],      ["bow"],   "",     ""),
    ("がんばれ",      "jump",    ["exclaim"],       ["strawberry_hat"],  "",     ""),
]

KEIGO = [
    ("おはよう\nございます", "bounce",  [],                ["bow"],            "",     ""),
    ("おつかれ\nさまです",   "breathe", ["sweat"],         [],                 "",     ""),
    ("ありがとう\nございます", "bounce", ["sparkle_burst"], ["flower_crown"],  "",     ""),
    ("よろしく\nお願いします", "bounce", [],               ["bow"],            "",     ""),
    ("承知しました",        "pop",     [],                ["round_glasses"],  "",     ""),
    ("了解です",            "pop",     [],                ["sunglasses"],     "",     ""),
    ("かしこまり\nました",   "bounce",  [],                ["bow"],            "",     ""),
    ("申し訳\nありません",   "tilt",    ["sweat"],         [],                 "cool", ""),
    ("すみません",          "tilt",    ["sweat"],         [],                 "",     ""),
    ("恐れ入ります",        "tilt",    [],                ["blush"],          "",     ""),
    ("助かりました",        "jump",    ["sparkle_burst"], [],                 "",     ""),
    ("お世話に\nなります",   "bounce",  [],                ["bow"],            "",     ""),
    ("確認します",          "pop",     ["exclaim"],       ["round_glasses"],  "",     ""),
    ("対応します",          "jump",    ["exclaim"],       [],                 "",     ""),
    ("少々\nお待ちください", "breathe", ["question"],      [],                 "",     ""),
    ("お待ち\nしております", "breathe", ["note"],          ["bow"],            "",     ""),
    ("お先に\n失礼します",   "bounce",  [],                ["bunny_ears"],     "",     ""),
    ("行って\nまいります",   "jump",    [],                ["shark_hood"],     "",     ""),
    ("ただいま\n戻りました", "bounce",  ["note"],          ["bear_hood"],      "",     ""),
    ("大丈夫です",          "pop",     ["sparkle_burst"], [],                 "",     ""),
    ("検討します",          "tilt",    ["question"],      ["round_glasses"],  "",     ""),
    ("がんばります",        "jump",    ["exclaim"],       ["crown"],          "",     ""),
    ("楽しみに\nしています", "jump",    ["heart_eyes"],    ["strawberry_hat"], "",     ""),
    ("おやすみ\nなさい",     "breathe", ["zzz"],           ["bao"],            "cool", ""),
]

SETS = {"casual": ("うちの猫スタンプ", CASUAL), "keigo": ("うちの猫スタンプ 敬語", KEIGO)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=SETS, default="casual")
    ap.add_argument("--photos", type=int, default=4, help="input/ にある写真の枚数")
    ap.add_argument("--count", type=int, default=24, choices=(8, 16, 24))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    title, table = SETS[args.set]
    rows = table[:args.count]
    items, used = [], {}
    for i, (text, motion, emo, wear, tint, zoom) in enumerate(rows):
        pid = i % args.photos + 1
        used[pid] = used.get(pid, 0) + 1
        items.append({
            "src": f"input/{pid:02d}.png", "text": text, "motion": motion,
            "wear": wear, "emo": emo, "deco": [], "tint": tint, "zoom": zoom,
            "flip": used[pid] % 3 == 0,          # 同じ写真の3回目は左右反転して変化をつける
            "text_pos": "bottom",
        })

    cfg = {"title": title, "type": "animation", "canvas": [320, 270], "margin": 10,
           "outline": 8, "frames": 10, "loop_ms": 1000, "loop": 4,
           "max_bytes": 300000, "font": "auto",
           "main": {"src": "input/01.png", "text": "", "motion": "pop",
                    "wear": ["bow"], "emo": ["sparkle_burst"], "deco": []},
           "items": items}

    out = Path(args.out or f"config.{args.set}.json")
    out.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{out} を作成（{len(items)}個 / 写真{args.photos}枚を使い回し）")


if __name__ == "__main__":
    main()
