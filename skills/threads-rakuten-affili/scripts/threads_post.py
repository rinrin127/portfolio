#!/usr/bin/env python3
"""STEP F: Threads投稿（Meta公式 Threads API）
承認された投稿番号のみを投稿する。コンテナ作成→公開の2段階。

使い方:
  python threads_post.py --test                                  # 権限確認のみ
  python threads_post.py --publish work/posts_YYMMDD.json --approved 1,3,5
  python threads_post.py --publish work/posts_YYMMDD.json --approved 1 --now  # 即時投稿

安全設計:
- --approved で明示された番号以外は絶対に投稿しない
- compliance.ok=False の投稿は承認済みでもブロック（理由を表示して停止）
- 未記入プレースホルダ（【ここに体験】【要確認】）が残る投稿もブロック
- 投稿成功したものは posts_log.csv に追記（重複防止の照合元）

比較モード:
  posts JSON に "thread": [{text, product, affiliateUrl}, ...] があれば、
  親を投稿したあと reply_to_id で順にぶら下げる（Threadsのスレッド投稿）。
"""
import argparse, csv, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
API = "https://graph.threads.net/v1.0"


def load_env():
    env = {}
    envfile = BASE / "config" / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for k in ("THREADS_ACCESS_TOKEN", "THREADS_USER_ID"):
        env.setdefault(k, os.environ.get(k, ""))
    if not env.get("THREADS_ACCESS_TOKEN") or not env.get("THREADS_USER_ID"):
        sys.exit("[SETUP REQUIRED] config/.env に THREADS_ACCESS_TOKEN / THREADS_USER_ID を設定してください")
    return env


def api_post(path, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{path}", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def api_get(path, params):
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def publish_text(env, text, reply_to_id=None):
    """コンテナ作成→公開の2段階投稿。公開後のpost IDを返す。
    reply_to_id を渡すとその投稿へのぶら下げ（返信）になる。"""
    params = {
        "media_type": "TEXT", "text": text,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    }
    if reply_to_id:
        params["reply_to_id"] = reply_to_id
    c = api_post(f"{env['THREADS_USER_ID']}/threads", params)
    container_id = c["id"]
    time.sleep(5)  # コンテナ処理待ち（公式推奨）
    p = api_post(f"{env['THREADS_USER_ID']}/threads_publish", {
        "creation_id": container_id,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    return p["id"]


def publish_thread(env, post):
    """親を投稿→ぶら下げを順に投稿。(親ID, [ぶら下げID...]) を返す"""
    parent_id = publish_text(env, post["text"])
    reply_ids = []
    for i, t in enumerate(post.get("thread", []), 1):
        time.sleep(3)
        try:
            rid = publish_text(env, t["text"], reply_to_id=parent_id)
            reply_ids.append(rid)
            print(f"    └ ぶら下げ{i} 完了 (id={rid})")
        except Exception as e:
            # 親は既に公開済み。残りは手動で足せるよう明示して続行しない
            print(f"    └ ぶら下げ{i} 失敗: {e}")
            print(f"       親(id={parent_id})は公開済みです。"
                  f"残りのぶら下げは手動で追加するか、再実行せず追記してください")
            break
    return parent_id, reply_ids


def blocking_placeholders(post):
    """未記入の【ここに体験】【要確認】を1行の説明にして返す（無ければ空文字）"""
    ph = post.get("placeholders", {})
    if not ph.get("remaining"):
        return ""
    return (f"体験{len(ph.get('experience', []))}か所 / "
            f"要確認{len(ph.get('verify', []))}か所 が未記入")


def log_post(post, post_id):
    logf = BASE / "work" / "posts_log.csv"
    new = not logf.exists()
    with logf.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "post_id", "hook_type", "text_head", "product",
                        "affiliateUrl", "score", "views", "likes", "replies", "reposts"])
        hook = post.get("hook_type", "")
        if post.get("thread"):
            hook = f"{hook}(スレッド{len(post['thread']) + 1}本)"
        w.writerow([time.strftime("%Y-%m-%d %H:%M"), post_id, hook,
                    post.get("text", "")[:60].replace(",", "、").replace("\n", " "),
                    post.get("product", "")[:40].replace(",", "、"),
                    post.get("affiliateUrl", ""), post.get("score", ""), "", "", "", ""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--publish")
    ap.add_argument("--approved", default="")
    ap.add_argument("--now", action="store_true", help="予定時刻を待たず即時投稿")
    args = ap.parse_args()

    env = load_env()

    if args.test:
        try:
            me = api_get("me", {"fields": "id,username",
                                "access_token": env["THREADS_ACCESS_TOKEN"]})
            print(f"[OK] Threads API疎通確認: @{me.get('username')} (id={me.get('id')})")
        except Exception as e:
            sys.exit(f"[NG] Threads API疎通失敗: {e}")
        return

    if not args.publish or not args.approved:
        sys.exit("usage: threads_post.py --publish work/posts_YYMMDD.json --approved 1,3,5")

    data = json.loads(Path(args.publish).read_text(encoding="utf-8"))
    approved = {int(x) for x in args.approved.replace("、", ",").split(",") if x.strip().isdigit()}
    posts = {p["no"]: p for p in data.get("posts", [])}

    for no in sorted(approved):
        p = posts.get(no)
        if not p:
            print(f"[SKIP] 投稿{no}: 見つかりません")
            continue
        if not p.get("compliance", {}).get("ok", False):
            print(f"[BLOCK] 投稿{no}: コンプラ⚠️のため投稿しません。修正して再検査してください")
            continue
        ph = blocking_placeholders(p)
        if ph:
            print(f"[BLOCK] 投稿{no}: {ph}。"
                  f"【ここに体験】【要確認】を埋めてから compliance_check.py を再実行してください")
            continue
        if not args.now and p.get("post_time"):
            print(f"[INFO] 投稿{no}は {p['post_time']} 予定 → その時刻に再実行するか --now を付けてください")
            continue
        try:
            if p.get("thread"):
                pid, _ = publish_thread(env, p)
            else:
                pid = publish_text(env, p["text"])
            log_post(p, pid)
            print(f"[OK] 投稿{no} 完了 (id={pid})")
            time.sleep(3)
        except Exception as e:
            print(f"[NG] 投稿{no} 失敗: {e}")


if __name__ == "__main__":
    main()
