# ケータイから「自動編集」を動かす手順（Windows版）

すぎちゃんさんのWindows PCに入っている **スキル＋自動編集キット** を、
スマホのClaudeアプリから動かせるようにするためのセットアップ手順です。

---

## 0. まず仕組みだけ理解する（ここ大事）

```
[スマホのClaudeアプリ]
        │  指示＋スクショを送る
        ▼
   Anthropicのサーバー（中継するだけ）
        │
        ▼
[すぎちゃんのWindows PC で動いてる Claude Code]  ← 実際の処理はぜんぶココ
        │  ffmpeg / 自動編集スキルを実行
        ▼
   PCの output フォルダ → クラウド同期 → スマホで確認
```

ポイントは2つ。

1. **スマホは「リモコン」でしかない。** 編集そのものはPCがやる。
   だから **PCの電源が入っていて、Claude Codeが起動しっぱなし** である必要がある。
2. この仕組みの名前は **Remote Control（リモートコントロール）**。
   クラウドで動く「Claude Code on the web」とは別物。
   自動編集キットはPCの中にあるので、**必ずRemote Controlの方**を使う。

---

## 1. 事前チェック（これが揃ってないと動かない）

| 項目 | 条件 |
|---|---|
| プラン | **Pro / Max / Team / Enterprise**（無料プランは不可） |
| ログイン方法 | **claude.aiアカウントでログイン**。APIキー（`ANTHROPIC_API_KEY`）だと使えない |
| Claude Codeのバージョン | **v2.1.51以降**（`claude --version` で確認） |
| スマホ | Claudeアプリ（iOS / Android）を入れて **同じアカウント** でログイン |

バージョンが古かったらPowerShellで:

```powershell
claude update
```

---

## 2. PC側のセットアップ（最初の1回だけ）

### 2-1. Git for Windows を入れる ★超重要

自動編集キットが `bash` のスクリプトやコマンドを使っている場合、
**Git for Windows が入っていないとClaude CodeはPowerShellで動こうとして失敗します。**

- https://git-scm.com/downloads/win からインストール（設定はぜんぶデフォルトでOK）

入れたのに認識されない場合は、`C:\Users\（ユーザー名）\.claude\settings.json` に追記:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

### 2-2. ffmpeg が動くか確認

自動編集キットはだいたい ffmpeg を使うので、PowerShellで:

```powershell
ffmpeg -version
```

「認識されていません」と出たら ffmpeg を入れる（`winget install Gyan.FFmpeg` が早い）。
入れたあとは **PowerShellを一度閉じて開き直す**。

### 2-3. claude.aiアカウントでログインし直す

```powershell
claude auth login
```

→ ブラウザが開くので「claude.ai」の方を選んでログイン。

### 2-4. 作業フォルダで一度だけ普通に起動する

Remote Controlは「信頼済みフォルダ」でしか始められません。
**自動編集キットが入っているフォルダ**（例：`C:\Users\sugi\video-kit`）で:

```powershell
cd C:\Users\sugi\video-kit
claude
```

→ 「このフォルダを信頼しますか？」に **Yes**。確認できたら `/exit` で抜けてOK。

### 2-5. スマホ通知と自動接続をONにする

`claude` を起動した状態で:

```
/config
```

ここで次の3つをONにする。

- **Enable Remote Control for all sessions** … 毎回コマンドを打たなくても自動でスマホと繋がる
- **Push when Claude decides** … 編集が終わったらスマホに通知が飛ぶ
- **Push when actions required** … 「実行していい？」の確認をスマホに飛ばす

### 2-6. PCがスリープしないようにする

Windowsの `設定 → システム → 電源とバッテリー → 画面とスリープ`
→ **「次の時間が経過後にデバイスをスリープ状態にする」を「なし」** に。

（スリープするとスマホから繋がらなくなります。画面OFFだけならOK）

---

## 3. 動画とスクショをどう渡すか ← ここが一番のキモ

スマホからPCへのファイルの渡し方は、**サイズで使い分け**ます。

### ✅ スクショ・写真・短いクリップ → アプリから直接添付でOK

Claudeアプリのメッセージ欄からそのまま添付すればいい。
- **画像** … Claudeがその場で中身を見てくれる
- **画像以外のファイル** … PCに自動ダウンロードされて `@ファイル名` として渡される

ただし **1ファイル30MBまで**。スマホで撮った動画はすぐ超えるので、動画は次の方法にする。

### ✅ 本番の動画素材 → クラウド同期フォルダ経由（おすすめ）

これが一番ラクで確実。**Googleドライブ or OneDrive のデスクトップアプリ**をPCに入れて、
PC側にフォルダを2つ作っておく。

```
C:\Users\sugi\video-kit\input     ← スマホから動画を置く場所
C:\Users\sugi\video-kit\output    ← 編集済みが出てくる場所
```

この2つをクラウド同期の対象にしておく。

**スマホ側の流れ:**
1. 写真アプリで動画を選ぶ
2. 共有 → Googleドライブ（or OneDrive）→ `input` フォルダを選んでアップ
3. アップが終わったらClaudeアプリで指示を送る

> ファイル名は `20260821_01.mp4` のように **日付＋連番** にしておくと、
> 「今日のいちばん新しいやつ」とだけ言えば通じるようになります。

---

## 4. 毎回の運用フロー（慣れたら30秒）

### PC側（家を出る前に1回）

作業フォルダでこれを打つだけ:

```powershell
cd C:\Users\sugi\video-kit
claude remote-control --name "動画編集"
```

- ターミナルにセッションのURLが出る
- **スペースキーを押すとQRコードが出る** → スマホでスキャンすればアプリで一発で開く
- **このターミナルは閉じないこと**（閉じると切れる）

※ 2-5で「Enable Remote Control for all sessions」をONにしたなら、
普通に `claude` と打つだけでも繋がります。

### スマホ側

1. Claudeアプリを開く → 下の **「Code」タブ**
2. セッション一覧に「動画編集」が出てくる（**PCアイコン＋緑の点＝オンライン**）
3. タップして開く
4. 動画をドライブの `input` に上げる
5. メッセージを送る。例:

   ```
   input フォルダのいちばん新しい動画で自動編集を実行して。
   サムネはこのスクショの雰囲気に寄せて。終わったら通知して。
   ```
   （ここでスクショを添付する）

6. 「このコマンド実行していい？」の確認が来たら **スマホでタップして承認**
7. 完了通知が来たら `output` フォルダをスマホのドライブアプリで確認 → ダウンロード

---

## 5. もっとラクにする小ワザ

### CLAUDE.md に決まりごとを書いておく

`C:\Users\sugi\video-kit\CLAUDE.md` に、毎回言うことを書いておくと省略できる。

```markdown
# 動画自動編集ルール

- 素材はつねに `input/` の中の最新の .mp4 を対象にする
- 完成品は `output/` に `編集済み_元ファイル名.mp4` で出す
- スマホから指示が来たら、途中経過より「完了したか」を優先して報告する
- 処理が終わったら必ずプッシュ通知を送る
```

こうしておくと、スマホからは **「いつものやつ、お願い」** で通るようになります。

### 通知を明示的に頼む

長い処理のときは指示文に **「終わったら通知して」** と入れておくと確実です。

---

## 6. うまくいかないときのチェックリスト

| 症状 | 原因と対処 |
|---|---|
| スマホのCodeタブにセッションが出ない | PCのターミナルを閉じてないか / PCがスリープしてないか確認 |
| `Remote Control requires a claude.ai subscription` | APIキーでログインしてる。`ANTHROPIC_API_KEY` を消して `claude auth login` |
| `Remote Control isn't enabled for this account` | `claude auth logout` → `claude auth login` でやり直し。それでもダメなら `claude doctor` |
| `/remote-control` が「不明なコマンド」 | バージョンが古い。`claude update` |
| 通知が来ない | `/config` が「No mobile registered」ならスマホでClaudeアプリを一度開く。iOSは集中モード、Androidはバッテリー最適化の除外も確認 |
| bashのコマンドが失敗する | Git for Windows が未インストール（2-1参照） |
| セッションが勝手に切れた | ネット断が10分続くとサーバーモードは終了する。`claude remote-control` を打ち直す |
| ターミナルを閉じちゃった | 4時間以内なら同じフォルダで `claude remote-control --continue` で復活できる |

---

## 7. やってはいけないこと

- ❌ **Claude Code on the web（claude.ai/code の新規セッション）で自動編集を頼む**
  → クラウド上で動くのでPCの自動編集キットもffmpegも動画素材も存在しない。必ずRemote Controlで。
- ❌ **PCをシャットダウン／スリープさせたまま外出する**
- ❌ **30MB超の動画をアプリから直接添付しようとする** → ドライブ経由にする

---

## 参考リンク

- Remote Control 公式ドキュメント: https://code.claude.com/docs/en/remote-control
- Claude Code インストール（Windows）: https://code.claude.com/docs/en/setup
- Git for Windows: https://git-scm.com/downloads/win
