#!/usr/bin/env python3
"""STEP H: 週次分析
posts_log.csv を集計し、フック型別ランキング表の骨組みmdを出力。
AIコメント（伸びた型2つ／捨てる型1つ、hooks_config.md反映差分）はモデルが追記する。

使い方:
  python weekly_review.py --out work/weekly_YYMMDD.md
  python weekly_review.py --clicks 420 --revenue 9800 --orders 14 --target 50000
      # 楽天管理画面の実測値を渡すと1クリック単価(EPC)と目標到達に必要なクリック数を算出

楽天は「クリック→24h以内にかご入れ→89日以内に購入完了」で成果になり、
かごに入った商品が紹介商品と別でも対象になり得る。よって単価ではなく
**1クリックあたりいくらになったか(EPC)** を主KPIにする。
"""
import argparse, csv, time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--clicks", type=int, default=None, help="楽天管理画面の週間クリック数")
    ap.add_argument("--revenue", type=int, default=None, help="週間の発生報酬(円)")
    ap.add_argument("--orders", type=int, default=None, help="週間の発生件数")
    ap.add_argument("--target", type=int, default=None, help="月間の目標報酬(円)")
    args = ap.parse_args()

    logf = BASE / "work" / "posts_log.csv"
    if not logf.exists():
        print("[INFO] posts_log.csv なし。投稿実績が貯まってから実行してください")
        return

    cutoff = datetime.now() - timedelta(days=args.days)
    by_hook = defaultdict(lambda: {"n": 0, "views": 0, "likes": 0, "replies": 0, "reposts": 0})
    total = {"n": 0, "views": 0, "likes": 0}

    for row in list(csv.reader(logf.open(encoding="utf-8")))[1:]:
        try:
            if datetime.strptime(row[0], "%Y-%m-%d %H:%M") < cutoff:
                continue
        except ValueError:
            continue
        hook = row[2] or "未分類"
        d = by_hook[hook]
        d["n"] += 1
        for i, k in ((7, "views"), (8, "likes"), (9, "replies"), (10, "reposts")):
            try:
                d[k] += int(row[i] or 0)
            except (ValueError, IndexError):
                pass
        total["n"] += 1
        total["views"] += d["views"] and int(row[7] or 0)
        total["likes"] += int(row[8] or 0) if len(row) > 8 and row[8] else 0

    date = time.strftime("%Y-%m-%d")
    lines = [f"# 週次分析 {date}（直近{args.days}日）", "",
             f"投稿数: {total['n']}本", "",
             "## フック型別パフォーマンス", "",
             "| フック型 | 本数 | 平均views | 平均likes | エンゲ率% |",
             "|---|---|---|---|---|"]
    ranked = sorted(by_hook.items(),
                    key=lambda kv: (kv[1]["views"] / kv[1]["n"]) if kv[1]["n"] else 0,
                    reverse=True)
    for hook, d in ranked:
        avg_v = d["views"] / d["n"] if d["n"] else 0
        avg_l = d["likes"] / d["n"] if d["n"] else 0
        eng = (d["likes"] + d["replies"] + d["reposts"]) / d["views"] * 100 if d["views"] else 0
        lines.append(f"| {hook} | {d['n']} | {avg_v:.0f} | {avg_l:.1f} | {eng:.2f} |")

    lines += ["", "## 楽天成果", ""]
    if args.clicks:
        epc = (args.revenue or 0) / args.clicks
        cvr = (args.orders or 0) / args.clicks * 100
        lines += [f"- クリック数: {args.clicks:,}回",
                  f"- 発生報酬: {(args.revenue or 0):,}円",
                  f"- 発生件数: {(args.orders or 0):,}件",
                  f"- **EPC（1クリック単価）: {epc:.1f}円**",
                  f"- 成約率: {cvr:.2f}%（クリック→発生）", ""]
        if args.target:
            need = args.target / epc if epc > 0 else 0
            per_post = need / (total["n"] * 4) if total["n"] else 0
            lines += [f"### 目標 {args.target:,}円/月 の逆算（EPC {epc:.1f}円で計算）", "",
                      f"- 必要クリック数: 約{need:,.0f}回/月",
                      f"- 今の投稿ペース（直近{args.days}日で{total['n']}本）なら"
                      f"1本あたり約{per_post:,.0f}クリック必要", "",
                      "> EPCは投稿本数より先に効く。1本あたりのクリックが足りないうちに",
                      "> 本数だけ増やしても目標には届かない（本数はEPCが安定してから伸ばす）", ""]
        kpi = BASE / "work" / "rakuten_kpi.csv"
        new_file = not kpi.exists()
        with kpi.open("a", encoding="utf-8") as f:
            if new_file:
                f.write("date,posts,clicks,revenue,orders,epc\n")
            f.write(f"{date},{total['n']},{args.clicks},{args.revenue or 0},"
                    f"{args.orders or 0},{epc:.2f}\n")
        lines.append(f"（推移は work/rakuten_kpi.csv に追記済み）")
    else:
        lines += ["- 発生件数: ___件", "- 発生報酬: ___円", "- クリック数: ___回", "",
                  "> 楽天アフィリエイト管理画面の週間数値を入れて再実行すると",
                  "> EPC（1クリック単価）と目標逆算まで自動で出ます:",
                  "> `python weekly_review.py --clicks 420 --revenue 9800 --orders 14 --target 50000`", ""]

    lines += ["", "## AI分析コメント（モデルが追記）", "",
              "- 強化する型（2つ）: ", "- 捨てる型（1つ）: ",
              "- hooks_config.md への反映差分: ",
              "- EPCを上げる打ち手 / クリック数を増やす打ち手のどちらを優先するか: "]

    out = Path(args.out) if args.out else BASE / "work" / f"weekly_{time.strftime('%y%m%d')}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 週次分析の骨組みを出力: {out}")
    print("→ AI分析コメントを追記し、Drive「Threads楽天アフィ/週次/」へ保存してください")


if __name__ == "__main__":
    main()
