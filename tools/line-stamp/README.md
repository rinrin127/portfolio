# うちの猫スタンプ ビルダー

飼ってた猫ちゃんの写真から、**動くLINEスタンプ（APNG）一式＋申請用ZIP**を作るツール。
LINEの規格チェックまで自動でやるので、リジェクトで往復するのを防げる。

## 使い方

### 1. 写真を切り抜く（ここだけ手作業、いちばん品質に効く）

`input/01.png` 〜 `24.png` として、**背景を透過したPNG**を置く。

- **iPhone**：写真の猫を長押し → 「コピー」→ メモ等に貼って書き出し。これが一番きれいで速い
- Mac：プレビュー.app の「インスタントアルファ」
- PC/自動化：`pip install rembg` → `rembg i in.jpg out.png`

毛のフチが荒いとそのままスタンプの粗さになるので、ここだけは丁寧に。

### 2. セリフとモーションを決める

`config.json` を編集する。

```json
{ "src": "input/01.png", "text": "おはよ", "motion": "bounce", "deco": ["sparkle"] }
```

| 項目 | 指定できる値 |
|---|---|
| `motion` | `bounce` `jump` `shake` `pop` `breathe` `tilt` `wiggle` `none` |
| `deco` | `bow`（リボン）`heart` `sparkle` `star` `flower` |
| `text_pos` | `bottom` / `top` |

個数は **8・16・24個** のいずれか（動くスタンプの場合）。

### 3. ビルドする

```bash
pip install pillow
python3 make_stamps.py --config config.json --out build
```

`build/` に出るもの：

- `01.png`〜`24.png` … APNGスタンプ本体
- `main.png`（240×240）`tab.png`（96×74）
- `うちの猫スタンプ.zip` … **これをそのままLINEに申請できる**
- `_preview.jpg` … 一覧プレビュー
- `_motion.gif` … 動きが分かるGIF（Discord承認用）

### 4. LINEに申請する

LINE Creators Market のマイページ → 新規登録 → ZIPをアップロード → 申請。
（申請だけは公開APIが無いので手作業。1セット1分）

## 自動でやっていること

- 透明な余白の自動トリム／シールっぽい白フチ付け
- リボン・ハート・キラキラ等のデコ合成（キラキラは瞬く）
- 白フチ付きのセリフ描画（日本語フォントを自動検出）
- ぷるぷる・ジャンプ等のモーション生成 → APNG化
- **300KBに収まるまで「フレーム数 → 減色 → 縮小」の順に自動調整**
- 規格バリデータ：サイズ／偶数ピクセル／長辺270px以上／フレーム数5〜20／
  1ループ1〜4秒／総再生4秒以内／ループ回数1〜4／容量300KB

## 権利について

- **自分で撮った自分の猫の写真** ＝ 権利は自分にあるのでOK
- 他人が作ったスタンプのデザインや、拾い画は使わない
- 人物が写り込んでいる写真は本人の同意が必要（猫だけなら問題なし）

## フォント

日本語フォントを自動で探す（ヒラギノ丸ゴ → ヒラギノ → メイリオ → 游ゴシック → Noto）。
好きなフォントを使いたいときは `--font /path/to/font.ttf`。
丸ゴシック系だと一気にスタンプっぽくなる。

## 動作確認

写真がまだ無いときは、ダミーの猫画像で一通り動かせる。

```bash
python3 make_demo_input.py     # input/ にダミー24枚
python3 make_stamps.py --config config.json --out build
```
