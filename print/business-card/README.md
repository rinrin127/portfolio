# 名刺データ（ピンク）

| ファイル | 用途 |
|---|---|
| `business-card-pink.pdf` | **印刷所に入稿するファイル。** 表・裏の2ページ。仕上がり 91×55mm に塗り足し3mmを足した 97×61mm で、フォントは埋め込み済み |
| `business-card-pink-front.png` / `-back.png` | 表と裏のプレビュー画像（350dpi）。SNSやCanvaで見せる用 |
| `business-card-pink.html` | 名刺のもと。ブラウザで開くと仕上がり線つきで確認できます |
| `qr-site.svg` | 表に載せているサイトのQRコード |

## 載っている内容

すべて `content/` の JSON から取っています。**このフォルダの中身を手で直さないでください**（次に作り直すと消えます）。

| 名刺の場所 | 元データ |
|---|---|
| ロゴ TONARIE／トナリエ | `site.json` の `nameEn` / `name` |
| ネットの向こうを、となりに。 | `site.json` の `tagline`（`taglineAccent` の部分だけ濃いピンク） |
| 名前・肩書き | `profile.json` の `name` / `role`（ローマ字は `nameEn`。無ければ Risa Nakajima） |
| メール・URL・所在地 | `site.json` の `contact.email` / `url` / `footer.location` |
| 裏の実績3行 | `site.json` の `achievements.items` |
| 裏の 01/02/03 | `services.json` の各柱の `title` |
| 裏の @risalink0127 | `accounts.json` で名前に「本アカウント」が入っているもの |

## 作り直す

```bash
npm run card
```

`content/` を直したあとにこれを実行すると、HTML・PDF・PNG がすべて作り直されます。

- PDF を作るには Google Chrome（または Chromium）が入っていれば十分です。見つからない場合は HTML だけ出るので、ブラウザで開いて「印刷 → PDFに保存」してください（用紙サイズは自動で 97×61mm になります）。
- PNG は Python の `pypdfium2` がある場合だけ作られます（`pip install pypdfium2`）。無くても PDF はできます。
- フォントは Google Fonts から読みます。ネットにつながらない環境で作るときは、`fonts/` に次の9ファイルを置くと同じ字形で出ます（このフォルダは Git に入りません）:
  `ZenOldMincho-500/600/700.ttf`、`ZenKakuGothicNew-400/500/700.ttf`、`CrimsonPro-400/500/600.ttf`

### QRコードを作り直す（サイトのURLを変えたとき）

```bash
pip install qrcode
python3 -c "
import qrcode, qrcode.image.svg, json
url = json.load(open('content/site.json'))['url']
img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=0)
img.save('print/business-card/qr-site.svg')
s = open('print/business-card/qr-site.svg').read().replace('<svg', f'<!-- QR: {url} -->\n<svg', 1)
open('print/business-card/qr-site.svg', 'w').write(s)
"
npm run card
```

`site.json` の `url` と QR の中身が違うと、`npm run card` のときに警告が出ます。

## 入稿するときのメモ

- サイズ: 仕上がり 91×55mm（日本の標準サイズ）、塗り足し 3mm、トンボなし
- 文字は仕上がり線から 4mm 以上内側に置いてあります
- 色は RGB です。印刷所側で CMYK に変換されるため、画面より少し落ち着いたピンクになります。気になる場合は「RGB入稿可」の印刷所（ラクスル・プリントパック等）を選んでください
- 表: 淡いピンク地＋左端に濃いピンクの帯（断裁後 約2.5mm）。裏: 濃いピンク地に白文字

## 色

| 役割 | 色 |
|---|---|
| 表の地色 | `#FCE9EF` |
| 濃いピンク（帯・裏の地色・強調） | `#C9466C` |
| 表の文字 | `#5A2A38` |
| 裏の文字 | `#FFF7F9` |

色を変えたいときは `scripts/business-card.mjs` の `:root` にある変数を直してください。
