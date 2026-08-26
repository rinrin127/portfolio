#!/usr/bin/env node
/**
 * figma-tokens.mjs — ② 色・文字のテーマ同期
 *
 *   npm run figma:tokens
 *
 * Figmaに登録した「スタイル」（カラースタイル／テキストスタイル）を読み取り、
 * assets/tokens.css を作り直します。Figmaで色を変えたら、このコマンド1つで
 * サイトの配色が揃います。
 *
 * 使い方（Figma側の準備）
 *   ローカルスタイルの名前を、CSS変数名にしたい名前で付けます。
 *     色     : 「ink」「accent」「cream」など → --ink / --accent / --cream
 *     階層可 : 「brand/accent」 → --brand-accent
 *   ※ Figmaのスタイル名は日本語でも動きますが、英数字を推奨します。
 *
 * 安全のため、Figma側に無いトークンは既定値のまま残します
 *   （＝サイトが急に崩れることはありません）。
 */

import { writeFileSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { requireEnv, figma, ROOT, walk } from './figma-lib.mjs';

const { token, fileKey } = requireEnv();

/* --- 既定値（Figmaに該当スタイルが無いときはこれが使われる） --- */
const DEFAULTS = {
  ink: '#4A382F', 'ink-soft': '#7A6558', 'ink-faint': '#A8968A',
  cream: '#FBF4EC', 'cream-deep': '#F5E9DD', white: '#FFFFFF',
  accent: '#B4505D', 'accent-soft': '#D0808A', 'accent-pale': '#F6E4E6',
  'accent-on-dark': '#E8A9B0', line: '#EADCD0', dark: '#3B2C26',
};

const hex = (c) => {
  const to = (v) => Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).padStart(2, '0');
  return `#${to(c.r)}${to(c.g)}${to(c.b)}`.toUpperCase();
};
const cssName = (s) => s.trim().toLowerCase().replace(/[\s\/]+/g, '-').replace(/[^a-z0-9-]/g, '');

console.log(`→ Figmaファイル ${fileKey} のスタイルを読み込み中…`);
const meta = await figma(`/files/${fileKey}`, token);

const styles = meta.styles || {};
const fillStyleIds = new Set(
  Object.entries(styles).filter(([, s]) => s.styleType === 'FILL').map(([id]) => id)
);
const textStyleIds = new Set(
  Object.entries(styles).filter(([, s]) => s.styleType === 'TEXT').map(([id]) => id)
);

/* スタイルIDを実際に使っているノードから色・書体を拾う */
const colors = {};
const fonts = {};
for (const { node } of walk(meta.document)) {
  const fillId = node.styles?.fill || node.styles?.fills;
  if (fillId && fillStyleIds.has(fillId)) {
    const solid = (node.fills || []).find((f) => f.type === 'SOLID' && f.visible !== false);
    if (solid) colors[cssName(styles[fillId].name)] = hex(solid.color);
  }
  const textId = node.styles?.text;
  if (textId && textStyleIds.has(textId) && node.style?.fontFamily) {
    fonts[cssName(styles[textId].name)] = node.style.fontFamily;
  }
}

const found = Object.keys(colors);
if (!found.length) {
  console.warn(`
! Figmaのカラースタイルから色を1つも取得できませんでした。

  Figma REST API は「スタイルを実際に適用しているレイヤー」からしか色を読めません。
  対策：Figmaファイルのどこかに、各カラースタイルを塗った四角を1つずつ並べた
        パレット用のフレームを作っておいてください（1回作れば以降ずっと効きます）。

  既定の配色のまま tokens.css を書き出します。
`);
} else {
  console.log(`  取得した色: ${found.map((k) => `${k}=${colors[k]}`).join(' / ')}`);
}
if (Object.keys(fonts).length) {
  console.log(`  取得した書体: ${[...new Set(Object.values(fonts))].join(' / ')}`);
}

const merged = { ...DEFAULTS, ...colors };
const primaryFont = Object.values(fonts)[0];
const fontStack = primaryFont
  ? `"${primaryFont}", "Noto Sans JP", -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif`
  : `"Noto Sans JP", -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif`;

/* 既存 tokens.css の Typography 以降（レイアウト等）はそのまま活かす */
const current = readFileSync(join(ROOT, 'assets', 'tokens.css'), 'utf8');
const tail = current.slice(current.indexOf('  /* --- Typography --- */'));
const tailWithFont = tail.replace(/--font-sans:.*?;/s, `--font-sans: ${fontStack};`);

const out = `/* ============================================================
   デザイントークン
   自動生成: npm run figma:tokens（${new Date().toISOString().slice(0, 10)}）
   Figmaファイル: ${fileKey}
   ------------------------------------------------------------
   手で編集してもかまいませんが、次に figma:tokens を実行すると
   --- Color --- のブロックは上書きされます。
   ============================================================ */

:root {
  /* --- Color --- */
${Object.entries(merged).map(([k, v]) => `  --${k}:${' '.repeat(Math.max(1, 12 - k.length))}${v};`).join('\n')}

${tailWithFont}`;

writeFileSync(join(ROOT, 'assets', 'tokens.css'), out, 'utf8');
console.log(`\n✓ assets/tokens.css を更新しました（色 ${Object.keys(merged).length}件）`);
console.log('  続けて実行してください:  npm run build');
