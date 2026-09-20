#!/usr/bin/env node
/**
 * scripts/selfback/run.mjs — A8.net セルフバック 半自動チェッカー
 *
 *   node scripts/selfback/run.mjs [--debug] [--headless] [--config <path>]
 *
 * やること:
 *   1. ブラウザを自動で開く（初回は自分でログインしてもらう。パスワードはこのツールに一切渡さない）
 *   2. ログインセッションを state/ に保存し、次回以降は自動で再利用する
 *   3. config.json で指定した「セルフバック案件一覧ページ」を開いて案件を読み取る
 *   4. 除外キーワード・最低報酬額でふるいにかけ、報酬額が高い順に並べる
 *   5. 結果を reports/ に書き出し、上位の案件ページをタブで開いた状態でブラウザを残す
 *
 * やらないこと（意図的に実装していません）:
 *   - ログインID/パスワードの自動入力（毎回自分の目でログイン画面を確認してもらう）
 *   - 申し込みフォームへの入力・送信（最後にボタンを押すのは必ず自分）
 *   これは技術的な制約ではなく、A8.netの利用規約でのアカウント停止リスクと、
 *   クレジットカード等の実際の契約が意図せず走ってしまうリスクを避けるための設計判断です。
 *   スコープを広げたくなっても、その2点は変更しないでください。
 *
 * 初回セットアップ:
 *   npm install
 *   npx playwright install chromium
 *   cp scripts/selfback/config.example.json scripts/selfback/config.json
 *   → config.json の selfbackUrl を、実際にA8にログインして
 *     「セルフバック」ページを開いたときのURLに書き換える
 *   node scripts/selfback/run.mjs --debug
 *     → 初回はブラウザが開くのでログインし、ターミナルでEnterを押す
 *     → reports/ にそのページのHTMLと拾えた案件一覧が出力されるので、
 *       ちゃんと案件が拾えているか確認する（拾えていなければ config.json の
 *       selectors / rewardPattern を実際のページに合わせて調整する）
 */

import { chromium } from 'playwright';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import readline from 'node:readline/promises';

const DIR = dirname(fileURLToPath(import.meta.url));
const STATE_FILE = join(DIR, 'state', 'auth.json');
const REPORTS_DIR = join(DIR, 'reports');

const args = process.argv.slice(2);
const DEBUG = args.includes('--debug');
const HEADLESS = args.includes('--headless');
const configArgIndex = args.indexOf('--config');
const CONFIG_PATH = configArgIndex >= 0 && args[configArgIndex + 1]
  ? args[configArgIndex + 1]
  : join(DIR, 'config.json');

async function loadConfig() {
  if (!existsSync(CONFIG_PATH)) {
    console.error(
      `設定ファイルが見つかりません: ${CONFIG_PATH}\n` +
      `scripts/selfback/config.example.json をコピーして scripts/selfback/config.json を作り、\n` +
      `selfbackUrl（A8にログインして「セルフバック」を開いたときのURL）を設定してください。`
    );
    process.exit(1);
  }
  const raw = await readFile(CONFIG_PATH, 'utf8');
  const config = JSON.parse(raw);
  if (!config.selfbackUrl || config.selfbackUrl.includes('ここに')) {
    console.error('config.json の selfbackUrl が未設定です。実際のセルフバックページのURLを入れてください。');
    process.exit(1);
  }
  return config;
}

async function waitForEnter(message) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  await rl.question(message);
  rl.close();
}

async function ensureLoggedIn(context, page, config) {
  await page.goto(config.loginCheckUrl || 'https://www.a8.net/', { waitUntil: 'domcontentloaded' });

  const loggedIn = await isLoggedIn(page, config);
  if (loggedIn) return;

  console.log('\n未ログインのようです。開いたブラウザ画面で自分でログインしてください。');
  console.log('（IDとパスワードはこのツールには一切入力しません。2段階認証もそのまま画面で完了してください）');
  await waitForEnter('ログインが完了したら、このターミナルでEnterキーを押してください... ');

  const stillLoggedOut = !(await isLoggedIn(page, config));
  if (stillLoggedOut) {
    console.warn('ログイン状態を確認できませんでした。config.json の loggedInMarkerText を実際の画面文言に合わせて調整してください。');
    console.warn('（誤検知の可能性があるだけなので、このまま処理は続行します）');
  }

  await mkdir(dirname(STATE_FILE), { recursive: true });
  await context.storageState({ path: STATE_FILE });
  console.log('ログインセッションを保存しました。次回からは自動で再利用されます。\n');
}

async function isLoggedIn(page, config) {
  const marker = config.loggedInMarkerText || 'ログアウト';
  try {
    const count = await page.getByText(marker, { exact: false }).count();
    return count > 0;
  } catch {
    return false;
  }
}

/** 案件一覧ページから「報酬額の近くにあるリンク」をヒューリスティックに拾う。
 *  A8側のマークアップは把握できていないため、正確な抽出には
 *  config.json の rewardPattern / excludeSelectors を実データに合わせた調整が要る想定。 */
async function scrapeOffers(page, config) {
  const rewardPattern = config.rewardPattern || '([0-9][0-9,]*)\\s*円';

  return page.evaluate((rewardPatternSrc) => {
    const rewardRe = new RegExp(rewardPatternSrc);
    const anchors = Array.from(document.querySelectorAll('a[href]'));
    const seen = new Set();
    const offers = [];

    for (const a of anchors) {
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('javascript:')) continue;

      // リンク自身、もしくはリンクを含む直近のブロック要素のテキストから報酬額を探す
      const block = a.closest('li, tr, article, div') || a;
      const text = (block.innerText || '').replace(/\s+/g, ' ').trim();
      const match = text.match(rewardRe);
      if (!match) continue;

      const title = (a.innerText || a.getAttribute('title') || '').replace(/\s+/g, ' ').trim();
      if (!title) continue;

      const url = new URL(href, location.href).toString();
      const key = `${title}__${url}`;
      if (seen.has(key)) continue;
      seen.add(key);

      const reward = Number(match[1].replace(/,/g, ''));
      offers.push({ title, url, reward, contextText: text.slice(0, 200) });
    }
    return offers;
  }, rewardPattern);
}

function applyFilters(offers, config) {
  const minReward = config.minReward ?? 0;
  const excludeKeywords = config.excludeKeywords || [];
  const completedMarkers = config.completedMarkers || [];

  return offers
    .filter((o) => o.reward >= minReward)
    .filter((o) => !excludeKeywords.some((kw) => o.title.includes(kw) || o.contextText.includes(kw)))
    .filter((o) => !completedMarkers.some((kw) => o.contextText.includes(kw)))
    .sort((a, b) => b.reward - a.reward);
}

function toMarkdown(offers, config) {
  const lines = [
    `# セルフバック候補一覧（${new Date().toLocaleString('ja-JP')}）`,
    '',
    `- 除外キーワード: ${(config.excludeKeywords || []).join(', ') || 'なし'}`,
    `- 最低報酬額: ${config.minReward ?? 0}円`,
    `- 件数: ${offers.length}`,
    '',
    '| 報酬額 | 案件名 | リンク |',
    '| ---: | --- | --- |',
    ...offers.map((o) => `| ${o.reward.toLocaleString('ja-JP')}円 | ${o.title} | ${o.url} |`),
    '',
    '※ ここに出ているのは候補の一覧だけです。申し込み・登録は必ず自分でリンク先を確認してから行ってください。',
    '',
  ];
  return lines.join('\n');
}

async function main() {
  const config = await loadConfig();
  await mkdir(REPORTS_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext(
    existsSync(STATE_FILE) ? { storageState: STATE_FILE } : {}
  );
  const page = await context.newPage();

  await ensureLoggedIn(context, page, config);

  console.log(`セルフバック一覧を確認中: ${config.selfbackUrl}`);
  await page.goto(config.selfbackUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1000 + Math.random() * 1000); // サーバーに負荷をかけないよう少し待つ

  if (DEBUG) {
    const html = await page.content();
    const htmlPath = join(REPORTS_DIR, 'debug-page.html');
    await writeFile(htmlPath, html, 'utf8');
    console.log(`デバッグ用にページのHTMLを保存しました: ${htmlPath}`);
  }

  const rawOffers = await scrapeOffers(page, config);
  const offers = applyFilters(rawOffers, config);

  console.log(`拾えた案件: ${rawOffers.length}件 / 条件に合った案件: ${offers.length}件`);

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPath = join(REPORTS_DIR, `${timestamp}.md`);
  await writeFile(reportPath, toMarkdown(offers, config), 'utf8');
  console.log(`レポートを書き出しました: ${reportPath}`);

  const maxOpenTabs = config.maxOpenTabs ?? 5;
  const toOpen = offers.slice(0, maxOpenTabs);

  if (toOpen.length === 0) {
    console.log('条件に合う案件はありませんでした。');
  } else {
    console.log(`上位${toOpen.length}件をタブで開きます（申し込みボタンは自分で押してください）:`);
    for (const offer of toOpen) {
      console.log(`  - ${offer.reward.toLocaleString('ja-JP')}円  ${offer.title}`);
      const tab = await context.newPage();
      await tab.goto(offer.url, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(500 + Math.random() * 500);
    }
    await page.bringToFront();
  }

  if (HEADLESS) {
    await browser.close();
  } else {
    console.log('\n内容を確認してください。ブラウザを閉じたら、このターミナルでEnterキーを押すと終了します。');
    await waitForEnter('');
    await browser.close();
  }
}

main().catch((err) => {
  console.error('エラーが発生しました:', err);
  process.exit(1);
});
