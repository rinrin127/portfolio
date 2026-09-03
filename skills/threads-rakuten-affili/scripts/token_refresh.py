#!/usr/bin/env python3
"""Threads長期トークンのリフレッシュ（週次実行推奨）
60日有効の長期トークンを refresh_access_token で延命し .env を書き換える。

使い方: python token_refresh.py
"""
import json, re, sys, urllib.parse, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ENVFILE = BASE / "config" / ".env"


def main():
    if not ENVFILE.exists():
        sys.exit("[SETUP REQUIRED] config/.env がありません")
    text = ENVFILE.read_text()
    m = re.search(r"THREADS_ACCESS_TOKEN=(\S+)", text)
    if not m:
        sys.exit("[SETUP REQUIRED] THREADS_ACCESS_TOKEN が未設定です")
    token = m.group(1)

    url = "https://graph.threads.net/refresh_access_token?" + urllib.parse.urlencode({
        "grant_type": "th_refresh_token", "access_token": token})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        sys.exit(f"[NG] リフレッシュ失敗: {e}\n"
                 "→ トークンが失効している可能性。SKILL.md references節の手順で再取得してください")

    new_token = data.get("access_token")
    expires_days = data.get("expires_in", 0) // 86400
    if not new_token:
        sys.exit(f"[NG] 予期しない応答: {data}")

    ENVFILE.write_text(text.replace(token, new_token))
    print(f"[OK] トークン更新完了（残り約{expires_days}日）")
    if expires_days < 7:
        print("⚠️ 有効期限が7日未満です。承認キューに警告を表示してください")


if __name__ == "__main__":
    main()
