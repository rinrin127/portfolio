#!/usr/bin/env python3
"""STEP A: 楽天商品リサーチ
楽天ウェブサービス(IchibaItem/Search)で候補商品を抽出し、
affiliateUrl付きでスコアリングしてJSON出力する。モデル非依存。

使い方:
  python rakuten_search.py --out work/products_YYMMDD.json
  python rakuten_search.py --test        # API疎通確認のみ
  python rakuten_search.py --keywords "洗濯洗剤,柔軟剤" --out work/compare_YYMMDD.json
                                         # 比較モード: 指定語ごとに候補を取る（商品は探させない）
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
API = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"


def load_env():
    env = {}
    envfile = BASE / "config" / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for k in ("RAKUTEN_APP_ID", "RAKUTEN_AFFILIATE_ID"):
        env.setdefault(k, os.environ.get(k, ""))
    return env


def load_genres():
    p = BASE / "config" / "genres.json"
    return json.loads(p.read_text(encoding="utf-8"))


def fetch(params):
    url = API + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def score_item(it, cfg):
    """レビュー件数×評価×価格帯適合の複合スコア(0-100)"""
    rc = it.get("reviewCount", 0)
    ra = it.get("reviewAverage", 0.0)
    price = it.get("itemPrice", 0)
    s = 0.0
    s += min(rc / cfg.get("review_count_cap", 2000), 1.0) * 45      # レビュー件数 45点
    s += max(0.0, (ra - 4.0) / 1.0) * 35                            # 評価4.0超過分 35点
    lo, hi = cfg.get("price_range", [1500, 6000])
    s += 20 if lo <= price <= hi else 8                             # 価格帯 20点
    return round(s, 1)


def search_genre(env, genre, cfg):
    params = {
        "applicationId": env["RAKUTEN_APP_ID"],
        "affiliateId": env["RAKUTEN_AFFILIATE_ID"],
        "genreId": genre["genreId"],
        "sort": "-reviewCount",
        "hits": 30,
        "formatVersion": 2,
        "minPrice": cfg.get("price_range", [1500, 6000])[0],
        "maxPrice": cfg.get("price_range", [1500, 6000])[1],
    }
    data = fetch(params)
    items = []
    for it in data.get("Items", []):
        if it.get("reviewCount", 0) < cfg.get("min_review_count", 100):
            continue
        if it.get("reviewAverage", 0) < cfg.get("min_review_average", 4.2):
            continue
        name = it.get("itemName", "")
        if any(ng in name for ng in cfg.get("exclude_keywords", [])):
            continue
        items.append({
            "genre": genre["label"],
            "itemName": name,
            "itemPrice": it.get("itemPrice"),
            "reviewCount": it.get("reviewCount"),
            "reviewAverage": it.get("reviewAverage"),
            "affiliateUrl": it.get("affiliateUrl") or it.get("itemUrl"),
            "itemCaption": (it.get("itemCaption") or "")[:800],
            "shopName": it.get("shopName"),
            "score": score_item(it, cfg),
        })
    return items


def search_keyword(env, keyword, cfg, hits=5):
    """比較モード用: my_products.md に書かれた商品名・カテゴリで候補を引く。
    ジャンル横断・価格帯フィルタなしで検索し、レビュー数順に返す。
    「人気商品を探す」のではなく「りんりんが挙げた商品の事実を取りに行く」用途。
    """
    params = {
        "applicationId": env["RAKUTEN_APP_ID"],
        "affiliateId": env["RAKUTEN_AFFILIATE_ID"],
        "keyword": keyword,
        "sort": "-reviewCount",
        "hits": hits,
        "formatVersion": 2,
    }
    items = []
    for it in fetch(params).get("Items", []):
        name = it.get("itemName", "")
        if any(ng in name for ng in cfg.get("exclude_keywords", [])):
            continue
        items.append({
            "keyword": keyword,
            "itemName": name,
            "itemPrice": it.get("itemPrice"),
            "reviewCount": it.get("reviewCount"),
            "reviewAverage": it.get("reviewAverage"),
            "affiliateUrl": it.get("affiliateUrl") or it.get("itemUrl"),
            "itemCaption": (it.get("itemCaption") or "")[:800],
            "shopName": it.get("shopName"),
            "score": score_item(it, cfg),
        })
    return items


def run_comparison(env, conf, keywords, out):
    """キーワードごとに候補を取り、比較モード用JSONを書き出す"""
    cfg = conf["filters"]
    cmp_cfg = conf.get("comparison_mode", {})
    per_kw = cmp_cfg.get("hits_per_keyword", 5)
    groups = []
    for kw in keywords:
        try:
            found = search_keyword(env, kw, cfg, hits=per_kw)
        except Exception as e:
            print(f"[WARN] keyword {kw}: {e}", file=sys.stderr)
            found = []
        groups.append({"keyword": kw, "candidates": found})
        print(f"  「{kw}」: {len(found)}件")
        for it in found:
            print(f"    - {it['itemName'][:36]}… ¥{it['itemPrice']} "
                  f"(★{it['reviewAverage']}/{it['reviewCount']}件)")
        time.sleep(1.1)  # レート制限(1req/sec)遵守

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"date": time.strftime("%Y-%m-%d"), "mode": "comparison",
                               "groups": groups}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"[OK] 比較モードの候補を出力: {out}")
    print("→ 価格・容量は【要確認】のまま扱うこと。ここの数値は取得時点のもの")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--keywords", default="",
                    help="比較モード: カンマ区切りの商品名/カテゴリ（my_products.md由来）")
    args = ap.parse_args()

    env = load_env()
    missing = [k for k in ("RAKUTEN_APP_ID", "RAKUTEN_AFFILIATE_ID") if not env.get(k)]
    if missing:
        sys.exit(f"[SETUP REQUIRED] config/.env に未設定: {', '.join(missing)}")

    conf = load_genres()
    cfg, genres = conf["filters"], conf["genres"]

    if args.test:
        try:
            fetch({"applicationId": env["RAKUTEN_APP_ID"], "keyword": "test", "hits": 1})
            print("[OK] 楽天API疎通確認に成功しました")
        except Exception as e:
            sys.exit(f"[NG] 楽天API疎通失敗: {e}")
        return

    if args.keywords:
        kws = [k.strip() for k in args.keywords.replace("、", ",").split(",") if k.strip()]
        out = Path(args.out) if args.out else BASE / "work" / f"compare_{time.strftime('%y%m%d')}.json"
        run_comparison(env, conf, kws, out)
        return

    all_items = []
    for g in genres:
        try:
            all_items += search_genre(env, g, cfg)
            time.sleep(1.1)  # レート制限(1req/sec)遵守
        except Exception as e:
            print(f"[WARN] genre {g['label']}: {e}", file=sys.stderr)

    all_items.sort(key=lambda x: x["score"], reverse=True)
    top = all_items[: args.top]

    out = Path(args.out) if args.out else BASE / "work" / "products_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"date": time.strftime("%Y-%m-%d"), "products": top},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(top)}商品を出力: {out}")
    for i, it in enumerate(top, 1):
        print(f"  {i}. [{it['score']}] {it['itemName'][:40]}… ¥{it['itemPrice']} "
              f"(★{it['reviewAverage']}/{it['reviewCount']}件)")


if __name__ == "__main__":
    main()
