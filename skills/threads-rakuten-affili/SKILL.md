---
name: threads-rakuten-affili
description: Threads×楽天アフィリエイトの全自動運用パイプライン。「今日のスレッズ」「承認キュー作って」「スレッズ楽天」「投稿候補出して」などの依頼、または毎朝の定時実行で必ずこのスキルを使う。商品リサーチ→投稿文生成→事前採点→コンプラ検査→承認キュー出力→（承認後）Threads API投稿→インサイト収集→週次分析までを担当。承認の返信（「1,3,5 OK」等）を受けたら投稿実行フェーズとしてもこのスキルを使う。「比較投稿作って」「買い替えたやつで比較」など比較モードの依頼にもこのスキルを使う。
---

# threads-rakuten-affili v1.1

Threads × 楽天アフィリエイト自動化パイプライン。
りんりんの作業は**毎朝の承認返信1行のみ**。それ以外は全自動。

設計書：Drive「Threads楽天アフィ/00_設計書_v1.md」参照。
TikTokショップアフィv4パイプラインからの横展開（skill-transfer）。

モードは2つ。**日次＝単品モード**（毎朝・楽天APIの人気商品から）と、
**週1＝比較モード**（りんりんが買い替えた商品からスレッド型比較を1本）。

---

## 初回セットアップ（未完了なら最優先で実行）

`config/.env` が存在しない、または必須キーが空の場合はセットアップモードに入る。

1. `.env.example` を `.env` にコピーし、以下を順に案内して埋める：
   - `RAKUTEN_APP_ID`：https://webservice.rakuten.co.jp/ で「アプリID発行」（無料・即時）。りんりんに手順を1つずつ案内し、発行されたIDを聞いて書き込む
   - `RAKUTEN_AFFILIATE_ID`：https://affiliate.rakuten.co.jp/ ログイン後、右上メニュー→「パラメータ確認」等で表示されるアフィリエイトID（xxxx.xxxx.xxxx 形式）
   - `THREADS_ACCESS_TOKEN` / `THREADS_USER_ID`：Meta開発者手順は `references` 節（本ファイル末尾）の通り案内
2. `python scripts/rakuten_search.py --test` で楽天API疎通確認
3. `python scripts/threads_post.py --test` でThreads API疎通確認（投稿はしない、権限確認のみ）
4. `config/persona.md` をりんりんと1往復で初回チューニング
5. テスト実行：日次フローを1周し、承認キューの見た目を確認してもらう

**トークン等の秘密情報は `.env` のみに保存。SKILL.md・Drive・チャットログに書かない。**

## 日次フロー（朝の実行）

すべて質問なしで自動実行し、最後に承認キューだけ提示する。

```bash
cd ~/.claude/skills/threads-rakuten-affili

# STEP A: 商品リサーチ（上位10商品を抽出）
python scripts/rakuten_search.py --out work/products_$(date +%y%m%d).json

# STEP B: 投稿文生成 → ここはAIが担当
#   work/products_*.json の上位商品から5本の投稿文を生成する。
#   ルール: config/hooks_config.md の6フック型 + config/persona.md に従う。
#   構成: ①フック1行 ②本文2〜5行(200〜350字) ③CTA1行
#   本文はレビュー由来の事実のみ。「レビューでは〜の声」形式。体験談の捏造禁止。
#   絵文字3個まで。共感だけの空フレーズ禁止。
#   出力: work/posts_YYMMDD.json （scripts/approval_queue.py --schema でフォーマット確認可）

# STEP C: 事前採点 → AIが担当
#   config/scoring_rubric.md の5軸100点で各投稿を採点しJSONに書き込む。
#   80点以上=推奨 / 60-79=1回リライトして再採点 / 60未満=破棄

# STEP D: コンプラ検査（機械・全数）
python scripts/compliance_check.py work/posts_$(date +%y%m%d).json

# STEP E: 承認キュー生成 → Driveへ保存
python scripts/approval_queue.py --build work/posts_$(date +%y%m%d).json
```

STEP Eの出力4点セットをDriveの「Threads楽天アフィ/日次/」へ保存する
（markdown保存は `contentMimeType: text/markdown` + `disableConversionToGoogleType: True` 必須）：
1. `YYMMDD_承認キュー.md`
2. `YYMMDD_商品リサーチ.md`
3. `YYMMDD_トラッキング.md`（fetch_insights.pyの前日結果）
4. `posts_log.csv`（累積・上書きではなく新版アップ→旧版削除案内）

最後にチャットで承認キューの要約（各投稿の1行目＋スコア＋コンプラ判定のみ）を提示して終了。
**承認を催促しない。返信を待つ。**

## 承認返信を受けたら（投稿フェーズ）

返信例：「1,3,5 OK」「2は値段推しに直して」「全部OK」「今日はスキップ」

```bash
# 承認された番号のみ予約投稿（config/post_times.jsonの時刻に割当）
python scripts/threads_post.py --publish work/posts_YYMMDD.json --approved 1,3,5
```

- 修正指示があった投稿はリライト→再採点→再提示（1往復のみ、2回目の指示は「そのまま反映」）
- 投稿完了後、投稿IDを posts_log.csv に追記
- **承認されていない投稿は絶対に投稿しない**（Phase 2で自動投稿に移行するまで）

## 比較モード（週1本・「比較投稿作って」で起動）

日次フローとは別ルート。**商品を探させない**のがこのモードの要点。
入力は `config/my_products.md`（りんりんが実際に買い替えた商品メモ）だけ。

`config/my_products.md` の記入欄が空なら、**実行せずに**こう返して終わる：
> 「楽天アプリの購入履歴から、2回以上買った／別のものに買い替えた商品を3つ、
> 『今／前／理由』の3行で `config/my_products.md` に書いてください」

記入があれば質問なしで最後まで実行する。

```bash
cd ~/.claude/skills/threads-rakuten-affili

# STEP 1: my_products.md からカテゴリを1つ選ぶ → AIが担当
#   選定チェック3問（my_products.md 記載）を通ったものだけ。通らなければ実行しない

# STEP 2: 選んだカテゴリの候補を楽天から取得（事実の裏取りのみ）
python scripts/rakuten_search.py --keywords "<選んだカテゴリ>,<競合になる語>" \
       --out work/compare_$(date +%y%m%d).json

# STEP 3: スレッド型比較の生成 → AIが担当
#   config/comparison_template.md の型どおりに、親1本＋ぶら下げ3本を生成する。
#   ・勝者を1つに決めない。3商品それぞれに「向いている人／向いていない人」を書く
#   ・体験は書かない → 【ここに体験：〜】を3か所空ける
#   ・価格・容量は書かない → 【要確認：〜】にする
#   出力: work/posts_YYMMDD.json（thread配列を持つ形。--schema で確認可）

# STEP 4-5: 採点・コンプラ検査・承認キュー（日次と同じスクリプトがそのまま通る）
python scripts/compliance_check.py work/posts_$(date +%y%m%d).json
python scripts/approval_queue.py --build work/posts_$(date +%y%m%d).json
```

承認キューには「📝 記入待ち: 体験3か所／要確認2か所」が出る。
**りんりんがそこを埋めるまで `threads_post.py` は投稿をブロックする**（機械で止まる）。
埋め終わったら `compliance_check.py` を再実行 → 承認 → 投稿。

- 体験欄は使っていない商品には書かない。競合2つは削除で通してよい
- 埋めなかった `【要確認：〜】` は、その一文ごと削除して投稿する（推測で数値を書かない）
- 同じカテゴリで2本目を作らない。2本目は `my_products.md` を別カテゴリに差し替えるだけ

## インサイト収集（投稿24h後・72h後）

```bash
python scripts/fetch_insights.py   # 対象投稿を自動判定してCSV追記
```

## 週次分析（土曜）

```bash
python scripts/weekly_review.py --out work/weekly_$(date +%y%m%d).md
```

出力の骨組み（型別ランキング表）にAIが分析コメントを追記：
- 伸びた型2つ／捨てる型1つの提案
- `config/hooks_config.md` への反映差分を提示 → りんりん承認後に書き換え
- 楽天成果の手動入力枠（報酬額・発生件数・クリック数）を空欄で用意し、入力を1行依頼
- 数値をもらえたら `--clicks/--revenue/--orders/--target` を付けて再実行し、
  **EPC（1クリック単価）** と目標到達に必要なクリック数まで出す。
  楽天は「クリック→24h以内にかご入れ→89日以内に購入完了」で成果になり、
  紹介商品以外のかご入れも対象になり得るため、単価ではなくEPCを主KPIにする

## 絶対ルール（v4から継承）

- 表現は**楽天商品ページ記載内容のみ**使用可。断定的効果効能は`compliance_check.py`が機械ブロック
- 全投稿に「#PR」自動付与（景表法ステマ規制対応、欠落は投稿ブロック）
- 同一文面の再投稿禁止（posts_log.csvと照合）
- Phase 1（初月）は1日2〜3本まで（スパム判定回避）
- 標準語で書く
- 1入力→質問なし自動生成。「おまかせ」=全デフォルト
- 数値計算はPythonに委譲。完了はコマンド実行結果で検証
- **体験と数値はAIが書かない。** プレースホルダ（`【ここに体験：〜】`『`【要確認：〜】`）で空け、
  りんりんが埋める。未記入のまま投稿しようとしたら機械がブロックする
- 1商品あたりの成果報酬には上限があるため高額商品は狙わない（衝動買い帯1,500〜6,000円）。
  料率・上限・成果条件は変更されうるので、断定して書かず公式ページで都度確認する

## references: Threads APIセットアップ手順（初回のみ）

1. https://developers.facebook.com/ → 「マイアプリ」→「アプリを作成」→ ユースケースで「Threads APIにアクセス」を選択
2. アプリ作成後、「Threads API」→「設定」でリダイレクトURI等を設定（テスト用なら https://localhost で可）
3. 「Threadsテスター」に運用アカウントを追加 → Threadsアプリ側で承認
4. Graph API Explorerまたは認可フローで短期トークン取得 → `threads_access_token` エンドポイントで**長期トークン（60日）**に交換
5. `.env` に `THREADS_ACCESS_TOKEN` と `THREADS_USER_ID`（me?fields=id で取得）を保存
6. 以後のトークン延命は `python scripts/token_refresh.py`（週次実行、失効7日前に承認キューへ⚠️表示）
