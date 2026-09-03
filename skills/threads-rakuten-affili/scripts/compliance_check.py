#!/usr/bin/env python3
"""STEP D: コンプラ検査（薬機法・景表法・ステマ規制）
posts_YYMMDD.json の全投稿を機械検査し、結果をJSONに書き戻す。
v4パイプラインの「顔ガード全数検査」と同じ思想＝人間の目より先に機械で全数ブロック。
比較モード（親＋ぶら下げのスレッド投稿）と、未記入プレースホルダの検出にも対応。

使い方: python compliance_check.py work/posts_YYMMDD.json
"""
import json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# 断定的効果効能・医薬品的表現（正規表現）
NG_PATTERNS = [
    (r"(治る|治療|完治|治す)", "医薬品的表現"),
    (r"(痩せる|やせる|脂肪が(落ち|燃え))", "断定的効果(ダイエット)"),
    (r"(シミ|シワ|ほうれい線)が(消え|なくな|薄くな)", "断定的効果(美容)"),
    (r"(効く|効果(あり|抜群|絶大)|即効)", "効能断定"),
    (r"(アンチエイジング|若返(り|る))", "医薬品的表現(老化)"),
    (r"(絶対|必ず|100%|確実に)", "保証表現"),
    (r"(No\.?1|ナンバーワン|日本一)(?!.*(調べ|調査|出典))", "最上級表現(出典なし)"),
    (r"(飲むだけで|塗るだけで|貼るだけで).{0,10}(変わ|改善|解消)", "簡便断定"),
    (r"(便秘|アトピー|ニキビ|花粉症|不眠)(が|を)(治|改善|解消)", "症状改善断定"),
]


def load_extra_ng():
    p = BASE / "config" / "ng_words.txt"
    if not p.exists():
        return []
    pats = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            pats.append((re.escape(line), "追加NGワード"))
    return pats


# 未記入プレースホルダ（比較モード / comparison_template.md の安全装置）
PLACEHOLDER_PATTERNS = {
    "experience": r"【ここに体験[：:][^】]*】",
    "verify": r"【要確認[：:]?[^】]*】",
}


def post_texts(post):
    """親投稿＋ぶら下げの全テキストを (種別, index, text) で返す"""
    out = [("parent", 0, post.get("text", ""))]
    for i, t in enumerate(post.get("thread", []), 1):
        out.append(("thread", i, t.get("text", "")))
    return out


def find_placeholders(post):
    """埋め忘れを種別ごとに列挙する。ここに残っている＝りんりんの記入待ち"""
    found = {k: [] for k in PLACEHOLDER_PATTERNS}
    for kind, idx, text in post_texts(post):
        for key, pat in PLACEHOLDER_PATTERNS.items():
            for m in re.finditer(pat, text):
                found[key].append({"where": f"{kind}{idx}" if kind == "thread" else "親",
                                   "matched": m.group(0)})
    return found


def check_text(text, patterns):
    hits = []
    for pat, label in patterns:
        m = re.search(pat, text)
        if m:
            hits.append({"label": label, "matched": m.group(0)})
    return hits


def load_posted_texts():
    """過去投稿との重複ブロック用"""
    p = BASE / "work" / "posts_log.csv"
    if not p.exists():
        return set()
    texts = set()
    for line in p.read_text(encoding="utf-8").splitlines()[1:]:
        cols = line.split(",")
        if len(cols) > 3:
            texts.add(cols[3][:60])
    return texts


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: compliance_check.py work/posts_YYMMDD.json")
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    patterns = NG_PATTERNS + load_extra_ng()
    posted = load_posted_texts()

    for post in data.get("posts", []):
        hits = []
        # 親＋ぶら下げを全数検査（比較モードはぶら下げ側に本文の大半が乗る）
        for kind, idx, text in post_texts(post):
            where = f"ぶら下げ{idx}" if kind == "thread" else "親"
            for h in check_text(text, patterns):
                h["matched"] = f"[{where}] {h['matched']}"
                hits.append(h)

        # ステマ規制: #PR 必須。スレッドの場合は親と最終ぶら下げの両方に付ける
        text = post.get("text", "")
        if "#PR" not in text and "#アフィリエイト" not in text:
            post["text"] = text.rstrip() + "\n#PR"
            post.setdefault("auto_fixed", []).append("#PR自動付与(親)")
            text = post["text"]
        thread = post.get("thread", [])
        if thread:
            last = thread[-1]
            lt = last.get("text", "")
            if "#PR" not in lt and "#アフィリエイト" not in lt:
                last["text"] = lt.rstrip() + "\n#PR"
                post.setdefault("auto_fixed", []).append(f"#PR自動付与(ぶら下げ{len(thread)})")

        # 重複検査（親の冒頭で判定）
        if text[:60] in posted:
            hits.append({"label": "重複投稿", "matched": "過去投稿と冒頭60字一致"})

        post["compliance"] = {"ok": len(hits) == 0, "issues": hits}
        # 未記入プレースホルダはコンプラ違反とは別枠で記録（投稿時に threads_post.py がブロック）
        ph = find_placeholders(post)
        post["placeholders"] = {
            "experience": ph["experience"],
            "verify": ph["verify"],
            "remaining": len(ph["experience"]) + len(ph["verify"]),
        }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for p in data["posts"] if p["compliance"]["ok"])
    print(f"[OK] 検査完了: ✅{ok}件 / ⚠️{len(data['posts']) - ok}件")
    for i, p in enumerate(data["posts"], 1):
        if not p["compliance"]["ok"]:
            for h in p["compliance"]["issues"]:
                print(f"  投稿{i} ⚠️ {h['label']}: 「{h['matched']}」")
        ph = p.get("placeholders", {})
        if ph.get("remaining"):
            print(f"  投稿{i} 📝 記入待ち: 体験{len(ph['experience'])}か所 / "
                  f"要確認{len(ph['verify'])}か所 → 埋めるまで投稿はブロックされます")


if __name__ == "__main__":
    main()
