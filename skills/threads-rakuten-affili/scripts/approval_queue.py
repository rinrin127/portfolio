#!/usr/bin/env python3
"""STEP E: 承認キュー生成
posts_YYMMDD.json から YYMMDD_承認キュー.md / YYMMDD_商品リサーチ.md を生成。

使い方:
  python approval_queue.py --build work/posts_YYMMDD.json
  python approval_queue.py --schema     # STEP B(AI生成)が従うJSONスキーマを表示
"""
import argparse, json, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

SCHEMA = {
    "date": "YYYY-MM-DD",
    "posts": [{
        "no": 1,
        "product": "商品名",
        "affiliateUrl": "https://hb.afl.rakuten.co.jp/...",
        "hook_type": "価格ショック|ビフォアフ示唆|社会的証明|時短・簡便|悩み言い当て|意外性",
        "text": "①フック\n②本文\n③CTA（#PRは検査で自動付与）",
        "score": 85,
        "score_detail": "5軸の内訳1行",
        "post_time": "07:30",
    }],
    "_comparison_mode_post": {
        "no": 1,
        "mode": "comparison",
        "hook_type": "比較・買い替え",
        "text": "親投稿（結論3行・リンクなし）",
        "thread": [
            {"product": "商品A", "affiliateUrl": "https://hb.afl.rakuten.co.jp/...",
             "text": "商品A：向いている人/向いていない人/【ここに体験：…】/リンク"},
            {"product": "商品B", "affiliateUrl": "...", "text": "…"},
            {"product": "商品C", "affiliateUrl": "...", "text": "…"},
        ],
        "score": 85,
        "score_detail": "5軸の内訳1行",
        "post_time": "20:30",
        "_note": "config/comparison_template.md 参照。体験と数値はプレースホルダのまま出す",
    },
}


def build(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    date = data.get("date", time.strftime("%Y-%m-%d"))
    ymd = date.replace("-", "")[2:]
    outdir = BASE / "work"
    outdir.mkdir(exist_ok=True)

    lines = [f"# {date} 承認キュー", "",
             "返信例：「1,3,5 OK」／「2は値段推しに直して」／「全部OK」／「今日はスキップ」", ""]
    for p in data.get("posts", []):
        c = p.get("compliance", {})
        mark = "✅" if c.get("ok") else "⚠️"
        issues = "".join(f"\n> ⚠️ {h['label']}:「{h['matched']}」" for h in c.get("issues", []))
        rec = "★推奨" if p.get("score", 0) >= 80 else ""
        thread = p.get("thread", [])
        title = p.get("product", "") or "／".join(t.get("product", "") for t in thread)
        head = f"## {p['no']}. {mark} [{p.get('score','-')}点]{rec} {p.get('hook_type','')} — {title[:40]}"
        if thread:
            head += f" ＜スレッド{len(thread) + 1}本＞"
        lines += [head, "```", p.get("text", ""), "```"]
        for i, t in enumerate(thread, 1):
            lines += [f"└ ぶら下げ{i}: {t.get('product','')[:30]}",
                      "```", t.get("text", ""), "```",
                      f"　リンク: {t.get('affiliateUrl','')[:60]}…"]
        ph = p.get("placeholders", {})
        if ph.get("remaining"):
            lines.append(f"> 📝 記入待ち: 体験{len(ph.get('experience', []))}か所 "
                         f"／ 要確認{len(ph.get('verify', []))}か所"
                         f"（埋めるまで投稿はブロックされます）")
        link = p.get("affiliateUrl", "")
        lines += [
            f"予定時刻: {p.get('post_time','未定')}"
            + (f" ／ リンク: {link[:60]}…" if link else "")
            + issues,
            "",
        ]
    q = outdir / f"{ymd}_承認キュー.md"
    q.write_text("\n".join(lines), encoding="utf-8")

    # 商品リサーチmd
    prod_path = outdir / f"products_{ymd}.json"
    if prod_path.exists():
        prods = json.loads(prod_path.read_text(encoding="utf-8"))
        rl = [f"# {date} 商品リサーチ（上位{len(prods.get('products', []))}件）", ""]
        for i, it in enumerate(prods.get("products", []), 1):
            rl.append(f"{i}. [{it['score']}] {it['itemName'][:50]} ¥{it['itemPrice']} "
                      f"★{it['reviewAverage']}({it['reviewCount']}件) {it['genre']}")
        (outdir / f"{ymd}_商品リサーチ.md").write_text("\n".join(rl), encoding="utf-8")

    print(f"[OK] 承認キュー生成: {q}")
    print("→ Driveの「Threads楽天アフィ/日次/」へ保存し、チャットで要約を提示してください")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build")
    ap.add_argument("--schema", action="store_true")
    args = ap.parse_args()
    if args.schema:
        print(json.dumps(SCHEMA, ensure_ascii=False, indent=2))
        return
    if args.build:
        build(Path(args.build))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
