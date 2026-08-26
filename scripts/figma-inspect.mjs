#!/usr/bin/env node
/**
 * figma-inspect.mjs — ③ Figmaのデザインを読み取って中身を書き出す
 *
 *   npm run figma:inspect              … ファイル全体の構造を表示
 *   npm run figma:inspect -- "ページ名"  … そのページを詳しく書き出す
 *
 * Figmaで作ったページデザインを、テキスト・色・サイズ付きの一覧として
 * scratch/figma-inspect.md に書き出します。
 * 「このデザインどおりにHTMLにして」とAIに渡すための下ごしらえです。
 *
 * ※ Figmaの絶対配置をそのままHTMLに変換すると、スマホで崩れる／保守できない
 *   ものが出来上がります。このスクリプトは「設計図の読み取り」までを担当し、
 *   実際のHTML化は content/*.json と build.mjs 側で行う想定です。
 */

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { requireEnv, figma, ROOT, walk, ensureDir } from './figma-lib.mjs';

const { token, fileKey } = requireEnv();
const targetPage = process.argv[2];

console.log(`→ Figmaファイル ${fileKey} を読み込み中…`);
const file = await figma(`/files/${fileKey}`, token);
const pages = file.document.children || [];

if (!targetPage) {
  console.log(`\nファイル名: ${file.name}\n`);
  console.log('ページ一覧:');
  for (const p of pages) {
    const frames = (p.children || []).filter((n) => n.type === 'FRAME');
    console.log(`  - ${p.name}  (フレーム ${frames.length}個)`);
    for (const f of frames.slice(0, 12)) {
      const w = Math.round(f.absoluteBoundingBox?.width ?? 0);
      const h = Math.round(f.absoluteBoundingBox?.height ?? 0);
      console.log(`      · ${f.name}  ${w}×${h}`);
    }
    if (frames.length > 12) console.log(`      … ほか ${frames.length - 12}個`);
  }
  console.log('\n詳しく見るには:  npm run figma:inspect -- "ページ名"');
  process.exit(0);
}

const page = pages.find((p) => p.name.trim() === targetPage.trim());
if (!page) {
  console.error(`✗ ページ「${targetPage}」が見つかりません。ページ一覧: ${pages.map((p) => p.name).join(' / ')}`);
  process.exit(1);
}

const hex = (c) => {
  const to = (v) => Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).padStart(2, '0');
  return `#${to(c.r)}${to(c.g)}${to(c.b)}`.toUpperCase();
};

const lines = [
  `# Figma 読み取り: ${file.name} / ${page.name}`,
  '',
  `- ファイルキー: \`${fileKey}\``,
  `- 取得日: ${new Date().toISOString().slice(0, 10)}`,
  '',
  '各行のフォーマット: `階層 種別 名前  [サイズ]  {色}  "テキスト"`',
  '',
  '```',
];

const texts = [];
for (const { node, depth } of walk(page)) {
  if (depth === 0) continue;
  if (depth > 8) continue;
  const bb = node.absoluteBoundingBox;
  const size = bb ? `[${Math.round(bb.width)}×${Math.round(bb.height)}]` : '';
  const solid = (node.fills || []).find((f) => f.type === 'SOLID' && f.visible !== false);
  const color = solid ? `{${hex(solid.color)}}` : '';
  let txt = '';
  if (node.type === 'TEXT' && node.characters) {
    const one = node.characters.replace(/\n/g, ' ⏎ ');
    txt = `"${one.length > 80 ? one.slice(0, 80) + '…' : one}"`;
    texts.push({
      text: node.characters,
      size: node.style?.fontSize,
      weight: node.style?.fontWeight,
      family: node.style?.fontFamily,
    });
  }
  lines.push(`${'  '.repeat(depth - 1)}${node.type.padEnd(9)} ${node.name}  ${size} ${color} ${txt}`.trimEnd());
}
lines.push('```', '');

if (texts.length) {
  lines.push('## テキスト一覧（そのままコピーできます）', '');
  for (const t of texts) {
    const meta = [t.family, t.size ? `${Math.round(t.size)}px` : null, t.weight ? `w${t.weight}` : null]
      .filter(Boolean).join(' / ');
    lines.push(`- ${meta ? `\`${meta}\` ` : ''}${t.text.replace(/\n/g, '  \n  ')}`);
  }
  lines.push('');
}

const outDir = join(ROOT, 'scratch');
ensureDir(outDir);
const out = join(outDir, 'figma-inspect.md');
writeFileSync(out, lines.join('\n'), 'utf8');

console.log(`\n✓ scratch/figma-inspect.md に書き出しました（テキスト ${texts.length}件）`);
console.log('  このファイルをAIに渡して「この内容でHPを更新して」と伝えられます。');
