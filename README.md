# Risa Link. 公式サイト

公開URL: https://rinrin127.github.io/portfolio/

参考にした構成：https://www.yuitakayama.co.jp （結高山）

---

## いちばん大事なこと

**`index.html` などのHTMLは編集しないでください。** 自動生成されるので、直しても消えます。
編集するのは **`content/` の中** です。

```
content/
  site.json          サイト名・ファーストビュー画像・キャッチコピー・数字・連絡先
  services.json      事業内容（3つの柱）
  works.json         制作実績（Figma連携で自動更新されます）
  business.json      いま取り組んでいる自分の事業
  accounts.json      運用中のSNSアカウント
  profile.json       プロフィール文・スキル・経歴
  testimonials.json  お客様の声
  posts/             お知らせ・ブログの記事（.md を置くだけ）
```

直したら、これを実行するとサイト全体が作り直されます。

```bash
npm run build
```

Claude Code を使っているなら、**「HPのサービスに◯◯を追加して」と言うだけでOK**です。

---

## ページ構成（全7ページ＋記事）

| URL | ページ | 中身 | 編集ファイル |
|---|---|---|---|
| `/` | トップ | ファーストビュー＋各ページの抜粋 | `site.json` ほか全部 |
| `/service/` | 事業内容 | 01/02/03 の3つの柱と内訳 | `services.json` |
| `/works/` | 制作実績 | 作ったものの一覧 | `works.json` |
| `/business/` | 事業・発信 | 自分の事業＋運用アカウント | `business.json` / `accounts.json` |
| `/profile/` | プロフィール | 文章・スキル・経歴・お客様の声 | `profile.json` / `testimonials.json` |
| `/news/` | お知らせ | 記事の一覧 | `content/posts/` |
| `/news/記事名/` | 記事ページ | 記事の本文 | `content/posts/*.md` |
| `/contact/` | お問い合わせ | ココナラ・LINEへの導線 | `site.json` の `contact` |

トップページは「上から下まで読めば全体が分かる」形にしてあり、各セクションから
「詳しく見る →」で個別ページへ送っています。

`sitemap.xml` と `robots.txt` も自動で作られます（Googleに拾ってもらうため）。

---

## 記事（お知らせ・ブログ）を書く

`content/posts/` に `.md` ファイルを置くだけです。**ファイル名がそのままURL**になります。

```
content/posts/2026-09-01-ai-lp-seisaku.md
  → https://rinrin127.github.io/portfolio/news/2026-09-01-ai-lp-seisaku/
```

ファイルの中身はこの形です。

```markdown
---
title: 記事のタイトル
date: 2026-09-01
category: 制作の裏側
excerpt: 一覧に出る2〜3行の要約。省略すると本文の冒頭が使われます。
image: assets/posts/写真.jpg
---

ここから本文。

## 見出し

段落を書きます。**太字**、[リンク](https://example.com)、`コード` が使えます。

- 箇条書き
- 番号つきリスト
- 引用（> ではじめる）
- 表（| で区切る）

も使えます。
```

`image` は空でもかまいません。写真は `assets/posts/` に置いてください。
書いたら `npm run build` で一覧・記事ページ・sitemap が全部作り直されます。

**`script-to-blog` スキルで作った記事は、先頭に上の `---` を足せばそのまま使えます。**
`content/posts/README.md` は記事として扱われません（説明用のファイルです）。

---

## ファーストビューの写真

いまは **仮の画像**（色のグラデーション）が入っています。
写真を3枚用意して `assets/fv/` に置き、`content/site.json` の `hero.slides` を書き換えてください。

```json
"slides": [
  { "image": "assets/fv/fv-1.jpg", "alt": "立山連峰の朝" },
  { "image": "assets/fv/fv-2.jpg", "alt": "仕事の手元" },
  { "image": "assets/fv/fv-3.jpg", "alt": "内川の夕方" }
]
```

### 何を撮るか（3枚）

| | 内容 | 撮り方 |
|---|---|---|
| 1枚目 | **風景（引き）** 立山連峰・内川の朝 | 横位置。空を広めに入れる。晴れた日の午前中 |
| 2枚目 | **手元（寄り）** 窓辺の机、MacBook＋ノート＋コーヒー | 手だけ入れる（顔は入れない）。横から自然光。斜め45度から |
| 3枚目 | **風景（生活感）** 内川の水辺・町並み | 夕方のオレンジの光。人が写るなら小さく・後ろ姿で |

### 撮影のルール

- **横位置**で撮る。幅1920px以上（スマホならそのままでOK）
- **画面の中央は"静かな面"にする** — 中央にサイト名の文字が乗るので、空・水面・壁など模様の少ないものを中央に
- **明るめ・彩度は控えめ** に。明朝の上品さと合います
- **顔は入れない**
- **3枚のトーンを揃える** — 全部朝、または全部夕方。バラバラだと切り替わったときにチカチカします

2枚目の写真は、下層ページ（事業内容・制作実績など）の見出し帯の背景にも使われます。

色味の調整は `minpaku-photo-fix` スキルが使えます（同じ補正を3枚にかければトーンが揃います）。

---

## お問い合わせの設定（初回だけ・2つ）

問い合わせは **フォームが本線／メールが予備／ココナラは補助と実績の証明** という並びにしてあります。
LINEは外しました（データも消してあるので、戻したくなったら言ってください）。

```
お仕事のご依頼・ご相談
  ↓
[ お問い合わせフォーム ]        ← メイン
  ↓
メールでも受け付けています
info@risalink1.com              ← 予備
  ──────────────────────
ココナラをご利用の方へ           ← 補助（区切って小さく）
「ココナラのページを見る →」
```

ココナラは**プロフィールページにも**「販売実績104件・総合評価4.8 → 評価・レビューを見る」として
置いてあります。こちらは依頼導線ではなく、**数字の裏付け**としての役割です。

### ① フォームを動かす（Formspree・無料）

いまは `endpoint` が空なので、**フォームは表示されず、メールだけ**が出ています。
（設定前の壊れたフォームを公開しないようにしてあります）

1. https://formspree.io/ で無料登録する
2. New Form を作る
3. 表示される `https://formspree.io/f/xxxxxxxx` の **`xxxxxxxx` の部分**をコピー
4. `content/site.json` の `contact.form.endpoint` に貼る
5. `npm run build`

これでフォームが出ます。送信されるとご自身のメールに届きます（無料枠は月50件）。
送信後は「お問い合わせありがとうございます」の画面に戻る設定も入れてあります。

### ② メールアドレスを作る（Xserver・無料）

`info@risalink1.com` はまだ存在しません。Xserverのサーバーパネルで作れます。

1. Xserverサーバーパネル → メールアカウント設定 → `risalink1.com` を選ぶ
2. メールアカウント追加 → `info` で作成
3. 転送設定で普段のGmailに転送しておくと見逃しません

⚠️ **Xserverのサーバー契約が試用期間中（2026/08/23まで）です。** 支払わないとメールもドメインの
サイトも止まります。ここは先に対応が必要です。

アドレスを変える場合は `content/site.json` の `contact.email` の `user` と `domain` を書き換えます。

> メールアドレスはHTMLに直接書かず、**JavaScriptで組み立てて表示**しています。
> 自動収集されるスパムを減らすためです。

---

## よくある更新

| やりたいこと | 直すファイル |
|---|---|
| 記事を書く | `content/posts/` に `.md` を追加 |
| キャッチコピーを変える | `site.json` の `concept.catch` |
| ファーストビューの写真を変える | `assets/fv/` に置いて `site.json` の `hero.slides` |
| 事業内容の柱を増やす／減らす | `services.json` の `pillars` |
| 柱の中の項目を足す | その柱の `items` |
| 実績の数字を変える | `site.json` の `stats` |
| 経歴を追加する | `profile.json` の `career` |
| 事業の進捗を更新する | `business.json` の `status` と `body` |
| SNSアカウントを隠す | `accounts.json` のそのアカウントを `"public": false` |
| お客様の声を追加する | `testimonials.json` の `items` |
| 色を変える | `assets/tokens.css` の `--accent` など |
| フォントを変える | `assets/tokens.css` の `--font-mincho` など |
| メールアドレスを変える | `site.json` の `contact.email` |
| フォームの項目を変える | `site.json` の `contact.form.fields.topics` |
| ココナラのブロックを消す | `site.json` の `contact.alt.show` を `false` |
| メニューの項目を変える | `scripts/build.mjs` の `NAV` |

---

## 動き（JavaScript）について

サイトの動きは各HTMLの一番下に入っている **数十行のJavaScript** で作っています。
外部のライブラリは使っていないので、インストールするものはありません。
（**Java と JavaScript は別物です。Javaは不要です。**）

やっていること：

1. ファーストビューの写真を6秒ごとにフェードで切り替える
2. スクロールすると見出しが下からせり上がる／本文がふわっと現れる
3. 見出し帯を抜けたらヘッダーに背景色をつける
4. スマホのメニュー（右上の≡）の開閉
5. ページ内リンクをなめらかにスクロール

**JavaScriptが動かない環境でも、文章はすべて表示されます**（隠す指定は `.js` が付いているときだけ効く作りです）。
「動きを減らす」設定にしている人には、動きなしで表示されます。

---

## ローカルで確認する

```bash
npm run serve
```

http://localhost:4321 が開きます。`/service/` のようなURLもそのまま確認できます。

---

## Figma連携

初回だけ設定が必要です。

```bash
cp .env.example .env
```

`.env` を開いて2つの値を書き込みます。

- `FIGMA_TOKEN` … Figma右上のアカウントメニュー → Settings → Security →
  「Personal access tokens」→ Generate new token（スコープ **File content: Read**）
- `FIGMA_FILE_KEY` … FigmaファイルのURL `https://www.figma.com/design/【ここ】/名前`

`.env` はGitに含まれないので、トークンが公開されることはありません。

### ① デザイン実績を自動で載せる

```bash
npm run figma:works && npm run build
```

Figmaファイルに **「HP掲載」という名前のページ** を作り、載せたいバナー・LPをフレームで並べておきます。
フレーム名の付け方でカテゴリと説明も付けられます。

```
バナー｜夏セールLP / Photoshopで制作した広告バナー
└カテゴリ └タイトル   └説明文
```

先頭に `_` を付けたフレーム（例: `_下書き`）は無視されます。

### ② 色・書体をFigmaと揃える

```bash
npm run figma:tokens && npm run build
```

Figmaのカラースタイル名を `accent` `ink` `cream` のように付けておくと、
`assets/tokens.css` の `--accent` などに反映されます。

> Figma APIは「スタイルを実際に塗ってあるレイヤー」からしか色を読めません。
> Figmaファイルのどこかに、各カラースタイルを塗った四角を並べた
> パレット用フレームを1つ作っておいてください（1回でOK）。

Figmaに無い色は既定値のまま残るので、サイトが急に崩れることはありません。

### ③ Figmaのデザインを読み取る

```bash
npm run figma:inspect                 # ページ一覧を見る
npm run figma:inspect -- "ページ名"    # そのページを詳しく書き出す
```

### ①②をまとめて実行

```bash
npm run figma:all
```

---

## 公開する

```bash
git add -A && git commit -m "サイトを更新" && git push
```

GitHub Pages に反映されるまで1〜2分かかります。**ページを何枚増やしても無料です。**

---

## 構成

```
content/          ← 編集するのはここ
  posts/            記事（.md を置くだけで増える）
assets/
  tokens.css        色・フォント・余白の定義（Figma連携で上書きされる）
  style.css         レイアウトと動きのCSS
  fv/               ファーストビューの写真（いまは仮画像）
  images/           プロフィール写真など
  posts/            記事の写真
  works/            Figmaから書き出された実績画像
scripts/
  build.mjs         content → 全ページのHTML
  lib-markdown.mjs  記事のMarkdown変換
  figma-*.mjs       Figma連携
archive/
  v1.html           旧サイト（2026-06版）

↓ 以下は自動生成。編集しない
index.html  service/  works/  business/  profile/  news/  contact/
sitemap.xml  robots.txt
```

## 使っているフォント

Google Fonts から読み込んでいます（無料・商用可）。

- **Zen Old Mincho** … 見出し・キャッチコピー（明朝）
- **Crimson Pro** … 英字（Service / Works などの小見出し）
- **Zen Kaku Gothic New** … 本文
