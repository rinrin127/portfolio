#!/usr/bin/env python3
"""STEP G: インサイト収集
posts_log.csv の投稿についてThreads APIのインサイトを取得しCSVを更新。
24時間以上経過した投稿を対象に views/likes/replies/reposts を上書き更新する。

使い方: python fetch_insights.py
"""
import csv, json, sys, time, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
API = "https://graph.threads.net/v1.0"


def load_env():
    env = {}
    envfile = BASE / "config" / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    if not env.get("THREADS_ACCESS_TOKEN"):
        sys.exit("[SETUP REQUIRED] .env に THREADS_ACCESS_TOKEN がありません")
    return env


def get_insights(env, post_id):
    url = f"{API}/{post_id}/insights?" + urllib.parse.urlencode({
        "metric": "views,likes,replies,reposts",
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read().decode())
    out = {}
    for m in data.get("data", []):
        vals = m.get("values", [{}])
        out[m["name"]] = vals[0].get("value", 0) if vals else 0
    return out


def main():
    env = load_env()
    logf = BASE / "work" / "posts_log.csv"
    if not logf.exists():
        sys.exit("[INFO] posts_log.csv がまだありません（投稿実績なし）")

    rows = list(csv.reader(logf.open(encoding="utf-8")))
    header, body = rows[0], rows[1:]
    updated = 0
    for row in body:
        try:
            posted = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        age_h = (datetime.now() - posted).total_seconds() / 3600
        if age_h < 24:
            continue  # 24h未満はスキップ
        try:
            ins = get_insights(env, row[1])
            row[7] = str(ins.get("views", row[7]))
            row[8] = str(ins.get("likes", row[8]))
            row[9] = str(ins.get("replies", row[9]))
            row[10] = str(ins.get("reposts", row[10]))
            updated += 1
            time.sleep(1)
        except Exception as e:
            print(f"[WARN] {row[1]}: {e}", file=sys.stderr)

    with logf.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(body)
    print(f"[OK] {updated}件のインサイトを更新しました")


if __name__ == "__main__":
    main()
