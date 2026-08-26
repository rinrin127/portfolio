/**
 * figma-lib.mjs — Figma REST API の共通処理
 *
 * 必要な環境変数（.env に書く）
 *   FIGMA_TOKEN     … Figmaの個人アクセストークン（figd_ で始まる）
 *   FIGMA_FILE_KEY  … FigmaファイルURLの /design/ や /file/ の直後の英数字
 *
 * 例: https://www.figma.com/design/AbCdEf123456/My-Design
 *                                  ^^^^^^^^^^^^ これが FILE_KEY
 */

import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/** .env を読んで process.env に流し込む（依存パッケージなし） */
export function loadEnv() {
  const p = join(ROOT, '.env');
  if (!existsSync(p)) return;
  for (const raw of readFileSync(p, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const i = line.indexOf('=');
    if (i < 0) continue;
    const key = line.slice(0, i).trim();
    let val = line.slice(i + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
}

export function requireEnv() {
  loadEnv();
  const token = process.env.FIGMA_TOKEN;
  const fileKey = process.env.FIGMA_FILE_KEY;
  const missing = [];
  if (!token) missing.push('FIGMA_TOKEN');
  if (!fileKey) missing.push('FIGMA_FILE_KEY');
  if (missing.length) {
    console.error(`
✗ ${missing.join(' と ')} が設定されていません。

  1) .env.example をコピーして .env を作る
       cp .env.example .env
  2) .env を開いて、値を書き込む
       FIGMA_TOKEN    … Figma → 右上のアカウントメニュー → Settings → Security →
                        「Personal access tokens」→ Generate new token
                        （スコープは File content: Read が必要です）
       FIGMA_FILE_KEY … 対象ファイルのURLから取る
                        https://www.figma.com/design/【ここ】/ファイル名

  ※ .env はGitに含まれません（.gitignore 済み）。
`);
    process.exit(1);
  }
  return { token, fileKey };
}

/** Figma API を叩く */
export async function figma(path, token) {
  const res = await fetch(`https://api.figma.com/v1${path}`, {
    headers: { 'X-Figma-Token': token },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    if (res.status === 403) {
      throw new Error(`Figma APIが403を返しました。トークンの権限（File content: Read）と、そのファイルへのアクセス権を確認してください。\n${body.slice(0, 300)}`);
    }
    if (res.status === 404) {
      throw new Error(`Figma APIが404を返しました。FIGMA_FILE_KEY が間違っている可能性があります。\n${body.slice(0, 300)}`);
    }
    throw new Error(`Figma API ${res.status}: ${body.slice(0, 300)}`);
  }
  return res.json();
}

/** ノードツリーを深さ優先で歩く */
export function* walk(node, depth = 0, parent = null) {
  yield { node, depth, parent };
  for (const child of node.children || []) yield* walk(child, depth + 1, node);
}

/** content/*.json を読み書きする */
export function readContent(name) {
  return JSON.parse(readFileSync(join(ROOT, 'content', `${name}.json`), 'utf8'));
}
export function writeContent(name, obj) {
  writeFileSync(join(ROOT, 'content', `${name}.json`), JSON.stringify(obj, null, 2) + '\n', 'utf8');
}

export function ensureDir(p) {
  mkdirSync(p, { recursive: true });
}

/** ファイル名に使える文字だけにする */
export function slug(s) {
  return String(s)
    .trim()
    .replace(/[\/\\:*?"<>|]/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 60);
}
