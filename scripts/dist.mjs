#!/usr/bin/env node
/**
 * dist.mjs — 公開して良いファイルだけを dist/ に集める
 *
 *   npm run dist
 *
 * content/ や scripts/ や .env は「サイトの材料」であって公開物ではないので、
 * ここで明確に除外します。Cloudflare Pages などに上げるのは dist/ の中身だけです。
 */
import { cpSync, rmSync, mkdirSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = join(ROOT, 'dist');

/** 公開するもの */
const PAGES = ['index.html', 'sitemap.xml', 'robots.txt'];
const DIRS = ['assets', 'service', 'works', 'business', 'profile', 'news', 'contact', 'archive'];

rmSync(DIST, { recursive: true, force: true });
mkdirSync(DIST, { recursive: true });

for (const f of PAGES) {
  if (existsSync(join(ROOT, f))) cpSync(join(ROOT, f), join(DIST, f));
}
for (const d of DIRS) {
  if (existsSync(join(ROOT, d))) cpSync(join(ROOT, d), join(DIST, d), { recursive: true });
}

/* 念のため、機密が紛れ込んでいないか確認する */
const walk = (dir) => readdirSync(dir).flatMap((n) => {
  const p = join(dir, n);
  return statSync(p).isDirectory() ? walk(p) : [p];
});
const files = walk(DIST);
const bad = files.filter((p) => /(^|\/)\.env$|\.env\.|(^|\/)\.git(\/|$)|node_modules/.test(p));
if (bad.length) {
  console.error('✗ 公開してはいけないファイルが混ざっています:\n' + bad.join('\n'));
  process.exit(1);
}

const bytes = files.reduce((n, p) => n + statSync(p).size, 0);
console.log(`✓ dist/ に ${files.length} ファイル（${(bytes / 1024 / 1024).toFixed(1)} MB）`);
console.log('  公開されるのはこのフォルダの中身だけです（content/ scripts/ .env は含みません）');
