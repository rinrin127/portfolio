#!/usr/bin/env node
/**
 * figma-works.mjs — ① デザイン実績の自動掲載
 *
 *   npm run figma:works
 *
 * Figmaファイルの中の「特定のページ」にあるフレームを画像で書き出し、
 * assets/works/ に保存して content/works.json の items を作り直します。
 *
 * 使い方（Figma側の準備）
 *   1. Figmaファイルに「HP掲載」という名前のページを1つ作る（名前は .env で変更可）
 *   2. そのページに、載せたいバナー／LP／デザインをフレームとして並べる
 *   3. フレーム名がそのまま実績のタイトルになります
 *        例）「LPデザイン｜ココピタ / Photoshopで制作した商品LP」
 *            → カテゴリ「LPデザイン」／タイトル「ココピタ」／説明「Photoshopで…」
 *        区切り文字は ｜ と / 。無ければ全部タイトルになります。
 *   4. フレーム名の先頭に「_」を付けると、そのフレームは無視されます
 *
 * 実行後に `npm run build` すればサイトに反映されます。
 */

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { requireEnv, figma, ROOT, readContent, writeContent, ensureDir, slug } from './figma-lib.mjs';

const { token, fileKey } = requireEnv();
const PAGE_NAME = process.env.FIGMA_WORKS_PAGE || 'HP掲載';
const SCALE = Number(process.env.FIGMA_WORKS_SCALE || 2);
const FORMAT = (process.env.FIGMA_WORKS_FORMAT || 'png').toLowerCase();

console.log(`→ Figmaファイル ${fileKey} を読み込み中…`);
const file = await figma(`/files/${fileKey}?depth=2`, token);

const pages = file.document.children || [];
let page = pages.find((p) => p.name.trim() === PAGE_NAME);
if (!page && pages.length === 1) {
  // ページが1つしかないなら、名前が違ってもそれを使う（Figmaの初期名「Page 1」対策）
  page = pages[0];
  console.log(`  （「${PAGE_NAME}」という名前のページは無いので、唯一のページ「${page.name}」を使います）`);
}
if (!page) {
  const names = pages.map((p) => `「${p.name}」`).join(' / ');
  console.error(`✗ 「${PAGE_NAME}」という名前のページが見つかりませんでした。
  このファイルにあるページ: ${names || '（なし）'}
  ページ名を「${PAGE_NAME}」に変えるか、.env に FIGMA_WORKS_PAGE=ページ名 を追加してください。`);
  process.exit(1);
}

const frames = (page.children || []).filter(
  (n) => ['FRAME', 'COMPONENT', 'INSTANCE', 'GROUP'].includes(n.type) && !n.name.startsWith('_')
);

if (!frames.length) {
  console.log(`
まだ「${page.name}」ページにフレームがありません。

  Figmaでこのページに、サイトに載せたいバナーやLPを「フレーム」として並べてください。
  フレーム名の付け方でカテゴリと説明も入ります:

      バナー｜夏セールLP / Photoshopで制作した広告バナー
      └カテゴリ └タイトル   └説明文

  先頭に「_」を付けたフレーム（例: _下書き）は無視されます。
  並べ終わったら、もう一度  npm run figma:works  を実行してください。

（今回は content/works.json を変更していません）`);
  process.exit(0);
}
console.log(`  ${frames.length}個のフレームを検出: ${frames.map((f) => f.name).join(', ')}`);

// 画像URLを一括取得
const ids = frames.map((f) => f.id).join(',');
console.log('→ 画像を書き出し中…');
const rendered = await figma(
  `/images/${fileKey}?ids=${encodeURIComponent(ids)}&format=${FORMAT}&scale=${SCALE}`,
  token
);
if (rendered.err) throw new Error(`画像の書き出しに失敗しました: ${rendered.err}`);

const outDir = join(ROOT, 'assets', 'works');
ensureDir(outDir);

const items = [];
for (const f of frames) {
  const url = rendered.images[f.id];
  if (!url) {
    console.warn(`  ! ${f.name} の画像URLが取得できませんでした（スキップ）`);
    continue;
  }
  const res = await fetch(url);
  if (!res.ok) {
    console.warn(`  ! ${f.name} のダウンロードに失敗（${res.status}・スキップ）`);
    continue;
  }
  const buf = Buffer.from(await res.arrayBuffer());
  const fileName = `${slug(f.name)}.${FORMAT}`;
  writeFileSync(join(outDir, fileName), buf);

  // フレーム名 → カテゴリ｜タイトル / 説明
  const [head, note = ''] = f.name.split('/').map((s) => s.trim());
  const parts = head.split(/[｜|]/).map((s) => s.trim());
  const category = parts.length > 1 ? parts[0] : 'DESIGN';
  const title = parts.length > 1 ? parts.slice(1).join(' ') : parts[0];

  items.push({
    title,
    category,
    image: `assets/works/${fileName}`,
    href: '',
    note,
    _figmaNodeId: f.id,
  });
  console.log(`  ✓ ${fileName}  (${(buf.length / 1024).toFixed(0)} KB)`);
}

const works = readContent('works');
works.items = items;
works.figmaSyncedAt = new Date().toISOString().slice(0, 10);
writeContent('works', works);

console.log(`\n✓ content/works.json を更新しました（${items.length}件）`);
console.log('  続けて実行してください:  npm run build');
